"""Lite-feature migrations such as seed settings and helper indexes."""
from __future__ import annotations

from .database import current_database, get_connection


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
                "INSERT INTO app_settings(`key`, value) VALUES(%s, %s) "
                "ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (key, value),
            )
        conn.commit()


def ensure_indexes() -> None:
    """Create indexes used by the lite features."""
    with get_connection() as conn:
        indexes = [
            (
                "vehicle_assignments",
                "idx_assignments_vehicle",
                "CREATE INDEX idx_assignments_vehicle ON vehicle_assignments(vehicle_id)",
            ),
            (
                "maintenance_reminders",
                "idx_maintenance_next_date",
                "CREATE INDEX idx_maintenance_next_date ON maintenance_reminders(next_date)",
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
