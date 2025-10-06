from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import TimestampedModel


@dataclass(slots=True)
class VehicleAssignment(TimestampedModel):
    """Represents a vehicle-driver assignment."""

    vehicle_id: int = 0
    driver_id: int = 0
    from_date: str = ""
    to_date: Optional[str] = None
    notes: Optional[str] = None
