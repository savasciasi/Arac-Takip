"""Application entry point for Fleet & Fine Management."""
from __future__ import annotations

import sys

from pathlib import Path

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
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


ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"


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
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 32, 20, 32)
        self.sidebar_layout.setSpacing(16)
        self.brand_label = QLabel(self.ui_service.t("app.title"))
        self.brand_label.setProperty("role", "card-title")
        self.sidebar_layout.addWidget(self.brand_label)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        layout.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.toast_manager = ToastManager(self)
        self.command_palette = CommandPalette(self)
        self._pages: dict[str, QWidget] = {}
        self._register_pages()
        self._bind_shortcuts()
        first_key = next(iter(self._pages))
        self._navigate(first_key)

    def _register_pages(self) -> None:
        pages = [
            ("dashboard", DashboardPage(self.ui_service), "dashboard", "primary"),
            ("vehicles", VehiclesPage(self.ui_service), "vehicles", "primary"),
            ("drivers", DriversPage(self.ui_service), "drivers", "primary"),
            ("fines", FinesPage(self.ui_service), "fines", "primary"),
            ("documents", DocumentsPage(self.ui_service), "documents", "primary"),
            ("reports", ReportsPage(self.ui_service), "reports", "primary"),
            ("assignments", AssignmentsPage(self.ui_service), "assignments", "primary"),
            ("maintenance", MaintenanceLitePage(self.ui_service), "maintenance", "primary"),
            ("recycle", RecycleBinPage(self.ui_service), "recycle", "secondary"),
            ("settings", SettingsPage(self.ui_service, self.settings_service), "settings", "secondary"),
        ]
        bottom: list[QPushButton] = []
        for key, page, icon, section in pages:
            self._pages[key] = page
            self.stack.addWidget(page)
            button = self._create_nav_button(key, icon)
            if section == "secondary":
                bottom.append(button)
            else:
                self.sidebar_layout.addWidget(button)
            self.nav_group.addButton(button)
            self.nav_buttons[key] = button
        self.sidebar_layout.addStretch(1)
        for button in bottom:
            self.sidebar_layout.addWidget(button)
        self.ui_service.language_changed.connect(self._update_navigation)

    def _update_navigation(self, lang: str) -> None:
        self.setWindowTitle(self.ui_service.t("app.title"))
        self.brand_label.setText(self.ui_service.t("app.title"))
        for key, button in self.nav_buttons.items():
            button.setText(self._nav_label(key))
        self._bind_shortcuts()

    def _bind_shortcuts(self) -> None:
        self.command_palette.set_actions(
            [
                (self.ui_service.t("ui.nav.dashboard"), "", lambda: self._navigate("dashboard")),
                (self.ui_service.t("ui.nav.vehicles"), "", lambda: self._navigate("vehicles")),
                (self.ui_service.t("ui.nav.drivers"), "", lambda: self._navigate("drivers")),
                (self.ui_service.t("ui.nav.fines"), "", lambda: self._navigate("fines")),
                (self.ui_service.t("ui.nav.documents"), "", lambda: self._navigate("documents")),
                (self.ui_service.t("ui.nav.reports"), "", lambda: self._navigate("reports")),
                (self.ui_service.t("ui.nav.assignments"), "", lambda: self._navigate("assignments")),
                (self.ui_service.t("ui.nav.maintenance"), "", lambda: self._navigate("maintenance")),
                (self.ui_service.t("ui.nav.recycle"), "", lambda: self._navigate("recycle")),
                (self.ui_service.t("ui.nav.settings"), "", lambda: self._navigate("settings")),
            ]
        )

    def _navigate(self, key: str) -> None:
        index = list(self._pages.keys()).index(key)
        self.stack.setCurrentIndex(index)
        for item_key, button in self.nav_buttons.items():
            button.setChecked(item_key == key)

    def _nav_label(self, key: str) -> str:
        return self.ui_service.t(f"ui.nav.{key}")

    def _create_nav_button(self, key: str, icon_name: str) -> QPushButton:
        button = QPushButton(self._nav_label(key))
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setProperty("nav", True)
        icon_path = ICON_DIR / f"{icon_name}.svg"
        if icon_path.exists():
            button.setIcon(QIcon(str(icon_path)))
        button.clicked.connect(lambda _: self._navigate(key))
        button.setIconSize(QSize(20, 20))
        button.setMinimumHeight(40)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return button


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
