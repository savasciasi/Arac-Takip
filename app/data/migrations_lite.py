"""Lite feature migrations that run alongside the core schema setup."""
from __future__ import annotations

import json
import logging
from datetime import datetime

from .database import current_brand, current_database, get_connection, table_name
from ..utils.runtime_paths import state_file

logger = logging.getLogger(__name__)

LITE_STATE = state_file("schema_state.json")
LITE_VERSION = 2


DEFAULT_SETTINGS = {
    "default_language": "tr",
    "default_theme": "light",
    "theme_profile": "minimal",
    "large_text": "0",
    "high_fine_amount": "250",
    "upcoming_days": "14",
    "date_format": "DD.MM.YYYY",
}


def _load_state() -> dict[str, dict[str, object]]:
    try:
        return json.loads(LITE_STATE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict[str, dict[str, object]]) -> None:
    LITE_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _state_key() -> str:
    return current_brand() or "default"


def _mark_lite_migrated() -> None:
    state = _load_state()
    key = _state_key()
    entry = state.setdefault(key, {})
    entry["lite_version"] = LITE_VERSION
    entry["lite_updated_at"] = datetime.utcnow().isoformat()
    _save_state(state)


def seed_settings() -> None:
    """Ensure required application settings exist without recreating connections."""

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
                "SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s",
                (current_database(), table, name),
            ).fetchone()
            if not exists:
                conn.execute(ddl)
        conn.commit()


def run() -> None:
    """Apply lite feature migrations only when the schema version changes."""

    state = _load_state()
    key = _state_key()
    entry = state.get(key, {})
    if entry.get("lite_version") == LITE_VERSION:
        logger.info(
            "Skipping lite migrations for brand '%s'; version %s is up to date.",
            key,
            LITE_VERSION,
        )
        return

    logger.info(
        "Applying lite migrations for brand '%s' to reach version %s",
        key,
        LITE_VERSION,
    )
    seed_settings()
    ensure_indexes()
    _mark_lite_migrated()


if __name__ == "__main__":
    run()
