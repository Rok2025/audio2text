from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but was not found in PATH")


def convert_to_wav(source: str | Path, target: str | Path) -> Path:
    ensure_ffmpeg()
    source_path = Path(source).expanduser().resolve()
    target_path = Path(target).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Audio file not found: {source_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(target_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return target_path
