"""Application entry point for Fleet & Fine Management."""
from __future__ import annotations

import json
import sys

from pathlib import Path


if __package__ in (None, ""):
    # When the application is executed as ``python app/main.py`` or when the
    # PyInstaller bootstrapper runs ``main.py`` as a standalone script the
    # interpreter does not treat ``app`` as a package. We gently add the
    # repository root to ``sys.path`` so absolute imports keep working.
    sys.path.append(str(Path(__file__).resolve().parents[1]))


from app.qt import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QMainWindow,
    QFont,
    QPushButton,
    QSize,
    QSizePolicy,
    QStackedWidget,
    Qt,
    QVBoxLayout,
    QWidget,
)

from app.data import database, migrations, migrations_lite, seed
from app.services.settings_service import CONFIG_PATH, SettingsService
from app.services.ui_service import UIService
from app.ui.components.brand_selector import BrandSelectionDialog
from app.ui.components.command_palette import CommandPalette
from app.ui.components.toast import ToastManager
from app.ui.qss import theme_builder
from app.ui.pages.assignments import AssignmentsPage
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.documents import DocumentsPage
from app.ui.pages.drivers import DriversPage
from app.ui.pages.fines import FinesPage
from app.ui.pages.maintenance_lite import MaintenanceLitePage
from app.ui.pages.recycle_bin import RecycleBinPage
from app.ui.pages.reports import ReportsPage
from app.ui.pages.settings import SettingsPage
from app.ui.pages.vehicles import VehiclesPage

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
ICON_DIR = ASSETS_DIR / "icons"
BRANDING_DIR = ASSETS_DIR / "branding"


class MainWindow(QMainWindow):
    """Main application window with navigation and stacked pages."""

    def __init__(
        self,
        ui_service: UIService,
        settings_service: SettingsService,
        brand_mode: str,
    ) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.ui_service = ui_service
        self.brand_mode = brand_mode
        self._app = QApplication.instance()
        self.setWindowTitle(self._brand_display())
        central = QWidget()
        central.setObjectName("CentralContainer")
        central.setAttribute(Qt.WA_StyledBackground, True)
        self.central_widget = central
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 32, 20, 32)
        self.sidebar_layout.setSpacing(16)
        self.brand_label = QLabel(self._brand_display())
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
        self.ui_service.theme_changed.connect(self._apply_theme)
        self.ui_service.text_scale_changed.connect(self._apply_text_scale)
        self._apply_text_scale(self.ui_service.text_scale)
        self._apply_theme(self.ui_service.theme, self.ui_service.profile)
        self._apply_brand_logo()

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
        self.setWindowTitle(self._brand_display())
        self.brand_label.setText(self._brand_display())
        for key, button in self.nav_buttons.items():
            button.setText(self._nav_label(key))
        self._bind_shortcuts()

    def _brand_display(self) -> str:
        brand_name = self.ui_service.t(f"app.brand.{self.brand_mode}")
        return f"{self.ui_service.t('app.title')} · {brand_name}" if brand_name else self.ui_service.t("app.title")

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

    def _apply_theme(self, theme: str, profile: str) -> None:
        if not self._app:
            return
        qss = theme_builder.generate(profile, theme, self.ui_service.text_scale)
        self._app.setStyleSheet(qss)
        self._apply_brand_logo()

    def _apply_text_scale(self, scale: float) -> None:
        if self._app:
            font = QFont(self._app.font())
            font.setPointSizeF(14 * scale)
            self._app.setFont(font)
        # refresh theme to apply new base font size token
        self._apply_theme(self.ui_service.theme, self.ui_service.profile)

    def _apply_brand_logo(self) -> None:
        """Decorate the central container with the chosen brand logo."""

        if not hasattr(self, "central_widget"):
            return
        logo_path = BRANDING_DIR / f"{self.brand_mode}.svg"
        if logo_path.exists():
            stylesheet = (
                "#CentralContainer {"
                f" background-image: url({logo_path.as_posix()});"
                " background-repeat: no-repeat;"
                " background-position: center bottom;"
                "}"
            )
        else:
            stylesheet = "#CentralContainer { background-image: none; }"
        self.central_widget.setStyleSheet(stylesheet)


def main() -> None:
    app = QApplication(sys.argv)
    defaults = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    large_text_default = str(defaults.get("large_text", "false")).lower() == "true"
    ui_service = UIService(
        language=defaults.get("default_language", "tr"),
        theme=defaults.get("default_theme", "light"),
        profile=defaults.get("theme_profile", "minimal"),
        large_text=large_text_default,
    )
    # Apply baseline theme so the brand selector inherits the styling.
    app.setStyleSheet(
        theme_builder.generate(ui_service.profile, ui_service.theme, ui_service.text_scale)
    )
    font = app.font()
    font.setPointSizeF(14 * ui_service.text_scale)
    app.setFont(font)

    selector = BrandSelectionDialog(ui_service)
    if selector.exec_() != QDialog.Accepted or not selector.selection:
        sys.exit(0)
    brand_mode = selector.selection

    database.set_brand_mode(brand_mode)
    # Ensure the required schema objects exist before services query them. The
    # migrations are idempotent so calling them on each launch keeps both KNK
    # and NKK environments aligned without manual intervention.
    migrations.run()
    migrations_lite.run()
    seed.run()
    settings = SettingsService()
    stored_language = settings.get("default_language", defaults.get("default_language", "tr"))
    stored_theme = settings.get("default_theme", defaults.get("default_theme", "light"))
    stored_profile = settings.get("theme_profile", defaults.get("theme_profile", "minimal"))
    stored_large_text = settings.get("large_text", str(large_text_default)).lower() == "true"
    ui_service.set_language(stored_language)
    ui_service.set_text_scale(stored_large_text)
    qss = ui_service.set_theme(stored_theme, stored_profile)
    app.setStyleSheet(qss)
    font = app.font()
    font.setPointSizeF(14 * ui_service.text_scale)
    app.setFont(font)

    window = MainWindow(ui_service, settings, brand_mode)
    window.resize(1280, 720)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
