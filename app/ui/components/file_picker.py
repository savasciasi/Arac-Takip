"""Simple file picker dialog wrapper."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...qt import QFileDialog, QWidget


class FilePicker:
    """Wrapper to provide consistent file dialog behaviour."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self.parent = parent

    def open(self, title: str, directory: str | None = None, filter: str = "All Files (*.*)") -> Optional[Path]:
        file_path, _ = QFileDialog.getOpenFileName(self.parent, title, directory or str(Path.home()), filter)
        return Path(file_path) if file_path else None
