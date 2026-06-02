from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def elapsed_ms(started_at: str, finished_at: str) -> int | None:
    try:
        start = datetime.fromisoformat(started_at)
        finish = datetime.fromisoformat(finished_at)
    except ValueError:
        return None
    return round((finish - start).total_seconds() * 1000)


class RecordStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "records.jsonl"
        self._lock = threading.Lock()

    def append(self, record: dict[str, Any]) -> None:
        payload = dict(record)
        payload.setdefault("recordedAt", now_iso())
        line = json.dumps(payload, ensure_ascii=False, default=str)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        limit = max(1, min(limit, 500))
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return list(reversed(records[-limit:]))

    def find_by_task_id(self, task_id: str) -> list[dict[str, Any]]:
        if not task_id or any(char in task_id for char in "/\\"):
            raise ValueError("Invalid task id")
        return [record for record in self.list(limit=500) if record.get("taskId") == task_id]


def build_record(
    *,
    task_id: str,
    mode: str,
    status: str,
    started_at: str,
    finished_at: str | None = None,
    filename: str | None = None,
    media_type: str | None = None,
    file_size_bytes: int | None = None,
    threshold_ms: int | None = None,
    output_format: str | None = None,
    return_raw: bool | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    completed_at = finished_at or now_iso()
    segments = result.get("segments", []) if result else []
    text = result.get("text", "") if result else ""
    source = result.get("source", {}) if result else {}
    return {
        "taskId": task_id,
        "mode": mode,
        "status": status,
        "filename": filename or source.get("filename"),
        "mediaType": media_type or source.get("mediaType"),
        "fileSizeBytes": file_size_bytes,
        "durationMs": source.get("durationMs"),
        "thresholdMs": threshold_ms,
        "format": output_format,
        "returnRaw": return_raw,
        "textLength": len(text),
        "segmentCount": len(segments),
        "files": result.get("files") if result else None,
        "error": error,
        "startedAt": started_at,
        "finishedAt": completed_at,
        "elapsedMs": elapsed_ms(started_at, completed_at),
    }
