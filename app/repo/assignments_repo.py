from __future__ import annotations

from typing import List

from .base import Repository
from ..models.assignment import VehicleAssignment
from ..data.database import get_connection


class AssignmentRepository(Repository):
    """Repository for vehicle-driver assignments."""

    def __init__(self) -> None:
        super().__init__("vehicle_assignments", VehicleAssignment)

    def active_for_vehicle(self, vehicle_id: int) -> VehicleAssignment | None:
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM vehicle_assignments WHERE vehicle_id = ? AND to_date IS NULL ORDER BY from_date DESC LIMIT 1",
                (vehicle_id,),
            )
            row = cur.fetchone()
            return self._row_to_model(row) if row else None

    def active_map(self) -> dict[int, VehicleAssignment]:
        """Return active assignments keyed by vehicle id for quick lookup."""

        with get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM vehicle_assignments WHERE to_date IS NULL"
            )
            rows = cur.fetchall()
        return {row["vehicle_id"]: self._row_to_model(row) for row in rows}

    def active_by_driver(self) -> dict[int, VehicleAssignment]:
        """Return active assignments keyed by driver id."""

        with get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM vehicle_assignments WHERE to_date IS NULL AND driver_id IS NOT NULL"
            )
            rows = cur.fetchall()
        return {row["driver_id"]: self._row_to_model(row) for row in rows}

    def timeline(self, vehicle_id: int) -> List[VehicleAssignment]:
        return self.search("vehicle_id = ? ORDER BY from_date DESC", (vehicle_id,))

    def close_active(self, vehicle_id: int, to_date: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE vehicle_assignments SET to_date = ? WHERE vehicle_id = ? AND to_date IS NULL",
                (to_date, vehicle_id),
            )
            conn.commit()
