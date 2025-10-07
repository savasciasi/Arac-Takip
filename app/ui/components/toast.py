"""Stacked toast notifications with fade animation."""
from __future__ import annotations

from typing import List

from ...qt import QEasingCurve, QPropertyAnimation, QPoint, QLabel, Qt, QTimer, QVBoxLayout, QWidget


class Toast(QWidget):
    """Single toast widget."""

    def __init__(self, text: str, duration: int = 3000, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        self._timer = QTimer(self)
        self._timer.setInterval(duration)
        self._timer.timeout.connect(self.fade_out)
        self._timer.start()
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self.opacity_anim.setDuration(180)
        self.opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)

    def fade_out(self) -> None:
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.close)
        self.opacity_anim.start()


class ToastManager:
    """Manage stacking of toast notifications at the bottom-right corner."""

    def __init__(self, host: QWidget) -> None:
        self.host = host
        self.toasts: List[Toast] = []

    def show(self, message: str) -> None:
        toast = Toast(message, parent=self.host)
        toast.show()
        self.toasts.append(toast)
        self._reposition()
        toast.opacity_anim.finished.connect(lambda: self._cleanup(toast))

    def _cleanup(self, toast: Toast) -> None:
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._reposition()

    def _reposition(self) -> None:
        margin = 20
        y_offset = margin
        for toast in reversed(self.toasts):
            geo = toast.frameGeometry()
            parent_geo = self.host.geometry()
            x = parent_geo.right() - geo.width() - margin
            y = parent_geo.bottom() - y_offset - geo.height()
            toast.move(x, y)
            y_offset += geo.height() + 10
