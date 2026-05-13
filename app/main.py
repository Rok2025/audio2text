from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from app.config import load_config
from app.transcriber import AudioTranscriber, safe_stem


CONFIG = load_config(Path(__file__).resolve().parents[1] / "config.yaml")
TRANSCRIBER = AudioTranscriber(CONFIG)

app = FastAPI(title="audio2text", version="0.1.0")


@app.get("/")
def index() -> dict[str, object]:
    return {
        "name": "audio2text",
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "transcribe": "POST /api/transcribe?thresholdMs=600",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcribe")
def transcribe(
    file: Annotated[UploadFile, File()],
    threshold_ms: Annotated[int | None, Query(alias="thresholdMs", ge=100, le=5000)] = None,
) -> dict:
    suffix = Path(file.filename or "audio").suffix
    input_path = CONFIG.storage.input_dir / f"{uuid.uuid4().hex}_{safe_stem(file.filename or 'audio')}{suffix}"
    try:
        with input_path.open("wb") as handle:
            shutil.copyfileobj(file.file, handle)
        return TRANSCRIBER.transcribe_file(input_path, threshold_ms=threshold_ms)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
