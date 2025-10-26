"""Service that coordinates configuration persistence and live settings."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict

from ..models.app_settings import AppSetting
from ..repo.settings_repo import SettingsRepository
from ..utils.runtime_paths import runtime_root

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("ARACTAKIP_DATA_DIR", str(runtime_root())))
CONFIG_DIR = DATA_ROOT / "storage"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, str] = {
    "default_language": "tr",
    "default_theme": "light",
    "theme_profile": "minimal",
    "large_text": "false",
    "high_fine_amount": "250",
    "upcoming_days": "14",
    "date_format": "DD.MM.YYYY",
    "active_brand": "knk",
}


class SettingsService:
    """Manage reading/writing settings from config files and database."""

    def __init__(self) -> None:
        self.repo = SettingsRepository()
        self._cache: Dict[str, str] = {}
        self.load()

    # ------------------------------------------------------------------
    def _read_file_config(self) -> Dict[str, str]:
        """Read the JSON config guarding against empty or invalid files."""

        dirty = False
        content: Dict[str, str] = {}
        try:
            raw = CONFIG_PATH.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            dirty = True
        except OSError as exc:  # pragma: no cover - IO failure
            logger.warning("Config dosyası okunamadı: %s", exc)
            dirty = True
        else:
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Config JSON bozuk, varsayılanlarla devam ediliyor")
                    dirty = True
                else:
                    content = {k: str(v) for k, v in parsed.items()}
            else:
                dirty = True

        merged = {**DEFAULT_CONFIG, **content}
        if dirty or any(key not in content for key in DEFAULT_CONFIG):
            try:
                CONFIG_PATH.write_text(
                    json.dumps(merged, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except OSError as exc:  # pragma: no cover - IO failure
                logger.warning("Config dosyası yazılamadı: %s", exc)
        return merged

    def load(self) -> Dict[str, str]:
        """Load settings merging file defaults and DB values."""

        file_defaults = self._read_file_config()
        db_settings: Dict[str, str] = {}
        try:
            db_settings = self.repo.as_dict()
        except Exception as exc:  # pragma: no cover - DB unavailable at bootstrap
            logger.debug("DB ayarları okunamadı: %s", exc)
        merged = {**file_defaults, **db_settings}
        self._cache = {k: str(v) for k, v in merged.items()}
        return self._cache

    def get(self, key: str, fallback: str | None = None) -> str:
        default = fallback if fallback is not None else DEFAULT_CONFIG.get(key, "")
        return self._cache.get(key, str(default))

    def update(self, data: Dict[str, str]) -> None:
        """Persist settings both in config file and DB."""

        new_values = {**self._cache, **{k: str(v) for k, v in data.items()}}
        try:
            CONFIG_PATH.write_text(
                json.dumps(new_values, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover - IO failure
            logger.warning("Config dosyası güncellenemedi: %s", exc)
        for key, value in data.items():
            try:
                self.repo.upsert(AppSetting(key=key, value=str(value)))
            except Exception as exc:  # pragma: no cover - DB unavailable at bootstrap
                logger.debug("Ayar DB'ye yazılamadı (%s): %s", key, exc)
        self._cache.update({k: str(v) for k, v in data.items()})

    # ------------------------------------------------------------------
    def get_active_brand(self, fallback: str = "knk") -> str:
        """Return the stored active brand with a sensible fallback."""

        return self.get("active_brand", fallback)

    def set_active_brand(self, brand: str) -> None:
        """Persist the current active brand across sessions."""

        self.update({"active_brand": brand})
