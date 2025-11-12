# agent_A.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class TaskRecord:
    prompt: str
    user_id: Optional[str] = None
    source: str = "web-ui"
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plan: Optional[Dict[str, Any]] = None
    export_path: Optional[str] = None
    error: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    def mark_running(self) -> None:
        self.status = "running"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self, export_path: str, plan: Dict[str, Any]) -> None:
        self.status = "completed"
        self.export_path = export_path
        self.plan = plan
        self._mark_finished()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error = error
        self._mark_finished()

    def _mark_finished(self) -> None:
        now = datetime.now(timezone.utc)
        self.updated_at = now.isoformat()
        self.finished_at = self.updated_at
        try:
            started = datetime.fromisoformat(self.created_at)
            delta = (now - started).total_seconds()
            self.duration_seconds = max(delta, 0.0)
        except ValueError:
            self.duration_seconds = None


class AgentA:

    def __init__(self, source: str = "web-ui"):
        self.source = source

    def create_task(self, prompt: str, user_id: Optional[str] = None) -> TaskRecord:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("Task prompt cannot be empty")

        record = TaskRecord(prompt=text, user_id=user_id, source=self.source)
        return record
