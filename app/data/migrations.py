"""Base schema migrations for the fleet management database."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .database import execute_script, get_connection

MIGRATIONS_LOG = Path(__file__).with_name(".migrations")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER,
    notes TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    deleted_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    license_no TEXT,
    notes TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    deleted_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER,
    fine_no TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'OPEN',
    payment_date TEXT,
    attachments_json TEXT DEFAULT '[]',
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    deleted_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER,
    driver_id INTEGER,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    preview_path TEXT,
    tags TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    deleted_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS vehicle_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT,
    notes TEXT,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS maintenance_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    next_date TEXT NOT NULL,
    done INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(plate);
CREATE INDEX IF NOT EXISTS idx_drivers_last_name ON drivers(last_name);
CREATE INDEX IF NOT EXISTS idx_fines_fine_no ON fines(fine_no);
CREATE INDEX IF NOT EXISTS idx_fines_date ON fines(date);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
"""


def mark_migrated() -> None:
    """Persist the last run timestamp for bookkeeping."""
    MIGRATIONS_LOG.write_text(datetime.utcnow().isoformat(), encoding="utf-8")


def ensure_columns() -> None:
    """Add optional columns for forward compatibility."""
    with get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(fines)")
        names = {row[1] for row in cursor.fetchall()}
        if "attachments_json" not in names:
            conn.execute("ALTER TABLE fines ADD COLUMN attachments_json TEXT DEFAULT '[]'")
        if "status" not in names:
            conn.execute("ALTER TABLE fines ADD COLUMN status TEXT DEFAULT 'OPEN'")
        if "payment_date" not in names:
            conn.execute("ALTER TABLE fines ADD COLUMN payment_date TEXT")

        cursor = conn.execute("PRAGMA table_info(vehicles)")
        vnames = {row[1] for row in cursor.fetchall()}
        if "notes" not in vnames:
            conn.execute("ALTER TABLE vehicles ADD COLUMN notes TEXT")

        cursor = conn.execute("PRAGMA table_info(drivers)")
        dnames = {row[1] for row in cursor.fetchall()}
        if "notes" not in dnames:
            conn.execute("ALTER TABLE drivers ADD COLUMN notes TEXT")

        conn.commit()


def run() -> None:
    """Apply initial schema and forward-compatible alterations."""
    execute_script(SCHEMA_SQL)
    ensure_columns()
    mark_migrated()


if __name__ == "__main__":
    run()
