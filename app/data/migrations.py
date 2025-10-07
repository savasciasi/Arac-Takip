"""Base schema migrations for the fleet management database (MySQL)."""
from __future__ import annotations

from datetime import datetime
from .database import current_database, execute_script, get_connection, table_name, table_prefix
from ..utils.runtime_paths import state_file

MIGRATIONS_LOG = state_file("migrations.log")


def _schema_sql() -> str:
    """Build schema DDL using the active brand's table names."""

    tables = {name: table_name(name) for name in (
        "vehicles",
        "drivers",
        "fines",
        "documents",
        "vehicle_assignments",
        "maintenance_reminders",
        "app_settings",
    )}
    raw_prefix = table_prefix()
    prefix = raw_prefix[:-1].upper() if raw_prefix.endswith("_") else raw_prefix.upper()
    fk_prefix = f"{prefix}_" if prefix else ""

    return f"""
CREATE TABLE IF NOT EXISTS {tables['vehicles']} (
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

CREATE TABLE IF NOT EXISTS {tables['drivers']} (
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

CREATE TABLE IF NOT EXISTS {tables['fines']} (
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
    CONSTRAINT fk_{fk_prefix}fines_vehicle FOREIGN KEY(vehicle_id) REFERENCES {tables['vehicles']}(id),
    CONSTRAINT fk_{fk_prefix}fines_driver FOREIGN KEY(driver_id) REFERENCES {tables['drivers']}(id)
);

CREATE TABLE IF NOT EXISTS {tables['documents']} (
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
    CONSTRAINT fk_{fk_prefix}documents_vehicle FOREIGN KEY(vehicle_id) REFERENCES {tables['vehicles']}(id),
    CONSTRAINT fk_{fk_prefix}documents_driver FOREIGN KEY(driver_id) REFERENCES {tables['drivers']}(id)
);

CREATE TABLE IF NOT EXISTS {tables['vehicle_assignments']} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    driver_id INT NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NULL,
    notes TEXT,
    CONSTRAINT fk_{fk_prefix}assignments_vehicle FOREIGN KEY(vehicle_id) REFERENCES {tables['vehicles']}(id),
    CONSTRAINT fk_{fk_prefix}assignments_driver FOREIGN KEY(driver_id) REFERENCES {tables['drivers']}(id)
);

CREATE TABLE IF NOT EXISTS {tables['maintenance_reminders']} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    title VARCHAR(128) NOT NULL,
    next_date DATE NOT NULL,
    done TINYINT(1) DEFAULT 0,
    notes TEXT,
    CONSTRAINT fk_{fk_prefix}maintenance_vehicle FOREIGN KEY(vehicle_id) REFERENCES {tables['vehicles']}(id)
);

CREATE TABLE IF NOT EXISTS {tables['app_settings']} (
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

    fines_table = table_name("fines")
    vehicles_table = table_name("vehicles")
    drivers_table = table_name("drivers")
    with get_connection() as conn:
        if not _column_exists(fines_table, "attachments_json"):
            conn.execute(f"ALTER TABLE {fines_table} ADD COLUMN attachments_json TEXT DEFAULT '[]'")
        if not _column_exists(fines_table, "status"):
            conn.execute(f"ALTER TABLE {fines_table} ADD COLUMN status VARCHAR(16) DEFAULT 'OPEN'")
        if not _column_exists(fines_table, "payment_date"):
            conn.execute(f"ALTER TABLE {fines_table} ADD COLUMN payment_date DATE NULL")
        if not _column_exists(vehicles_table, "notes"):
            conn.execute(f"ALTER TABLE {vehicles_table} ADD COLUMN notes TEXT")
        if not _column_exists(drivers_table, "notes"):
            conn.execute(f"ALTER TABLE {drivers_table} ADD COLUMN notes TEXT")
        conn.commit()


def ensure_indexes() -> None:
    """Create indexes used by common queries."""

    tables = {name: table_name(name) for name in ("vehicles", "drivers", "fines", "documents")}
    indexes = [
        (
            tables["vehicles"],
            "idx_vehicles_plate",
            f"CREATE INDEX idx_vehicles_plate ON {tables['vehicles']}(plate)",
        ),
        (
            tables["drivers"],
            "idx_drivers_last_name",
            f"CREATE INDEX idx_drivers_last_name ON {tables['drivers']}(last_name)",
        ),
        (
            tables["fines"],
            "idx_fines_fine_no",
            f"CREATE INDEX idx_fines_fine_no ON {tables['fines']}(fine_no)",
        ),
        (
            tables["fines"],
            "idx_fines_date",
            f"CREATE INDEX idx_fines_date ON {tables['fines']}(date)",
        ),
        (
            tables["documents"],
            "idx_documents_title",
            f"CREATE INDEX idx_documents_title ON {tables['documents']}(title)",
        ),
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

    execute_script(_schema_sql())
    ensure_columns()
    ensure_indexes()
    mark_migrated()


if __name__ == "__main__":
    run()
