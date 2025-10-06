from __future__ import annotations

from datetime import date
from typing import List

from .base import Repository
from ..models.maintenance import MaintenanceReminder
from ..data.database import get_connection


class MaintenanceRepository(Repository):
    """Repository for maintenance reminders."""

    def __init__(self) -> None:
        super().__init__("maintenance_reminders", MaintenanceReminder)

    def upcoming(self, until_date: str) -> List[MaintenanceReminder]:
        return self.search("done = 0 AND next_date <= ?", (until_date,))

    def due_today(self) -> List[MaintenanceReminder]:
        today = date.today().isoformat()
        return self.search("done = 0 AND next_date = ?", (today,))

    def mark_done(self, reminder_id: int) -> None:
        with get_connection() as conn:
            conn.execute("UPDATE maintenance_reminders SET done = 1 WHERE id = ?", (reminder_id,))
            conn.commit()
