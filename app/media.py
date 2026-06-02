from __future__ import annotations

from pathlib import Path
from typing import Literal


MediaType = Literal["audio", "video"]

AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
VIDEO_SUFFIXES = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
ALLOWED_SUFFIXES = AUDIO_SUFFIXES | VIDEO_SUFFIXES

AUDIO_UPLOAD_LIMIT_BYTES = 200 * 1024 * 1024
VIDEO_UPLOAD_LIMIT_BYTES = 1024 * 1024 * 1024


def suffix_for(filename: str | Path) -> str:
    return Path(filename).suffix.lower()


def detect_media_type(filename: str | Path) -> MediaType:
    suffix = suffix_for(filename)
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    raise ValueError(f"Unsupported media suffix: {suffix or '(none)'}")


def upload_limit_bytes(media_type: MediaType) -> int:
    if media_type == "video":
        return VIDEO_UPLOAD_LIMIT_BYTES
    return AUDIO_UPLOAD_LIMIT_BYTES
