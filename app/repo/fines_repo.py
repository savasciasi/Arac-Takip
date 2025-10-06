from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from .base import Repository
from ..models.fine import Fine
from ..data.database import get_connection


class FineRepository(Repository):
    """Repository for fines with aggregations."""

    def __init__(self) -> None:
        super().__init__("fines", Fine)

    def search_text(self, text: str) -> List[Fine]:
        like = f"%{text.lower()}%"
        return self.search(
            "(LOWER(fine_no) LIKE ? OR LOWER(description) LIKE ?) AND is_deleted = 0",
            (like, like),
        )

    def summary(self) -> Dict[str, float]:
        """Return summary totals for dashboard cards."""
        with get_connection() as conn:
            totals = {
                "total": conn.execute("SELECT COALESCE(SUM(amount),0) FROM fines WHERE is_deleted = 0").fetchone()[0],
                "open": conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM fines WHERE status = 'OPEN' AND is_deleted = 0"
                ).fetchone()[0],
                "month": conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM fines WHERE strftime('%Y-%m', date) = ? AND is_deleted = 0",
                    (datetime.utcnow().strftime("%Y-%m"),),
                ).fetchone()[0],
                "year": conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM fines WHERE strftime('%Y', date) = ? AND is_deleted = 0",
                    (datetime.utcnow().strftime("%Y"),),
                ).fetchone()[0],
            }
        return totals

    def filter(self, status: str | None = None, vehicle_id: int | None = None, driver_id: int | None = None) -> List[Fine]:
        """Filter fines by status, vehicle, or driver."""
        clauses = ["is_deleted = 0"]
        params: List[object] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if vehicle_id:
            clauses.append("vehicle_id = ?")
            params.append(vehicle_id)
        if driver_id:
            clauses.append("driver_id = ?")
            params.append(driver_id)
        where = " AND ".join(clauses)
        return self.search(where, params)

    def attachments(self, fine_id: int) -> List[str]:
        """Return attachments for a fine."""
        fine = self.get(fine_id)
        if not fine:
            return []
        import json

        return json.loads(fine.attachments_json or "[]")
