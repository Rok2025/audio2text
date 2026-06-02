from __future__ import annotations

import json
import re
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Any

from app.audio_convert import convert_to_wav
from app.config import AppConfig
from app.media import MediaType, detect_media_type
from app.segment_by_gap import render_segments_text, segment_funasr_result
from app.subtitle import enrich_segments, render_srt, render_vtt


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "audio"


class AudioTranscriber:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._model: Any | None = None
        self._lock = threading.Lock()

    def _load_model(self) -> Any:
        if self._model is None:
            from funasr import AutoModel

            self._model = AutoModel(
                model=str(self.config.asr.model_path),
                vad_model=str(self.config.asr.vad_model_path),
                device=self.config.asr.device,
                disable_update=True,
            )
        return self._model

    def transcribe_file(
        self,
        source: str | Path,
        threshold_ms: int | None = None,
        return_raw: bool = False,
        task_id: str | None = None,
        display_filename: str | None = None,
        media_type: MediaType | None = None,
    ) -> dict[str, Any]:
        source_path = Path(source).expanduser().resolve()
        resolved_media_type = media_type or detect_media_type(source_path)
        task_id = task_id or uuid.uuid4().hex
        name = safe_stem(source_path.name)
        wav_path = self.config.storage.wav_dir / f"{task_id}_{name}.wav"
        json_path = self.config.storage.result_dir / f"{task_id}_{name}.json"
        segments_json_path = self.config.storage.result_dir / f"{task_id}_{name}_segments.json"
        segments_txt_path = self.config.storage.result_dir / f"{task_id}_{name}_segments.txt"
        srt_path = self.config.storage.result_dir / f"{task_id}_{name}.srt"
        vtt_path = self.config.storage.result_dir / f"{task_id}_{name}.vtt"

        converted_wav = convert_to_wav(source_path, wav_path)
        with self._lock:
            model = self._load_model()
            raw_result = model.generate(input=str(converted_wav), batch_size_s=self.config.asr.batch_size_s)
        json_path.write_text(json.dumps(raw_result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        resolved_threshold = threshold_ms or self.config.asr.gap_threshold_ms
        segmented = segment_funasr_result(raw_result, resolved_threshold)
        segments_json_path.write_text(json.dumps(segmented, ensure_ascii=False, indent=2), encoding="utf-8")
        segments_text = render_segments_text(segmented)
        segments_txt_path.write_text(segments_text + ("\n" if segments_text else ""), encoding="utf-8")
        flat_segments = [segment for item in segmented for segment in item.get("segments", [])]
        enriched_segments = enrich_segments(flat_segments)
        srt_text = render_srt(enriched_segments)
        vtt_text = render_vtt(enriched_segments)
        srt_path.write_text(srt_text + ("\n" if srt_text else ""), encoding="utf-8")
        vtt_path.write_text(vtt_text + ("\n" if vtt_text else ""), encoding="utf-8")

        text = "".join(item.get("text", "").replace(" ", "") for item in raw_result)
        result = {
            "taskId": task_id,
            "status": "success",
            "source": {
                "filename": display_filename or source_path.name,
                "path": str(source_path),
                "mediaType": resolved_media_type,
                "durationMs": probe_duration_ms(source_path),
            },
            "text": text,
            "segments": enriched_segments,
            "files": {
                "wav": str(converted_wav),
                "rawJson": str(json_path),
                "segmentsJson": str(segments_json_path),
                "segmentsText": str(segments_txt_path),
                "srt": str(srt_path),
                "vtt": str(vtt_path),
            },
            "meta": {
                "model": str(self.config.asr.model_path),
                "vadModel": str(self.config.asr.vad_model_path),
                "thresholdMs": resolved_threshold,
                "device": self.config.asr.device,
            },
        }
        if return_raw:
            result["raw"] = raw_result
        return result


def probe_duration_ms(source: str | Path) -> int | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(source),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return round(float(completed.stdout.strip()) * 1000)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None
