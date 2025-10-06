from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class Vehicle(TimestampedModel):
    """Vehicle domain model."""

    plate: str = ""
    brand: str = ""
    model: str = ""
    year: Optional[int] = None
    notes: str = ""
    is_deleted: int = 0
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
    active_driver: Optional[str] = None
