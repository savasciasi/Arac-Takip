"""Card widget with modern styling."""
from __future__ import annotations

from ...qt import QLabel, QVBoxLayout, QWidget


class Card(QWidget):
    """Displays a titled content area with consistent padding."""

    def __init__(self, title: str, subtitle: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        layout.addWidget(self.title_label)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("CardValue")
        layout.addWidget(self.value_label)
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("CardSubtitle")
            layout.addWidget(self.subtitle_label)
        else:
            self.subtitle_label = None

    def set_value(self, text: str) -> None:
        self.value_label.setText(text)

    def set_title(self, text: str) -> None:
        self.title_label.setText(text)
