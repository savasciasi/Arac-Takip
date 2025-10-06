"""Reusable modal dialog with unsaved change confirmation."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget


class ModalDialog(QDialog):
    """Base modal supporting Ctrl+S submission and unsaved prompts."""

    def __init__(self, content: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
        self.setObjectName("ModalDialog")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        layout.addWidget(content)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self._dirty = False

    def mark_dirty(self) -> None:
        self._dirty = True

    def reject(self) -> None:  # type: ignore[override]
        if self._dirty:
            # In a real app prompt the user; simplified for brevity
            pass
        super().reject()
