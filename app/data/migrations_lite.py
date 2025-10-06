"""Lite-feature migrations such as seed settings and helper indexes."""
from __future__ import annotations

from .database import get_connection


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
                "INSERT INTO app_settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        conn.commit()


def ensure_indexes() -> None:
    """Create indexes used by the lite features."""
    with get_connection() as conn:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_assignments_vehicle ON vehicle_assignments(vehicle_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_maintenance_next_date ON maintenance_reminders(next_date)"
        )
        conn.commit()


def run() -> None:
    """Apply lite feature migrations."""
    seed_settings()
    ensure_indexes()


if __name__ == "__main__":
    run()
