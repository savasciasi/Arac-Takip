"""Repository helpers built on top of SQLite."""
from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime
from typing import Any, Iterable, List, Optional, Sequence, Type, TypeVar

from ..data.database import get_connection

T = TypeVar("T")


class Repository:
    """Generic repository for CRUD operations."""

    table: str
    model: Type[T]
    fields: Sequence[str]

    def __init__(self, table: str, model: Type[T]) -> None:
        self.table = table
        self.model = model
        self.fields = [f.name for f in fields(model) if f.init and f.name != "id"]

    def _row_to_model(self, row: Any) -> T:
        data = dict(row)
        return self.model(**data)  # type: ignore[arg-type]

    def list(self, include_deleted: bool = False) -> List[T]:
        """Return all rows optionally including soft-deleted ones."""
        query = f"SELECT * FROM {self.table}"
        params: Sequence[Any] = []
        if not include_deleted and "is_deleted" in self.fields:
            query += " WHERE is_deleted = 0"
        with get_connection() as conn:
            cur = conn.execute(query, params)
            return [self._row_to_model(row) for row in cur.fetchall()]

    def get(self, record_id: int) -> Optional[T]:
        """Fetch a row by id."""
        with get_connection() as conn:
            cur = conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (record_id,))
            row = cur.fetchone()
            return self._row_to_model(row) if row else None

    def insert(self, instance: T) -> int:
        """Insert a dataclass instance returning new id."""
        data = asdict(instance)
        data.pop("id", None)
        columns = ",".join(data.keys())
        placeholders = ":" + ",:".join(data.keys())
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        with get_connection() as conn:
            cur = conn.execute(sql, data)
            conn.commit()
            return int(cur.lastrowid)

    def update(self, record_id: int, data: dict[str, Any]) -> None:
        """Update columns for a row."""
        data["updated_at"] = datetime.utcnow().isoformat()
        assignments = ",".join([f"{key} = :{key}" for key in data])
        data["id"] = record_id
        sql = f"UPDATE {self.table} SET {assignments} WHERE id = :id"
        with get_connection() as conn:
            conn.execute(sql, data)
            conn.commit()

    def soft_delete(self, record_id: int, user: str | None = None) -> None:
        """Soft delete a record by setting is_deleted flag."""
        now = datetime.utcnow().isoformat()
        payload = {
            "is_deleted": 1,
            "deleted_at": now,
            "deleted_by": user,
            "updated_at": now,
            "id": record_id,
        }
        with get_connection() as conn:
            conn.execute(
                f"UPDATE {self.table} SET is_deleted=:is_deleted, deleted_at=:deleted_at, "
                "deleted_by=:deleted_by, updated_at=:updated_at WHERE id = :id",
                payload,
            )
            conn.commit()

    def restore(self, record_id: int) -> None:
        """Restore a soft-deleted record."""
        with get_connection() as conn:
            conn.execute(
                f"UPDATE {self.table} SET is_deleted = 0, deleted_at = NULL, deleted_by = NULL WHERE id = ?",
                (record_id,),
            )
            conn.commit()

    def delete(self, record_id: int) -> None:
        """Hard delete a record."""
        with get_connection() as conn:
            conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (record_id,))
            conn.commit()

    def search(self, where: str, params: Sequence[Any]) -> List[T]:
        """Basic search helper."""
        with get_connection() as conn:
            cur = conn.execute(f"SELECT * FROM {self.table} WHERE {where}", params)
            return [self._row_to_model(row) for row in cur.fetchall()]
