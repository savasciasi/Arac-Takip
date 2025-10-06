"""SQLite connection helpers for the fleet management application."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Callable, Iterable, Sequence

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

_current_brand = ""
_db_path: Path


def _normalise_brand(brand: str) -> str:
    """Return a filesystem friendly brand identifier."""

    cleaned = "".join(ch for ch in brand.lower() if ch.isalnum())
    return cleaned or "default"


def _brand_directory(brand: str) -> Path:
    directory = STORAGE_ROOT / brand
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def set_brand_mode(brand: str) -> Path:
    """Switch database/storage roots to the provided brand."""

    global _current_brand, _db_path
    _current_brand = _normalise_brand(brand)
    brand_dir = _brand_directory(_current_brand)
    _db_path = brand_dir / "app.db"
    return _db_path


def current_brand() -> str:
    """Expose the active brand code for other modules."""

    return _current_brand


def database_path() -> Path:
    """Return the sqlite file path for the active brand."""

    return _db_path


def storage_root(brand: str | None = None) -> Path:
    """Return the storage directory for the given or active brand."""

    code = _normalise_brand(brand or _current_brand)
    return _brand_directory(code)


def storage_path(*parts: str, brand: str | None = None, ensure: bool = False) -> Path:
    """Build a path inside the active brand storage directory."""

    base = storage_root(brand)
    path = base.joinpath(*parts) if parts else base
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory enabled."""

    conn = sqlite3.connect(_db_path)
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


# Initialise using environment variable so CLI scripts can target a brand.
set_brand_mode(os.getenv("APP_BRAND", "knk"))
