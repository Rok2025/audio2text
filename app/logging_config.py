from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
            "message": record.getMessage(),
        }
        details = getattr(record, "details", None)
        if isinstance(details, dict):
            payload.update(details)
        if record.exc_info:
            payload["exception"] = super().formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("audio2text")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = log_dir / "app.log"
    existing_paths = {
        getattr(handler, "baseFilename", None)
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler)
    }
    if str(log_path) not in existing_paths:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(JsonLineFormatter())
        logger.addHandler(handler)
    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    details: dict[str, Any] | None = None,
    level: int = logging.INFO,
) -> None:
    logger.log(level, event, extra={"event": event, "details": details or {}})
