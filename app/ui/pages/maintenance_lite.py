"""Maintenance reminders page."""
from __future__ import annotations

from datetime import date

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDateEdit, QFormLayout, QLabel, QPushButton, QTableView, QTextEdit, QVBoxLayout, QWidget

from ...models.maintenance import MaintenanceReminder
from ...repo.maintenance_repo import MaintenanceRepository
from ...services.maintenance_lite_service import MaintenanceLiteService
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class MaintenanceLitePage(BasePage):
    """Show and manage maintenance reminders."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = MaintenanceRepository()
        self.service = MaintenanceLiteService()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        layout.addWidget(self.header)
        self.table = QTableView()
        self.model = QStandardItemModel(0, 3, self)
        self.table.setModel(self.model)
        layout.addWidget(self.table)
        self.add_btn = QPushButton()
        self.complete_btn = QPushButton()
        layout.addWidget(self.add_btn)
        layout.addWidget(self.complete_btn)
        self.add_btn.clicked.connect(self.add_reminder)
        self.complete_btn.clicked.connect(self.complete_reminder)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for reminder in self.repo.list():
            row = [
                QStandardItem(reminder.title),
                QStandardItem(reminder.next_date),
                QStandardItem("✓" if reminder.done else ""),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(reminder.id)
            self.model.appendRow(row)

    def add_reminder(self) -> None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        title = QTextEdit()
        title.setFixedHeight(40)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(date.today())
        notes = QTextEdit()
        form.addRow(self.ui_service.t("maintenance.form.title"), title)
        form.addRow(self.ui_service.t("maintenance.form.next_date"), date_edit)
        form.addRow(self.ui_service.t("maintenance.form.notes"), notes)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            reminder = MaintenanceReminder(
                title=title.toPlainText(),
                next_date=date_edit.date().toString("yyyy-MM-dd"),
                notes=notes.toPlainText(),
                vehicle_id=1,
            )
            self.repo.insert(reminder)
            self.refresh()

    def complete_reminder(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        reminder_id = index.sibling(index.row(), 0).data()
        self.service.complete(int(reminder_id))
        self.refresh()

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("maintenance.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.complete_btn.setText(self.ui_service.t("maintenance.upcoming"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("maintenance.form.title"),
            self.ui_service.t("maintenance.form.next_date"),
            self.ui_service.t("maintenance.form.notes"),
        ])
