"""Simple log viewer for troubleshooting packaged builds."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ...qt import (
    QComboBox,
    QDesktopServices,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpacerItem,
    QUrl,
    QVBoxLayout,
)
from ...services.ui_service import UIService
from ...utils.logging_utils import current_log_file, logs_directory
from .base_page import BasePage


class LogsPage(BasePage):
    """Display generated log files and allow opening the folder."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.header.setProperty("role", "page-title")
        self.subtitle = QLabel()
        self.subtitle.setProperty("role", "muted")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.header)
        layout.addWidget(self.subtitle)

        controls = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.file_combo.currentIndexChanged.connect(self._load_selected_file)
        controls.addWidget(self.file_combo)
        self.refresh_button = QPushButton()
        self.refresh_button.setProperty("variant", "secondary")
        self.refresh_button.clicked.connect(self.refresh_files)
        controls.addWidget(self.refresh_button)
        self.open_button = QPushButton()
        self.open_button.setProperty("variant", "ghost")
        self.open_button.clicked.connect(self.open_folder)
        controls.addWidget(self.open_button)
        controls.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(controls)

        self.path_label = QLabel()
        self.path_label.setProperty("role", "muted")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        self.updated_label = QLabel()
        self.updated_label.setProperty("role", "muted")
        layout.addWidget(self.updated_label)

        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self.viewer, 1)
        layout.addStretch(1)

        self.retranslate(ui.language)

    def refresh_files(self) -> None:
        """Populate the combo box with available log files."""

        directory = logs_directory()
        directory.mkdir(parents=True, exist_ok=True)
        active = current_log_file()
        files = sorted(directory.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        selected_index = 0
        for idx, path in enumerate(files):
            timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            self.file_combo.addItem(f"{path.name} · {timestamp}", str(path))
            if path == active:
                selected_index = idx
        if not files:
            self.file_combo.addItem(self.ui_service.t("logs.noFiles"), "")
            self.file_combo.setEnabled(False)
            self.viewer.setPlainText(self.ui_service.t("logs.empty"))
            self.path_label.setText(self.ui_service.t("logs.noFiles"))
            self.updated_label.clear()
        else:
            self.file_combo.setEnabled(True)
            self.file_combo.setCurrentIndex(selected_index)
            self._load_selected_file(selected_index)
        self.file_combo.blockSignals(False)

    def open_folder(self) -> None:
        """Open the directory containing log files in the system file manager."""

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_directory())))

    def _load_selected_file(self, index: int) -> None:
        """Display the content of the currently selected log file."""

        if not self.file_combo.count():
            return
        path_text = self.file_combo.itemData(index)
        if not path_text:
            return
        path = Path(path_text)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if not content:
            content = self.ui_service.t("logs.empty")
        self.viewer.setPlainText(content)
        self.path_label.setText(
            self.ui_service.t("logs.pathLabel").format(path=str(path))
        )
        try:
            timestamp = datetime.fromtimestamp(path.stat().st_mtime)
            formatted = timestamp.strftime("%Y-%m-%d %H:%M")
        except OSError:
            formatted = ""
        if formatted:
            self.updated_label.setText(
                self.ui_service.t("logs.updated").format(timestamp=formatted)
            )
        else:
            self.updated_label.clear()

    def retranslate(self, _: str) -> None:
        """Update UI text when the application language changes."""

        self.header.setText(self.ui_service.t("logs.title"))
        self.subtitle.setText(self.ui_service.t("logs.subtitle"))
        self.refresh_button.setText(self.ui_service.t("logs.refresh"))
        self.open_button.setText(self.ui_service.t("logs.openFolder"))
        self.viewer.setPlaceholderText(self.ui_service.t("logs.empty"))
        self.refresh_files()
