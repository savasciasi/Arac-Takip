"""Runtime utilities shared across UI widgets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal

from ..ui.qss import theme_builder

BASE_DIR = Path(__file__).resolve().parents[1]
I18N_DIR = BASE_DIR / "i18n"
FEATURES_PATH = BASE_DIR / "config" / "features.json"
SHORTCUTS_PATH = BASE_DIR / "config" / "shortcuts.json"


class UIService(QObject):
    """Centralized language/theme management with Qt signals."""

    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str, str)

    def __init__(self, language: str = "tr", theme: str = "light", profile: str = "minimal") -> None:
        super().__init__()
        self.language = language
        self.theme = theme
        self.profile = profile
        self._translations: Dict[str, Dict[str, str]] = {}
        self.features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
        self.shortcuts = json.loads(SHORTCUTS_PATH.read_text(encoding="utf-8"))
        self.load_translations()

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
            qss = theme_builder.generate(profile)
            self.theme_changed.emit(theme, profile)
            return qss
        return theme_builder.generate(profile)

    def shortcut_descriptions(self) -> list[dict[str, str]]:
        return self.shortcuts
