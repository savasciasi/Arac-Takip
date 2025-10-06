"""Service helpers around maintenance reminders."""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from ..models.maintenance import MaintenanceReminder
from ..repo.maintenance_repo import MaintenanceRepository


class MaintenanceLiteService:
    """Fetch upcoming reminders and trigger toast notifications."""

    def __init__(self) -> None:
        self.repo = MaintenanceRepository()

    def upcoming(self, days: int) -> List[MaintenanceReminder]:
        until = (date.today() + timedelta(days=days)).isoformat()
        return self.repo.upcoming(until)

    def due_today(self) -> List[MaintenanceReminder]:
        return self.repo.due_today()

    def complete(self, reminder_id: int) -> None:
        self.repo.mark_done(reminder_id)
