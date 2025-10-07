from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class Document(TimestampedModel):
    """Document model that can be attached to vehicles or drivers."""

    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    title: str = ""
    path: str = ""
    preview_path: Optional[str] = None
    tags: str = ""
    is_deleted: int = 0
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
