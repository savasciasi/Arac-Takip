from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class Fine(TimestampedModel):
    """Traffic fine model."""

    vehicle_id: int = 0
    driver_id: Optional[int] = None
    fine_no: str = ""
    date: str = ""
    amount: float = 0.0
    description: str = ""
    status: str = "OPEN"
    payment_date: Optional[str] = None
    attachments_json: str = "[]"
    is_deleted: int = 0
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
