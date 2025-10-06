"""Animated skeleton placeholder widget."""
from __future__ import annotations

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PyQt5.QtWidgets import QWidget


class Skeleton(QWidget):
    """Skeleton placeholder with shimmering animation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(20)
        self._offset = 0.0
        self.anim = QPropertyAnimation(self, b"offset")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.start()

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = property(get_offset, set_offset)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(220, 225, 235))
        gradient.setColorAt(self._offset, QColor(245, 247, 250))
        gradient.setColorAt(1, QColor(220, 225, 235))
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()
