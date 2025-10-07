"""Runtime utilities shared across UI widgets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..qt import QObject, pyqtSignal
from ..utils.runtime_paths import package_path
from ..ui.qss import theme_builder

I18N_DIR = package_path("i18n")
FEATURES_PATH = package_path("config", "features.json")
SHORTCUTS_PATH = package_path("config", "shortcuts.json")


class UIService(QObject):
    """Centralized language/theme management with Qt signals."""

    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str, str)
    text_scale_changed = pyqtSignal(float)

    def __init__(
        self,
        language: str = "tr",
        theme: str = "light",
        profile: str = "minimal",
        large_text: bool = False,
    ) -> None:
        super().__init__()
        self.language = language
        self.theme = theme
        self.profile = profile
        self.large_text = large_text
        self.text_scale = 1.2 if large_text else 1.0
        self._translations: Dict[str, Dict[str, str]] = {}
        self.features = self._safe_json_load(FEATURES_PATH, {})
        self.shortcuts = self._safe_json_load(SHORTCUTS_PATH, [])
        self.load_translations()

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_json_load(path: Path, fallback: Any) -> Any:
        """Read a JSON file returning a fallback when unavailable or invalid."""

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return fallback
        except json.JSONDecodeError:
            return fallback

    def load_translations(self) -> None:
        for file in I18N_DIR.glob("*.json"):
            self._translations[file.stem] = json.loads(file.read_text(encoding="utf-8"))

    def t(self, key: str) -> str:
        return self._translations.get(self.language, {}).get(key, key)

    def available_languages(self) -> Dict[str, str]:
        return {code: data.get("app.title", code) for code, data in self._translations.items()}

    def set_language(self, lang: str) -> None:
        if lang != self.language and lang in self._translations:
            self.language = lang
            self.language_changed.emit(lang)

    def set_theme(self, theme: str, profile: str) -> str:
        if theme != self.theme or profile != self.profile:
            self.theme = theme
            self.profile = profile
            qss = theme_builder.generate(profile, theme, self.text_scale)
            self.theme_changed.emit(theme, profile)
            return qss
        return theme_builder.generate(profile, theme, self.text_scale)

    def set_text_scale(self, large_text: bool) -> float:
        new_scale = 1.2 if large_text else 1.0
        if abs(new_scale - self.text_scale) > 1e-3:
            self.large_text = large_text
            self.text_scale = new_scale
            self.text_scale_changed.emit(new_scale)
            # Regenerate theme so font-size tokens refresh immediately
            self.theme_changed.emit(self.theme, self.profile)
        return self.text_scale

    def shortcut_descriptions(self) -> list[dict[str, str]]:
        return self.shortcuts
