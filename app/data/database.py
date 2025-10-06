"""SQLite connection helpers for the fleet management application."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable, Iterable, Sequence

DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_script(sql: str) -> None:
    """Execute a SQL script in a managed connection."""
    with get_connection() as conn:
        conn.executescript(sql)


def iter_rows(query: str, params: Sequence | None = None) -> Iterable[sqlite3.Row]:
    """Yield rows for a query lazily."""
    with get_connection() as conn:
        cursor = conn.execute(query, params or [])
        for row in cursor:
            yield row


def transact(func: Callable[[sqlite3.Connection], None]) -> None:
    """Execute callback inside a transaction with auto-commit/rollback."""
    with get_connection() as conn:
        try:
            func(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
