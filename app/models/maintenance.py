from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class MaintenanceReminder(TimestampedModel):
    """Simple maintenance reminder."""

    vehicle_id: int = 0
    title: str = ""
    next_date: str = ""
    done: int = 0
    notes: Optional[str] = None
