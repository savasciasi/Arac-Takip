"""Settings page allowing to tweak application preferences."""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...services.backup_service import BackupService, BACKUP_DIR
from ...services.settings_service import SettingsService
from ...services.ui_service import UIService
from .base_page import BasePage


class SettingsPage(BasePage):
    """User settings including language, theme, and backup actions."""

    def __init__(self, ui: UIService, settings: SettingsService, parent=None) -> None:
        super().__init__(ui, parent)
        self.settings = settings
        self.backup = BackupService()
        layout = QVBoxLayout(self)
        self.header = QLabel(ui.t("settings.title"))
        layout.addWidget(self.header)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.language_combo = QComboBox()
        self.theme_combo = QComboBox()
        self.profile_combo = QComboBox()
        self.upcoming_spin = QSpinBox()
        self.upcoming_spin.setRange(1, 60)
        self.high_fine_spin = QSpinBox()
        self.high_fine_spin.setRange(0, 10000)
        self.large_text = QCheckBox()
        self._selected_language = settings.get("default_language", "tr")
        self._selected_theme = settings.get("default_theme", "light")
        self._selected_profile = settings.get("theme_profile", "minimal")
        self._selected_large_text = settings.get("large_text", "false").lower() == "true"
        self._populate_option_lists()
        self.upcoming_spin.setValue(int(settings.get("upcoming_days", "14")))
        self.high_fine_spin.setValue(int(settings.get("high_fine_amount", "250")))
        self.large_text.setChecked(self._selected_large_text)
        form.addRow(self.ui_service.t("settings.language"), self.language_combo)
        form.addRow(self.ui_service.t("settings.default_theme"), self.theme_combo)
        form.addRow(self.ui_service.t("settings.profile"), self.profile_combo)
        form.addRow(self.ui_service.t("settings.upcoming_days"), self.upcoming_spin)
        form.addRow(self.ui_service.t("settings.high_fine_amount"), self.high_fine_spin)
        form.addRow(self.ui_service.t("settings.large_text"), self.large_text)
        layout.addWidget(form_widget)
        self.save_btn = QPushButton(self.ui_service.t("settings.save"))
        layout.addWidget(self.save_btn)
        self.backup_btn = QPushButton(self.ui_service.t("backup.create"))
        self.restore_btn = QPushButton(self.ui_service.t("backup.restore"))
        layout.addWidget(self.backup_btn)
        layout.addWidget(self.restore_btn)
        self.save_btn.clicked.connect(self.save_settings)
        self.backup_btn.clicked.connect(self.create_backup)
        self.restore_btn.clicked.connect(self.restore_backup)

    def save_settings(self) -> None:
        data = {
            "default_language": self.language_combo.currentData(),
            "default_theme": self.theme_combo.currentData(),
            "theme_profile": self.profile_combo.currentData(),
            "upcoming_days": str(self.upcoming_spin.value()),
            "high_fine_amount": str(self.high_fine_spin.value()),
            "large_text": str(self.large_text.isChecked()),
        }
        self.settings.update(data)
        self.ui_service.set_language(data["default_language"])
        self.ui_service.set_theme(data["default_theme"], data["theme_profile"])
        self.ui_service.set_text_scale(self.large_text.isChecked())
        self._selected_language = data["default_language"]
        self._selected_theme = data["default_theme"]
        self._selected_profile = data["theme_profile"]
        self._selected_large_text = self.large_text.isChecked()

    def create_backup(self) -> None:
        self.backup.create_backup()

    def restore_backup(self) -> None:
        # In real scenario prompt for file path; using latest backup for demo
        backups = sorted(BACKUP_DIR.glob("backup_*.zip"), reverse=True)
        if backups:
            self.backup.restore_backup(backups[0])

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("settings.title"))
        self.save_btn.setText(self.ui_service.t("settings.save"))
        self.backup_btn.setText(self.ui_service.t("backup.create"))
        self.restore_btn.setText(self.ui_service.t("backup.restore"))
        self._populate_option_lists()

    def _populate_option_lists(self) -> None:
        language_value = getattr(self, "_selected_language", self.settings.get("default_language", "tr"))
        theme_value = getattr(self, "_selected_theme", self.settings.get("default_theme", "light"))
        profile_value = getattr(self, "_selected_profile", self.settings.get("theme_profile", "minimal"))

        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        languages = self.ui_service.available_languages()
        for code, title in languages.items():
            self.language_combo.addItem(title, code)
        lang_index = self.language_combo.findData(language_value)
        self.language_combo.setCurrentIndex(lang_index if lang_index >= 0 else 0)
        self.language_combo.blockSignals(False)

        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(self.ui_service.t("ui.theme.light"), "light")
        self.theme_combo.addItem(self.ui_service.t("ui.theme.dark"), "dark")
        theme_index = self.theme_combo.findData(theme_value)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.theme_combo.blockSignals(False)

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem(self.ui_service.t("ui.theme.minimal"), "minimal")
        self.profile_combo.addItem(self.ui_service.t("ui.theme.glass"), "glass")
        self.profile_combo.addItem(self.ui_service.t("ui.theme.contrast"), "contrast")
        profile_index = self.profile_combo.findData(profile_value)
        self.profile_combo.setCurrentIndex(profile_index if profile_index >= 0 else 0)
        self.profile_combo.blockSignals(False)
