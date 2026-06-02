from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import load_config
from app.job_store import JobStore
from app.logging_config import configure_logging, log_event
from app.media import (
    ALLOWED_SUFFIXES,
    AUDIO_SUFFIXES,
    VIDEO_SUFFIXES,
    MediaType,
    detect_media_type,
    suffix_for,
    upload_limit_bytes,
)
from app.records import RecordStore, build_record, now_iso
from app.transcriber import AudioTranscriber, safe_stem


CONFIG = load_config(Path(__file__).resolve().parents[1] / "config.yaml")
TRANSCRIBER = AudioTranscriber(CONFIG)
JOBS = JobStore(CONFIG.storage.job_dir)
RECORDS = RecordStore(CONFIG.storage.record_dir)
LOGGER = configure_logging(CONFIG.storage.log_dir)

app = FastAPI(title="audio2text", version="0.1.0")


@app.get("/")
def index() -> dict[str, object]:
    return {
        "name": "audio2text",
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "models": "/api/models",
            "records": "/api/records?limit=50",
            "transcribe": "POST /api/transcribe?thresholdMs=600",
            "jobs": "POST /api/jobs",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, object]:
    checks = {
        "modelPath": CONFIG.asr.model_path.exists(),
        "vadModelPath": CONFIG.asr.vad_model_path.exists(),
        "inputDir": CONFIG.storage.input_dir.exists(),
        "wavDir": CONFIG.storage.wav_dir.exists(),
        "resultDir": CONFIG.storage.result_dir.exists(),
        "jobDir": CONFIG.storage.job_dir.exists(),
        "logDir": CONFIG.storage.log_dir.exists(),
        "recordDir": CONFIG.storage.record_dir.exists(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
    }
    return {"status": "ok" if all(checks.values()) else "not_ready", "checks": checks}


@app.get("/api/models")
def models() -> dict[str, object]:
    return {
        "asr": {
            "model": str(CONFIG.asr.model_path),
            "vadModel": str(CONFIG.asr.vad_model_path),
            "device": CONFIG.asr.device,
            "batchSizeS": CONFIG.asr.batch_size_s,
            "gapThresholdMs": CONFIG.asr.gap_threshold_ms,
        },
        "formats": ["json", "text", "srt", "vtt"],
        "allowedAudioSuffixes": sorted(AUDIO_SUFFIXES),
        "allowedVideoSuffixes": sorted(VIDEO_SUFFIXES),
        "allowedSuffixes": sorted(ALLOWED_SUFFIXES),
    }


@app.post("/api/transcribe")
def transcribe(
    file: Annotated[UploadFile, File()],
    threshold_ms: Annotated[int | None, Query(alias="thresholdMs", ge=100, le=5000)] = None,
    output_format: Annotated[Literal["json", "text", "srt", "vtt"], Query(alias="format")] = "json",
    return_raw: Annotated[bool, Query(alias="returnRaw")] = False,
) -> Any:
    started_at = now_iso()
    filename = file.filename or "audio"
    media_type: MediaType | None = None
    file_size_bytes: int | None = None
    log_event(
        LOGGER,
        "transcribe.start",
        {
            "mode": "sync",
            "filename": filename,
            "thresholdMs": threshold_ms,
            "format": output_format,
            "returnRaw": return_raw,
        },
    )
    try:
        input_path, media_type, file_size_bytes = save_upload(file)
        result = TRANSCRIBER.transcribe_file(
            input_path,
            threshold_ms=threshold_ms,
            return_raw=return_raw,
            display_filename=file.filename,
            media_type=media_type,
        )
        RECORDS.append(
            build_record(
                task_id=result["taskId"],
                mode="sync",
                status="success",
                started_at=started_at,
                filename=filename,
                media_type=media_type,
                file_size_bytes=file_size_bytes,
                threshold_ms=result.get("meta", {}).get("thresholdMs"),
                output_format=output_format,
                return_raw=return_raw,
                result=result,
            )
        )
        log_event(
            LOGGER,
            "transcribe.success",
            {
                "mode": "sync",
                "taskId": result["taskId"],
                "filename": filename,
                "mediaType": media_type,
                "segmentCount": len(result.get("segments", [])),
                "textLength": len(result.get("text", "")),
            },
        )
        return format_result_response(result, output_format)
    except HTTPException as exc:
        detail = str(exc.detail)
        RECORDS.append(
            build_record(
                task_id="sync-" + uuid.uuid4().hex,
                mode="sync",
                status="failed",
                started_at=started_at,
                filename=filename,
                media_type=media_type,
                file_size_bytes=file_size_bytes,
                threshold_ms=threshold_ms,
                output_format=output_format,
                return_raw=return_raw,
                error=detail,
            )
        )
        log_event(
            LOGGER,
            "transcribe.failed",
            {
                "mode": "sync",
                "filename": filename,
                "mediaType": media_type,
                "error": detail,
            },
            level=logging.ERROR,
        )
        raise
    except Exception as exc:
        RECORDS.append(
            build_record(
                task_id="sync-" + uuid.uuid4().hex,
                mode="sync",
                status="failed",
                started_at=started_at,
                filename=filename,
                media_type=media_type,
                file_size_bytes=file_size_bytes,
                threshold_ms=threshold_ms,
                output_format=output_format,
                return_raw=return_raw,
                error=str(exc),
            )
        )
        log_event(
            LOGGER,
            "transcribe.failed",
            {
                "mode": "sync",
                "filename": filename,
                "mediaType": media_type,
                "error": str(exc),
            },
            level=logging.ERROR,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/jobs")
def create_job(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    threshold_ms: Annotated[int | None, Query(alias="thresholdMs", ge=100, le=5000)] = None,
    return_raw: Annotated[bool, Query(alias="returnRaw")] = False,
) -> dict[str, Any]:
    started_at = now_iso()
    task_id = uuid.uuid4().hex
    filename = file.filename or "audio"
    try:
        input_path, media_type, file_size_bytes = save_upload(file)
    except HTTPException as exc:
        detail = str(exc.detail)
        RECORDS.append(
            build_record(
                task_id=task_id,
                mode="async",
                status="failed",
                started_at=started_at,
                filename=filename,
                threshold_ms=threshold_ms,
                return_raw=return_raw,
                error=detail,
            )
        )
        log_event(
            LOGGER,
            "job.failed",
            {
                "taskId": task_id,
                "filename": filename,
                "error": detail,
            },
            level=logging.ERROR,
        )
        raise
    job = JOBS.create(
        task_id,
        {
            "source": {
                "filename": filename,
                "path": str(input_path),
                "mediaType": media_type,
                "fileSizeBytes": file_size_bytes,
            },
            "request": {
                "thresholdMs": threshold_ms,
                "returnRaw": return_raw,
                "startedAt": started_at,
            },
        },
    )
    RECORDS.append(
        build_record(
            task_id=task_id,
            mode="async",
            status="queued",
            started_at=started_at,
            filename=filename,
            media_type=media_type,
            file_size_bytes=file_size_bytes,
            threshold_ms=threshold_ms,
            return_raw=return_raw,
        )
    )
    log_event(
        LOGGER,
        "job.queued",
        {
            "taskId": task_id,
            "filename": filename,
            "mediaType": media_type,
            "fileSizeBytes": file_size_bytes,
            "thresholdMs": threshold_ms,
            "returnRaw": return_raw,
        },
    )
    background_tasks.add_task(run_job, task_id, input_path, threshold_ms, return_raw)
    return {
        "taskId": task_id,
        "status": job["status"],
        "statusUrl": f"/api/jobs/{task_id}",
        "resultUrl": f"/api/jobs/{task_id}/result",
    }


@app.get("/api/jobs/{task_id}")
def get_job(task_id: str) -> dict[str, Any]:
    job = read_job_or_404(task_id)
    result = job.get("result") or {}
    return {
        "taskId": job["taskId"],
        "status": job["status"],
        "createdAt": job.get("createdAt"),
        "updatedAt": job.get("updatedAt"),
        "source": job.get("source"),
        "request": job.get("request"),
        "error": job.get("error"),
        "resultUrl": f"/api/jobs/{task_id}/result" if result else None,
        "files": result.get("files"),
    }


@app.get("/api/records")
def list_records(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> dict[str, Any]:
    records = RECORDS.list(limit=limit)
    return {"records": records, "limit": limit, "count": len(records)}


@app.get("/api/records/{task_id}")
def get_record(task_id: str) -> dict[str, Any]:
    try:
        records = RECORDS.find_by_task_id(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not records:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"taskId": task_id, "records": records, "count": len(records)}


@app.get("/api/jobs/{task_id}/result")
def get_job_result(
    task_id: str,
    output_format: Annotated[Literal["json", "text", "srt", "vtt"], Query(alias="format")] = "json",
) -> Any:
    job = read_job_or_404(task_id)
    if job.get("status") != "success":
        raise HTTPException(status_code=409, detail=f"Job is not complete: {job.get('status')}")
    return format_result_response(job["result"], output_format)


@app.get("/api/jobs/{task_id}/files/{file_type}")
def get_job_file(task_id: str, file_type: str) -> FileResponse:
    job = read_job_or_404(task_id)
    if job.get("status") != "success":
        raise HTTPException(status_code=409, detail=f"Job is not complete: {job.get('status')}")
    files = job.get("result", {}).get("files", {})
    aliases = {
        "raw-json": "rawJson",
        "segments-json": "segmentsJson",
        "txt": "segmentsText",
        "text": "segmentsText",
        "srt": "srt",
        "vtt": "vtt",
        "wav": "wav",
    }
    key = aliases.get(file_type)
    if key is None or key not in files:
        raise HTTPException(status_code=404, detail=f"File type not found: {file_type}")
    path = Path(files[key]).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_type}")
    return FileResponse(path)


@app.delete("/api/jobs/{task_id}")
def delete_job(task_id: str) -> dict[str, object]:
    deleted = JOBS.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"taskId": task_id, "deleted": True}


def save_upload(file: UploadFile) -> tuple[Path, MediaType, int]:
    suffix = suffix_for(file.filename or "audio")
    try:
        media_type = detect_media_type(file.filename or "audio")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    input_path = CONFIG.storage.input_dir / f"{uuid.uuid4().hex}_{safe_stem(file.filename or 'audio')}{suffix}"
    max_upload_bytes = upload_limit_bytes(media_type)
    size = 0
    with input_path.open("wb") as handle:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_upload_bytes:
                handle.close()
                input_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Uploaded file is too large")
            handle.write(chunk)
    return input_path, media_type, size


def run_job(task_id: str, input_path: Path, threshold_ms: int | None, return_raw: bool) -> None:
    try:
        job = JOBS.read(task_id) or {}
        source = job.get("source") or {}
        request = job.get("request") or {}
        display_filename = source.get("filename")
        media_type = source.get("mediaType")
        file_size_bytes = source.get("fileSizeBytes")
        started_at = request.get("startedAt") or now_iso()
        JOBS.update(task_id, status="processing", progress={"stage": "transcribing"})
        log_event(
            LOGGER,
            "job.processing",
            {
                "taskId": task_id,
                "filename": display_filename,
                "mediaType": media_type,
                "thresholdMs": threshold_ms,
            },
        )
        result = TRANSCRIBER.transcribe_file(
            input_path,
            threshold_ms=threshold_ms,
            return_raw=return_raw,
            task_id=task_id,
            display_filename=display_filename,
            media_type=media_type,
        )
        JOBS.update(task_id, status="success", progress={"stage": "complete"}, result=result)
        RECORDS.append(
            build_record(
                task_id=task_id,
                mode="async",
                status="success",
                started_at=started_at,
                filename=display_filename,
                media_type=media_type,
                file_size_bytes=file_size_bytes,
                threshold_ms=result.get("meta", {}).get("thresholdMs"),
                return_raw=return_raw,
                result=result,
            )
        )
        log_event(
            LOGGER,
            "job.success",
            {
                "taskId": task_id,
                "filename": display_filename,
                "mediaType": media_type,
                "segmentCount": len(result.get("segments", [])),
                "textLength": len(result.get("text", "")),
            },
        )
    except Exception as exc:
        JOBS.update(task_id, status="failed", progress={"stage": "failed"}, error=str(exc))
        job = JOBS.read(task_id) or {}
        source = job.get("source") or {}
        request = job.get("request") or {}
        RECORDS.append(
            build_record(
                task_id=task_id,
                mode="async",
                status="failed",
                started_at=request.get("startedAt") or now_iso(),
                filename=source.get("filename"),
                media_type=source.get("mediaType"),
                file_size_bytes=source.get("fileSizeBytes"),
                threshold_ms=threshold_ms,
                return_raw=return_raw,
                error=str(exc),
            )
        )
        log_event(
            LOGGER,
            "job.failed",
            {
                "taskId": task_id,
                "filename": source.get("filename"),
                "mediaType": source.get("mediaType"),
                "error": str(exc),
            },
            level=logging.ERROR,
        )


def read_job_or_404(task_id: str) -> dict[str, Any]:
    try:
        job = JOBS.read(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def format_result_response(
    result: dict[str, Any],
    output_format: Literal["json", "text", "srt", "vtt"],
) -> Any:
    if output_format == "json":
        return result
    if output_format == "text":
        return PlainTextResponse(result["text"])
    path = Path(result["files"][output_format])
    media_type = "application/x-subrip" if output_format == "srt" else "text/vtt"
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type=media_type)
