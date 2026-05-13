from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from app.audio_convert import convert_to_wav
from app.config import AppConfig
from app.segment_by_gap import render_segments_text, segment_funasr_result


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "audio"


class AudioTranscriber:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._model: Any | None = None

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

    def transcribe_file(self, source: str | Path, threshold_ms: int | None = None) -> dict[str, Any]:
        source_path = Path(source).expanduser().resolve()
        task_id = uuid.uuid4().hex
        name = safe_stem(source_path.name)
        wav_path = self.config.storage.wav_dir / f"{task_id}_{name}.wav"
        json_path = self.config.storage.result_dir / f"{task_id}_{name}.json"
        segments_json_path = self.config.storage.result_dir / f"{task_id}_{name}_segments.json"
        segments_txt_path = self.config.storage.result_dir / f"{task_id}_{name}_segments.txt"

        converted_wav = convert_to_wav(source_path, wav_path)
        model = self._load_model()
        raw_result = model.generate(input=str(converted_wav), batch_size_s=self.config.asr.batch_size_s)
        json_path.write_text(json.dumps(raw_result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        resolved_threshold = threshold_ms or self.config.asr.gap_threshold_ms
        segmented = segment_funasr_result(raw_result, resolved_threshold)
        segments_json_path.write_text(json.dumps(segmented, ensure_ascii=False, indent=2), encoding="utf-8")
        segments_text = render_segments_text(segmented)
        segments_txt_path.write_text(segments_text + ("\n" if segments_text else ""), encoding="utf-8")

        text = "".join(item.get("text", "").replace(" ", "") for item in raw_result)
        return {
            "taskId": task_id,
            "status": "success",
            "text": text,
            "segments": [segment for item in segmented for segment in item.get("segments", [])],
            "files": {
                "wav": str(converted_wav),
                "rawJson": str(json_path),
                "segmentsJson": str(segments_json_path),
                "segmentsText": str(segments_txt_path),
            },
            "model": str(self.config.asr.model_path),
            "vadModel": str(self.config.asr.vad_model_path),
            "thresholdMs": resolved_threshold,
        }
