"""Enhanced table view with zebra striping and sticky header."""
from __future__ import annotations

from ...qt import QHeaderView, QTableView, Qt


class DataTable(QTableView):
    """Table view with preset styling and usability tweaks."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setHighlightSections(False)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.setObjectName("DataTable")
