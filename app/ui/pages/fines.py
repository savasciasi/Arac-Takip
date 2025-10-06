"""Fines management page."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...models.fine import Fine
from ...repo.drivers_repo import DriverRepository
from ...repo.fines_repo import FineRepository
from ...repo.vehicles_repo import VehicleRepository
from ...services.exporter import Exporter
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class FinesPage(BasePage):
    """Manage fines with filters and exports."""

    STATUSES = ["OPEN", "PAID", "DISPUTED"]

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = FineRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.exporter = Exporter()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        filter_row = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem(ui.t("fines.filter.status"), None)
        for status in self.STATUSES:
            self.status_filter.addItem(ui.t(f"fines.status.{status.lower()}"), status)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_row.addWidget(self.status_filter)
        layout.addLayout(filter_row)
        self.table = QTableView()
        self.model = QStandardItemModel(0, 6, self)
        self.table.setModel(self.model)
        button_row = QHBoxLayout()
        self.add_btn = QPushButton()
        self.edit_btn = QPushButton()
        self.delete_btn = QPushButton()
        self.export_csv_btn = QPushButton()
        self.export_pdf_btn = QPushButton()
        for btn in (self.add_btn, self.edit_btn, self.delete_btn, self.export_csv_btn, self.export_pdf_btn):
            button_row.addWidget(btn)
        layout.addWidget(self.header)
        layout.addLayout(button_row)
        layout.addWidget(self.table)
        self.add_btn.clicked.connect(self.add_fine)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for fine in self.repo.list():
            row = [
                QStandardItem(fine.fine_no),
                QStandardItem(fine.date),
                QStandardItem(f"{fine.amount:.2f}"),
                QStandardItem(fine.status),
                QStandardItem(fine.description or ""),
                QStandardItem(", ".join(json.loads(fine.attachments_json or "[]"))),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(fine.id)
            self.model.appendRow(row)
        self.apply_filters()

    def apply_filters(self) -> None:
        status = self.status_filter.currentData()
        for row in range(self.model.rowCount()):
            matches = True
            if status and self.model.item(row, 3).text() != status:
                matches = False
            self.table.setRowHidden(row, not matches)

    def _fine_form(self, fine: Optional[Fine] = None) -> Fine | None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        fine_no = QLineEdit(fine.fine_no if fine else "")
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(date.fromisoformat(fine.date) if fine and fine.date else date.today())
        amount = QDoubleSpinBox()
        amount.setRange(0, 1000000)
        amount.setValue(fine.amount if fine else 0)
        status = QComboBox()
        for s in self.STATUSES:
            status.addItem(self.ui_service.t(f"fines.status.{s.lower()}"), s)
        if fine:
            idx = self.STATUSES.index(fine.status) if fine.status in self.STATUSES else 0
            status.setCurrentIndex(idx)
        description = QTextEdit(fine.description if fine else "")
        attachments = QListWidget()
        existing = json.loads(fine.attachments_json or "[]") if fine else []
        for path in existing:
            attachments.addItem(path)
        form.addRow(self.ui_service.t("fines.form.fine_no"), fine_no)
        form.addRow(self.ui_service.t("fines.form.date"), date_edit)
        form.addRow(self.ui_service.t("fines.form.amount"), amount)
        form.addRow(self.ui_service.t("fines.form.status"), status)
        form.addRow(self.ui_service.t("fines.form.description"), description)
        form.addRow(self.ui_service.t("fines.form.attachments"), attachments)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            return Fine(
                id=fine.id if fine else None,
                vehicle_id=fine.vehicle_id if fine else 1,
                driver_id=fine.driver_id if fine else 1,
                fine_no=fine_no.text(),
                date=date_edit.date().toString("yyyy-MM-dd"),
                amount=float(amount.value()),
                description=description.toPlainText(),
                status=status.currentData(),
                attachments_json=json.dumps([attachments.item(i).text() for i in range(attachments.count())]),
            )
        return None

    def add_fine(self) -> None:
        data = self._fine_form(Fine())
        if data:
            self.repo.insert(data)
            self.refresh()

    def edit_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        fine_id = index.sibling(index.row(), 0).data()
        fine = self.repo.get(int(fine_id))
        if not fine:
            return
        updated = self._fine_form(fine)
        if updated:
            self.repo.update(
                int(fine_id),
                {
                    "fine_no": updated.fine_no,
                    "date": updated.date,
                    "amount": updated.amount,
                    "status": updated.status,
                    "description": updated.description,
                    "attachments_json": updated.attachments_json,
                },
            )
            self.refresh()

    def delete_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        fine_id = index.sibling(index.row(), 0).data()
        self.repo.soft_delete(int(fine_id))
        self.refresh()

    def export_csv(self) -> None:
        headers = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
        rows = []
        for row in range(self.model.rowCount()):
            if self.table.isRowHidden(row):
                continue
            rows.append([self.model.item(row, col).text() for col in range(self.model.columnCount())])
        self.exporter.export_csv(headers, rows, Path("exports/fines.csv"))

    def export_pdf(self) -> None:
        headers = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
        rows = []
        for row in range(self.model.rowCount()):
            if self.table.isRowHidden(row):
                continue
            rows.append([self.model.item(row, col).text() for col in range(self.model.columnCount())])
        self.exporter.export_pdf("Fines", headers, rows, Path("exports/fines.pdf"))

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("fines.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.export_csv_btn.setText(self.ui_service.t("export.csv"))
        self.export_pdf_btn.setText(self.ui_service.t("export.pdf"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("fines.form.fine_no"),
            self.ui_service.t("fines.form.date"),
            self.ui_service.t("fines.form.amount"),
            self.ui_service.t("fines.form.status"),
            self.ui_service.t("fines.form.description"),
            self.ui_service.t("fines.form.attachments"),
        ])
