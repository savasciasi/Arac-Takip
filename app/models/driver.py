from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class Driver(TimestampedModel):
    """Driver domain model."""

    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    license_no: str = ""
    notes: str = ""
    is_deleted: int = 0
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
