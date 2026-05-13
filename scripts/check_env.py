#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_config


def main() -> None:
    config = load_config(PROJECT_ROOT / "config.yaml")
    checks = {
        "python": sys.executable,
        "ffmpeg": shutil.which("ffmpeg") or "NOT FOUND",
        "asr_model": str(config.asr.model_path),
        "asr_model_exists": str(config.asr.model_path.exists()),
        "vad_model": str(config.asr.vad_model_path),
        "vad_model_exists": str(config.asr.vad_model_path.exists()),
        "storage_result": str(config.storage.result_dir),
    }
    for key, value in checks.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
