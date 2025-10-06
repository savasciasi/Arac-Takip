"""Base schema migrations for the fleet management database (MySQL)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .database import current_database, execute_script, get_connection

MIGRATIONS_LOG = Path(__file__).with_name(".migrations")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate VARCHAR(32) NOT NULL UNIQUE,
    brand VARCHAR(64) NOT NULL,
    model VARCHAR(64) NOT NULL,
    year INT,
    notes TEXT,
    is_deleted TINYINT(1) DEFAULT 0,
    deleted_at DATETIME NULL,
    deleted_by VARCHAR(128) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    phone VARCHAR(32),
    license_no VARCHAR(64),
    notes TEXT,
    is_deleted TINYINT(1) DEFAULT 0,
    deleted_at DATETIME NULL,
    deleted_by VARCHAR(128) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    driver_id INT NULL,
    fine_no VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    status VARCHAR(16) DEFAULT 'OPEN',
    payment_date DATE NULL,
    attachments_json TEXT DEFAULT '[]',
    is_deleted TINYINT(1) DEFAULT 0,
    deleted_at DATETIME NULL,
    deleted_by VARCHAR(128) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_fines_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    CONSTRAINT fk_fines_driver FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NULL,
    driver_id INT NULL,
    title VARCHAR(128) NOT NULL,
    path VARCHAR(255) NOT NULL,
    preview_path VARCHAR(255) NULL,
    tags VARCHAR(255),
    is_deleted TINYINT(1) DEFAULT 0,
    deleted_at DATETIME NULL,
    deleted_by VARCHAR(128) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_documents_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    CONSTRAINT fk_documents_driver FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS vehicle_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    driver_id INT NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NULL,
    notes TEXT,
    CONSTRAINT fk_assignments_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    CONSTRAINT fk_assignments_driver FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

CREATE TABLE IF NOT EXISTS maintenance_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    title VARCHAR(128) NOT NULL,
    next_date DATE NOT NULL,
    done TINYINT(1) DEFAULT 0,
    notes TEXT,
    CONSTRAINT fk_maintenance_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS app_settings (
    `key` VARCHAR(64) PRIMARY KEY,
    value TEXT NOT NULL
);

"""


def mark_migrated() -> None:
    """Persist the last run timestamp for bookkeeping."""

    MIGRATIONS_LOG.write_text(datetime.utcnow().isoformat(), encoding="utf-8")


def _column_exists(table: str, column: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (current_database(), table, column),
        )
        return cursor.fetchone() is not None


def ensure_columns() -> None:
    """Add optional columns for forward compatibility."""

    with get_connection() as conn:
        if not _column_exists("fines", "attachments_json"):
            conn.execute("ALTER TABLE fines ADD COLUMN attachments_json TEXT DEFAULT '[]'")
        if not _column_exists("fines", "status"):
            conn.execute("ALTER TABLE fines ADD COLUMN status VARCHAR(16) DEFAULT 'OPEN'")
        if not _column_exists("fines", "payment_date"):
            conn.execute("ALTER TABLE fines ADD COLUMN payment_date DATE NULL")
        if not _column_exists("vehicles", "notes"):
            conn.execute("ALTER TABLE vehicles ADD COLUMN notes TEXT")
        if not _column_exists("drivers", "notes"):
            conn.execute("ALTER TABLE drivers ADD COLUMN notes TEXT")
        conn.commit()


def ensure_indexes() -> None:
    """Create indexes used by common queries."""

    indexes = [
        ("vehicles", "idx_vehicles_plate", "CREATE INDEX idx_vehicles_plate ON vehicles(plate)"),
        ("drivers", "idx_drivers_last_name", "CREATE INDEX idx_drivers_last_name ON drivers(last_name)"),
        ("fines", "idx_fines_fine_no", "CREATE INDEX idx_fines_fine_no ON fines(fine_no)"),
        ("fines", "idx_fines_date", "CREATE INDEX idx_fines_date ON fines(date)"),
        ("documents", "idx_documents_title", "CREATE INDEX idx_documents_title ON documents(title)"),
    ]
    with get_connection() as conn:
        for table, name, ddl in indexes:
            exists = conn.execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s",
                (current_database(), table, name),
            ).fetchone()
            if not exists:
                conn.execute(ddl)
        conn.commit()


def run() -> None:
    """Apply initial schema and forward-compatible alterations."""

    execute_script(SCHEMA_SQL)
    ensure_columns()
    ensure_indexes()
    mark_migrated()


if __name__ == "__main__":
    run()
