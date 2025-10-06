from __future__ import annotations

from typing import List

from .base import Repository
from ..models.vehicle import Vehicle


class VehicleRepository(Repository):
    """Vehicle repository with helper queries."""

    def __init__(self) -> None:
        super().__init__("vehicles", Vehicle)

    def search_by_plate(self, text: str) -> List[Vehicle]:
        like = f"%{text.lower()}%"
        return self.search("LOWER(plate) LIKE ? AND is_deleted = 0", (like,))
