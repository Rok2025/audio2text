from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AsrConfig:
    model_path: Path
    vad_model_path: Path
    device: str = "cpu"
    batch_size_s: int = 60
    gap_threshold_ms: int = 600


@dataclass(frozen=True)
class StorageConfig:
    input_dir: Path
    wav_dir: Path
    result_dir: Path
    job_dir: Path
    log_dir: Path
    record_dir: Path


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    asr: AsrConfig
    storage: StorageConfig


def _resolve_path(root_dir: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root_dir / path
    return path.resolve()


def _read_mapping(config_path: Path) -> dict[str, Any]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {config_path}")
    return data


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    resolved_config = Path(config_path).expanduser().resolve()
    root_dir = resolved_config.parent
    data = _read_mapping(resolved_config)
    asr = data.get("asr") or {}
    storage = data.get("storage") or {}

    app_config = AppConfig(
        root_dir=root_dir,
        asr=AsrConfig(
            model_path=_resolve_path(root_dir, asr.get("model_path", "./models/paraformer-zh")),
            vad_model_path=_resolve_path(root_dir, asr.get("vad_model_path", "./models/fsmn-vad")),
            device=str(asr.get("device", "cpu")),
            batch_size_s=int(asr.get("batch_size_s", 60)),
            gap_threshold_ms=int(asr.get("gap_threshold_ms", 600)),
        ),
        storage=StorageConfig(
            input_dir=_resolve_path(root_dir, storage.get("input_dir", "./storage/input")),
            wav_dir=_resolve_path(root_dir, storage.get("wav_dir", "./storage/wav")),
            result_dir=_resolve_path(root_dir, storage.get("result_dir", "./storage/result")),
            job_dir=_resolve_path(root_dir, storage.get("job_dir", "./storage/jobs")),
            log_dir=_resolve_path(root_dir, storage.get("log_dir", "./storage/logs")),
            record_dir=_resolve_path(root_dir, storage.get("record_dir", "./storage/records")),
        ),
    )

    app_config.storage.input_dir.mkdir(parents=True, exist_ok=True)
    app_config.storage.wav_dir.mkdir(parents=True, exist_ok=True)
    app_config.storage.result_dir.mkdir(parents=True, exist_ok=True)
    app_config.storage.job_dir.mkdir(parents=True, exist_ok=True)
    app_config.storage.log_dir.mkdir(parents=True, exist_ok=True)
    app_config.storage.record_dir.mkdir(parents=True, exist_ok=True)
    return app_config
