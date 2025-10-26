"""Lite-feature migrations such as seed settings and helper indexes."""
from __future__ import annotations

from .database import current_database, get_connection, table_name


DEFAULT_SETTINGS = {
    "default_language": "tr",
    "default_theme": "light",
    "theme_profile": "minimal",
    "large_text": "0",
    "high_fine_amount": "250",
    "upcoming_days": "14",
    "date_format": "DD.MM.YYYY"
}


def seed_settings() -> None:
    """Ensure required application settings exist."""
    with get_connection() as conn:
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                f"INSERT INTO {table_name('app_settings')}(`key`, value) VALUES(%s, %s) "
                "ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (key, value),
            )
        conn.commit()


def ensure_indexes() -> None:
    """Create indexes used by the lite features."""
    with get_connection() as conn:
        assignments_table = table_name("vehicle_assignments")
        maintenance_table = table_name("maintenance_reminders")
        indexes = [
            (
                assignments_table,
                "idx_assignments_vehicle",
                f"CREATE INDEX idx_assignments_vehicle ON {assignments_table}(vehicle_id)",
            ),
            (
                maintenance_table,
                "idx_maintenance_next_date",
                f"CREATE INDEX idx_maintenance_next_date ON {maintenance_table}(next_date)",
            ),
        ]
        for table, name, ddl in indexes:
            exists = conn.execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s",
                (current_database(), table, name),
            ).fetchone()
            if not exists:
                conn.execute(ddl)
        conn.commit()


def run() -> None:
    """Apply lite feature migrations."""
    seed_settings()
    ensure_indexes()


if __name__ == "__main__":
    run()
