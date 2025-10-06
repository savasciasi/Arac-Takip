"""Recycle bin page to restore or permanently delete records."""
from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from ...repo.vehicles_repo import VehicleRepository
from ...repo.drivers_repo import DriverRepository
from ...repo.fines_repo import FineRepository
from ...services.ui_service import UIService
from .base_page import BasePage


class RecycleBinPage(BasePage):
    """Display soft deleted entries with restore/delete actions."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.fine_repo = FineRepository()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        layout.addWidget(self.header)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        button_row = QHBoxLayout()
        self.restore_btn = QPushButton()
        self.delete_btn = QPushButton()
        button_row.addWidget(self.restore_btn)
        button_row.addWidget(self.delete_btn)
        layout.addLayout(button_row)
        self.restore_btn.clicked.connect(self.restore_item)
        self.delete_btn.clicked.connect(self.delete_item)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.list_widget.clear()
        for repo, label in [
            (self.vehicle_repo, "vehicle"),
            (self.driver_repo, "driver"),
            (self.fine_repo, "fine"),
        ]:
            for item in repo.list(include_deleted=True):
                if getattr(item, "is_deleted", 0):
                    display = f"{label.upper()} #{item.id}"
                    self.list_widget.addItem(f"{display}")

    def restore_item(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        text = item.text()
        target, record_id = text.split(" #")
        record_id = int(record_id)
        repo = self._repo_for(target.lower())
        repo.restore(record_id)
        self.refresh()

    def delete_item(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        text = item.text()
        target, record_id = text.split(" #")
        record_id = int(record_id)
        repo = self._repo_for(target.lower())
        repo.delete(record_id)
        self.refresh()

    def _repo_for(self, key: str):
        return {
            "vehicle": self.vehicle_repo,
            "driver": self.driver_repo,
            "fine": self.fine_repo,
        }[key]

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("recycle.title"))
        self.restore_btn.setText(self.ui_service.t("recycle.restore"))
        self.delete_btn.setText(self.ui_service.t("recycle.delete_permanently"))
