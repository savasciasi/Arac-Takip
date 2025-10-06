"""Dataclass-style models representing records."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class TimestampedModel:
    """Common timestamped fields."""

    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def touch(self) -> None:
        """Update timestamps."""
        now = datetime.utcnow().isoformat()
        self.updated_at = now
        if not self.created_at:
            self.created_at = now
