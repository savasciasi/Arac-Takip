"""Service that handles vehicle-driver assignments with auto-closing logic."""
from __future__ import annotations

from datetime import date

from ..repo.assignments_repo import AssignmentRepository


class AssignmentService:
    """Create assignments ensuring only one active driver per vehicle."""

    def __init__(self) -> None:
        self.repo = AssignmentRepository()

    def assign(self, vehicle_id: int, driver_id: int, notes: str | None = None) -> None:
        today = date.today().isoformat()
        active = self.repo.active_for_vehicle(vehicle_id)
        if active:
            self.repo.close_active(vehicle_id, today)
        self.repo.insert(
            self.repo.model(vehicle_id=vehicle_id, driver_id=driver_id, from_date=today, to_date=None, notes=notes)
        )
