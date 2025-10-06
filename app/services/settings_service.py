"""Service that coordinates configuration persistence and live settings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from ..models.app_settings import AppSetting
from ..repo.settings_repo import SettingsRepository

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.json"


class SettingsService:
    """Manage reading/writing settings from config files and database."""

    def __init__(self) -> None:
        self.repo = SettingsRepository()
        self._cache: Dict[str, str] = {}
        self.load()

    def load(self) -> Dict[str, str]:
        """Load settings merging file defaults and DB values."""
        file_defaults = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        db_settings = self.repo.as_dict()
        merged = {**file_defaults, **db_settings}
        self._cache = {k: str(v) for k, v in merged.items()}
        return self._cache

    def get(self, key: str, fallback: str | None = None) -> str:
        return self._cache.get(key, fallback or "")

    def update(self, data: Dict[str, str]) -> None:
        """Persist settings both in config file and DB."""
        new_values = {**self._cache, **data}
        CONFIG_PATH.write_text(json.dumps(new_values, indent=2), encoding="utf-8")
        for key, value in data.items():
            self.repo.upsert(AppSetting(key=key, value=str(value)))
        self._cache.update({k: str(v) for k, v in data.items()})
