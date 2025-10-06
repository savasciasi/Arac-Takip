"""Repository helpers built on top of MySQL while mimicking sqlite API."""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Any, Iterable, List, Optional, Sequence, Type, TypeVar

from ..data.database import current_database, get_connection, table_name

T = TypeVar("T")


class Repository:
    """Generic repository for CRUD operations."""

    table: str
    model: Type[T]
    fields: Sequence[str]

    def __init__(self, table: str, model: Type[T]) -> None:
        self.base_table = table
        self.table = table_name(table)
        self.model = model
        self.columns = self._load_columns()
        model_fields = [f.name for f in fields(model) if f.init and f.name != "id"]
        if self.columns:
            self.fields = [name for name in model_fields if name in self.columns]
        else:
            self.fields = model_fields

    def _load_columns(self) -> set[str]:
        """Read column names from MySQL so transient fields are ignored."""

        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                    (current_database(), self.table),
                )
                return {row["COLUMN_NAME"] for row in cursor.fetchall()}
        except Exception:
            return set()

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
        now = datetime.utcnow().isoformat()
        payload: dict[str, Any] = {}
        for field in self.fields:
            value = getattr(instance, field, None)
            if field in {"created_at", "updated_at"} and not value:
                value = now
            payload[field] = value
        if not payload:
            raise ValueError(f"No insertable fields resolved for table '{self.table}'")
        columns = ",".join(payload.keys())
        placeholders = ",".join([f":{name}" for name in payload])
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        with get_connection() as conn:
            cur = conn.execute(sql, payload)
            conn.commit()
            return int(cur.lastrowid)

    def update(self, record_id: int, data: dict[str, Any]) -> None:
        """Update columns for a row."""
        filtered = {key: value for key, value in data.items() if not self.columns or key in self.columns}
        if self.columns and "updated_at" in self.columns:
            filtered["updated_at"] = datetime.utcnow().isoformat()
        elif "updated_at" in self.fields:
            filtered["updated_at"] = datetime.utcnow().isoformat()
        filtered["id"] = record_id
        assignments = ",".join([f"{key} = :{key}" for key in filtered if key != "id"])
        if not assignments:
            return
        sql = f"UPDATE {self.table} SET {assignments} WHERE id = :id"
        with get_connection() as conn:
            conn.execute(sql, filtered)
            conn.commit()

    def soft_delete(self, record_id: int, user: str | None = None) -> None:
        """Soft delete a record by setting is_deleted flag."""
        now = datetime.utcnow().isoformat()
        payload: dict[str, Any] = {"id": record_id}
        assignments: list[str] = []
        if not self.columns or "is_deleted" in self.columns:
            payload["is_deleted"] = 1
            assignments.append("is_deleted = :is_deleted")
        if not self.columns or "deleted_at" in self.columns:
            payload["deleted_at"] = now
            assignments.append("deleted_at = :deleted_at")
        if not self.columns or "deleted_by" in self.columns:
            payload["deleted_by"] = user
            assignments.append("deleted_by = :deleted_by")
        if not self.columns or "updated_at" in self.columns:
            payload["updated_at"] = now
            assignments.append("updated_at = :updated_at")
        if not assignments:
            # Nothing to update; fall back to hard delete semantics.
            self.delete(record_id)
            return
        with get_connection() as conn:
            conn.execute(
                f"UPDATE {self.table} SET {', '.join(assignments)} WHERE id = :id",
                payload,
            )
            conn.commit()

    def restore(self, record_id: int) -> None:
        """Restore a soft-deleted record."""
        assignments: list[str] = []
        payload: dict[str, Any] = {"id": record_id}
        if not self.columns or "is_deleted" in self.columns:
            assignments.append("is_deleted = 0")
        if not self.columns or "deleted_at" in self.columns:
            assignments.append("deleted_at = NULL")
        if not self.columns or "deleted_by" in self.columns:
            assignments.append("deleted_by = NULL")
        if not assignments:
            return
        with get_connection() as conn:
            conn.execute(f"UPDATE {self.table} SET {', '.join(assignments)} WHERE id = :id", payload)
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
