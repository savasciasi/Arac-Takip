"""Base page providing shared helpers."""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget

from ...services.ui_service import UIService


class BasePage(QWidget):
    """Base class for all application pages."""

    def __init__(self, ui: UIService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui_service = ui
        ui.language_changed.connect(self.retranslate)

    def retranslate(self, _: str) -> None:
        """Override to update labels when language changes."""
        pass
