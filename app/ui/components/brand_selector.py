"""Modal dialog that lets the operator pick the active brand."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...qt import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPushButton,
    QSize,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    Qt,
)
from ...services.ui_service import UIService

BRANDING_DIR = Path(__file__).resolve().parents[2] / "assets" / "branding"


class BrandSelectionDialog(QDialog):
    """Simple dialog with two branded options used at startup."""

    def __init__(
        self,
        ui_service: UIService,
        default_brand: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.ui_service = ui_service
        self.selection: str | None = None
        self._default_brand = (default_brand or "").lower()
        self._buttons: dict[str, QPushButton] = {}
        self.setWindowTitle(self.ui_service.t("app.brand.select"))
        self.setModal(True)
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        heading = QLabel(self.ui_service.t("app.brand.prompt"))
        heading.setWordWrap(True)
        heading.setProperty("role", "card-title")
        layout.addWidget(heading)

        button_row = QHBoxLayout()
        layout.addLayout(button_row)
        button_row.addStretch(1)
        for key in ("knk", "nkk"):
            button = self._build_option(key)
            self._buttons[key] = button
            button_row.addWidget(button)
        button_row.addStretch(1)

        layout.addItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Expanding))
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.rejected.connect(self.reject)
        cancel = buttons.button(QDialogButtonBox.Cancel)
        if cancel:
            cancel.setText(self.ui_service.t("ui.dialog.cancel"))
        layout.addWidget(buttons)
        if self._default_brand:
            self.apply_default(self._default_brand)

    def _build_option(self, key: str) -> QPushButton:
        """Create an option button for the provided branding key."""

        button = QPushButton(self.ui_service.t(f"app.brand.{key}"))
        button.setCursor(Qt.PointingHandCursor)
        button.setProperty("variant", "secondary")
        icon_path = BRANDING_DIR / f"{key}.svg"
        if icon_path.exists():
            button.setIcon(QIcon(str(icon_path)))
            button.setIconSize(QSize(64, 64))
        button.clicked.connect(lambda: self._choose(key))
        button.setMinimumHeight(96)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return button

    def _choose(self, key: str) -> None:
        """Persist the selection and close the dialog."""

        self.selection = key
        self.accept()

    def apply_default(self, brand: str) -> None:
        """Highlight the provided brand button for quicker confirmation."""

        target = brand.lower()
        for key, button in self._buttons.items():
            variant = "primary" if key == target else "secondary"
            button.setProperty("variant", variant)
            button.style().unpolish(button)
            button.style().polish(button)
            if key == target:
                button.setFocus(Qt.TabFocusReason)


__all__ = ["BrandSelectionDialog"]
