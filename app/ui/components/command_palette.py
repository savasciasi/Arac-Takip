"""Command palette with fuzzy search and keyboard navigation."""
from __future__ import annotations

import difflib
from typing import Callable, List, Sequence, Tuple

from ...qt import QListWidget, QListWidgetItem, QLineEdit, QVBoxLayout, QWidget, Qt


class CommandPalette(QWidget):
    """Simple command palette supporting keyboard navigation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("CommandPalette")
        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search")
        self.list_widget = QListWidget()
        layout.addWidget(self.search_input)
        layout.addWidget(self.list_widget)
        self.actions: List[Tuple[str, str, Callable[[], None]]] = []
        self.recent: List[Tuple[str, str, Callable[[], None]]] = []
        self.search_input.textChanged.connect(self._filter)
        self.search_input.returnPressed.connect(self.trigger_selected)
        self.list_widget.itemActivated.connect(self.trigger_selected)

    def open_palette(self) -> None:
        self._populate_list(self.actions)
        self.search_input.setText("")
        self.show()
        self.raise_()
        self.search_input.setFocus()

    def set_actions(self, actions: Sequence[Tuple[str, str, Callable[[], None]]]) -> None:
        self.actions = list(actions)
        self._populate_list(self.actions)

    def _populate_list(self, items: Sequence[Tuple[str, str, Callable[[], None]]]) -> None:
        self.list_widget.clear()
        for label, description, _ in items:
            item = QListWidgetItem(f"{label} — {description}")
            self.list_widget.addItem(item)

    def _filter(self, text: str) -> None:
        if not text:
            self._populate_list(self.actions)
            return
        matches = []
        for action in self.actions:
            score = difflib.SequenceMatcher(None, text.lower(), action[0].lower()).ratio()
            matches.append((score, action))
        matches.sort(key=lambda x: x[0], reverse=True)
        self._populate_list([match[1] for match in matches[:15]])

    def trigger_selected(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.actions):
            return
        label, description, callback = self.actions[row]
        callback()
        self.recent.insert(0, (label, description, callback))
        self.recent = self.recent[:5]
        self.hide()
