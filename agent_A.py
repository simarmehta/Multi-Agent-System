# agent_A.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class TaskRecord:
    """Canonical structure shared between Agent A, Agent B, and the API/UI."""

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

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # dataclasses replace None with None automatically; keep structure predictable for the API
        return data

    def mark_running(self) -> None:
        self.status = "running"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self, export_path: str, plan: Dict[str, Any]) -> None:
        self.status = "completed"
        self.export_path = export_path
        self.plan = plan
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error = error
        self.updated_at = datetime.now(timezone.utc).isoformat()


class AgentA:
    """Minimal dispatcher that converts free-form UI requests into task records."""

    def __init__(self, source: str = "web-ui"):
        self.source = source

    def create_task(self, prompt: str, user_id: Optional[str] = None) -> TaskRecord:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("Task prompt cannot be empty.")

        record = TaskRecord(prompt=text, user_id=user_id, source=self.source)
        return record
