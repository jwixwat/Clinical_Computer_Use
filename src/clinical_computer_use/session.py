"""
Session models and lifecycle metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .config import SCREENSHOT_DIR, TRACE_DIR


@dataclass
class SessionContext:
    task_name: str
    user_prompt: str
    session_id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def trace_dir(self) -> Path:
        path = TRACE_DIR / self.session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def screenshot_dir(self) -> Path:
        path = SCREENSHOT_DIR / self.session_id
        path.mkdir(parents=True, exist_ok=True)
        return path
