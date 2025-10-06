"""Application entry point for Fleet & Fine Management."""
from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .services.settings_service import SettingsService
from .services.ui_service import UIService
from .ui.components.command_palette import CommandPalette
from .ui.components.toast import ToastManager
from .ui.qss import theme_builder
from .ui.pages.assignments import AssignmentsPage
from .ui.pages.dashboard import DashboardPage
from .ui.pages.documents import DocumentsPage
from .ui.pages.drivers import DriversPage
from .ui.pages.fines import FinesPage
from .ui.pages.maintenance_lite import MaintenanceLitePage
from .ui.pages.recycle_bin import RecycleBinPage
from .ui.pages.reports import ReportsPage
from .ui.pages.settings import SettingsPage
from .ui.pages.vehicles import VehiclesPage


class MainWindow(QMainWindow):
    """Main application window with navigation and stacked pages."""

    def __init__(self, ui_service: UIService, settings_service: SettingsService) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.ui_service = ui_service
        self.setWindowTitle(self.ui_service.t("app.title"))
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        layout.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.toast_manager = ToastManager(self)
        self.command_palette = CommandPalette(self)
        self._pages: dict[str, QWidget] = {}
        self._register_pages()
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self._bind_shortcuts()

    def _register_pages(self) -> None:
        pages = [
            ("dashboard", DashboardPage(self.ui_service)),
            ("vehicles", VehiclesPage(self.ui_service)),
            ("drivers", DriversPage(self.ui_service)),
            ("fines", FinesPage(self.ui_service)),
            ("documents", DocumentsPage(self.ui_service)),
            ("reports", ReportsPage(self.ui_service)),
            ("settings", SettingsPage(self.ui_service, self.settings_service)),
            ("recycle", RecycleBinPage(self.ui_service)),
            ("assignments", AssignmentsPage(self.ui_service)),
            ("maintenance", MaintenanceLitePage(self.ui_service)),
        ]
        for key, page in pages:
            self._pages[key] = page
            self.stack.addWidget(page)
            item = QListWidgetItem(self.ui_service.t(f"ui.nav.{key}"))
            self.sidebar.addItem(item)
        self.ui_service.language_changed.connect(self._update_navigation)

    def _update_navigation(self, lang: str) -> None:
        self.setWindowTitle(self.ui_service.t("app.title"))
        for i, key in enumerate(self._pages.keys()):
            self.sidebar.item(i).setText(self.ui_service.t(f"ui.nav.{key}"))

    def _bind_shortcuts(self) -> None:
        self.command_palette.set_actions(
            [
                (self.ui_service.t("ui.nav.dashboard"), "", lambda: self._navigate("dashboard")),
                (self.ui_service.t("ui.nav.vehicles"), "", lambda: self._navigate("vehicles")),
                (self.ui_service.t("ui.nav.drivers"), "", lambda: self._navigate("drivers")),
                (self.ui_service.t("ui.nav.fines"), "", lambda: self._navigate("fines")),
                (self.ui_service.t("ui.nav.documents"), "", lambda: self._navigate("documents")),
                (self.ui_service.t("ui.nav.reports"), "", lambda: self._navigate("reports")),
                (self.ui_service.t("ui.nav.settings"), "", lambda: self._navigate("settings")),
            ]
        )

    def _navigate(self, key: str) -> None:
        index = list(self._pages.keys()).index(key)
        self.sidebar.setCurrentRow(index)


def main() -> None:
    app = QApplication(sys.argv)
    settings = SettingsService()
    ui_service = UIService(
        language=settings.get("default_language", "tr"),
        theme=settings.get("default_theme", "light"),
        profile=settings.get("theme_profile", "minimal"),
    )
    app.setStyleSheet(theme_builder.generate(ui_service.profile))
    window = MainWindow(ui_service, settings)
    window.resize(1280, 720)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
