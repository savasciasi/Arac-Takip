from __future__ import annotations

from typing import Dict

from ..data.database import get_connection
from ..models.app_settings import AppSetting


class SettingsRepository:
    """Repository for app settings key/value pairs."""

    table = "app_settings"

    def as_dict(self) -> Dict[str, str]:
        with get_connection() as conn:
            cur = conn.execute("SELECT `key`, value FROM app_settings")
            return {row[0]: row[1] for row in cur.fetchall()}

    def upsert(self, setting: AppSetting) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO app_settings(`key`, value) VALUES(%s, %s) "
                "ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (setting.key, setting.value),
            )
            conn.commit()
