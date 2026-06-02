from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class JobStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, task_id: str) -> Path:
        if not task_id or any(char in task_id for char in "/\\"):
            raise ValueError("Invalid task id")
        return self.root / f"{task_id}.json"

    def create(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        record = {
            "taskId": task_id,
            "status": "queued",
            "createdAt": now_iso(),
            "updatedAt": now_iso(),
            **data,
        }
        self.write(task_id, record)
        return record

    def read(self, task_id: str) -> dict[str, Any] | None:
        path = self.path_for(task_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, task_id: str, data: dict[str, Any]) -> None:
        path = self.path_for(task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        record = self.read(task_id)
        if record is None:
            raise FileNotFoundError(f"Job not found: {task_id}")
        record.update(changes)
        record["updatedAt"] = now_iso()
        self.write(task_id, record)
        return record

    def delete(self, task_id: str) -> bool:
        path = self.path_for(task_id)
        if not path.exists():
            return False
        path.unlink()
        return True
