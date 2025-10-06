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
    QMessageBox,
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
        self.vehicle_filter = QComboBox()
        self.driver_filter = QComboBox()
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self.vehicle_filter)
        filter_row.addWidget(self.driver_filter)
        layout.addLayout(filter_row)
        self.table = QTableView()
        self.model = QStandardItemModel(0, 8, self)
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

        self._vehicles: list = []
        self._drivers: list = []
        self._vehicle_map: dict[int, object] = {}
        self._driver_map: dict[int, object] = {}
        self._configure_filters()
        self.refresh()
        self.retranslate(ui.language)

    def _configure_filters(self) -> None:
        """Populate filter combo boxes with translated placeholders."""

        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.vehicle_filter.currentIndexChanged.connect(self.refresh)
        self.driver_filter.currentIndexChanged.connect(self.refresh)

    def _load_reference_data(self) -> None:
        self._vehicles = self.vehicle_repo.list()
        self._drivers = self.driver_repo.list()
        self._vehicle_map = {vehicle.id: vehicle for vehicle in self._vehicles}
        self._driver_map = {driver.id: driver for driver in self._drivers}

    def _populate_filter_options(self) -> None:
        status_value = self.status_filter.currentData()
        vehicle_value = self.vehicle_filter.currentData()
        driver_value = self.driver_filter.currentData()

        self.status_filter.blockSignals(True)
        self.vehicle_filter.blockSignals(True)
        self.driver_filter.blockSignals(True)

        self.status_filter.clear()
        self.status_filter.addItem(
            f"{self.ui_service.t('fines.filter.status')}: {self.ui_service.t('ui.filter.all')}",
            None,
        )
        for status in self.STATUSES:
            self.status_filter.addItem(self.ui_service.t(f"fines.status.{status.lower()}"), status)

        self.vehicle_filter.clear()
        self.vehicle_filter.addItem(
            f"{self.ui_service.t('fines.filter.vehicle')}: {self.ui_service.t('ui.filter.all')}",
            None,
        )
        for vehicle in self._vehicles:
            self.vehicle_filter.addItem(vehicle.plate, vehicle.id)

        self.driver_filter.clear()
        self.driver_filter.addItem(
            f"{self.ui_service.t('fines.filter.driver')}: {self.ui_service.t('ui.filter.all')}",
            None,
        )
        for driver in self._drivers:
            self.driver_filter.addItem(f"{driver.first_name} {driver.last_name}".strip(), driver.id)

        def _restore(combo: QComboBox, value: object) -> None:
            if value is None:
                combo.setCurrentIndex(0)
            else:
                index = combo.findData(value)
                combo.setCurrentIndex(index if index >= 0 else 0)

        _restore(self.status_filter, status_value)
        _restore(self.vehicle_filter, vehicle_value)
        _restore(self.driver_filter, driver_value)

        self.status_filter.blockSignals(False)
        self.vehicle_filter.blockSignals(False)
        self.driver_filter.blockSignals(False)

    def refresh(self) -> None:
        self._load_reference_data()
        self._populate_filter_options()
        fines = self.repo.filter(
            status=self.status_filter.currentData(),
            vehicle_id=self.vehicle_filter.currentData(),
            driver_id=self.driver_filter.currentData(),
        )
        self.model.removeRows(0, self.model.rowCount())
        for fine in fines:
            vehicle = self._vehicle_map.get(fine.vehicle_id)
            driver = self._driver_map.get(fine.driver_id) if fine.driver_id else None
            attachments = ", ".join(json.loads(fine.attachments_json or "[]"))
            status_label = self.ui_service.t(f"fines.status.{fine.status.lower()}")
            driver_label = (
                f"{driver.first_name} {driver.last_name}".strip()
                if driver
                else self.ui_service.t("fines.table.no_driver")
            )
            vehicle_label = vehicle.plate if vehicle else self.ui_service.t("fines.table.no_vehicle")
            row = [
                QStandardItem(fine.fine_no),
                QStandardItem(vehicle_label),
                QStandardItem(driver_label),
                QStandardItem(fine.date),
                QStandardItem(f"{fine.amount:.2f}"),
                QStandardItem(status_label),
                QStandardItem(fine.description or ""),
            ]
            attachment_item = QStandardItem(attachments)
            row.append(attachment_item)
            for item in row:
                item.setEditable(False)
            row[0].setData(fine.id)
            self.model.appendRow(row)

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
        payment_date = QDateEdit()
        payment_date.setCalendarPopup(True)
        payment_date.setDate(
            date.fromisoformat(fine.payment_date) if fine and fine.payment_date else date.today()
        )
        description = QTextEdit(fine.description if fine else "")
        attachments = QListWidget()
        existing = json.loads(fine.attachments_json or "[]") if fine else []
        for path in existing:
            attachments.addItem(path)
        vehicle_combo = QComboBox()
        for vehicle in self._vehicles:
            vehicle_combo.addItem(vehicle.plate, vehicle.id)
        driver_combo = QComboBox()
        for driver in self._drivers:
            driver_combo.addItem(f"{driver.first_name} {driver.last_name}".strip(), driver.id)
        if fine and fine.vehicle_id:
            index = vehicle_combo.findData(fine.vehicle_id)
            if index >= 0:
                vehicle_combo.setCurrentIndex(index)
        if fine and fine.driver_id:
            index = driver_combo.findData(fine.driver_id)
            if index >= 0:
                driver_combo.setCurrentIndex(index)
        elif driver_combo.count() > 0:
            driver_combo.setCurrentIndex(0)
        if fine and fine.status in self.STATUSES:
            idx = self.STATUSES.index(fine.status)
            status.setCurrentIndex(idx)

        def _toggle_payment(index: int) -> None:
            payment_date.setEnabled(status.itemData(index) == "PAID")

        status.currentIndexChanged.connect(_toggle_payment)
        _toggle_payment(status.currentIndex())

        form.addRow(self.ui_service.t("fines.form.fine_no"), fine_no)
        form.addRow(self.ui_service.t("fines.form.vehicle"), vehicle_combo)
        form.addRow(self.ui_service.t("fines.form.driver"), driver_combo)
        form.addRow(self.ui_service.t("fines.form.date"), date_edit)
        form.addRow(self.ui_service.t("fines.form.amount"), amount)
        form.addRow(self.ui_service.t("fines.form.status"), status)
        form.addRow(self.ui_service.t("fines.form.payment_date"), payment_date)
        form.addRow(self.ui_service.t("fines.form.description"), description)
        form.addRow(self.ui_service.t("fines.form.attachments"), attachments)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            if vehicle_combo.count() == 0 or driver_combo.count() == 0:
                QMessageBox.warning(
                    self,
                    self.ui_service.t("fines.dialog.missing_relations_title"),
                    self.ui_service.t("fines.dialog.missing_relations"),
                )
                return None
            return Fine(
                id=fine.id if fine else None,
                vehicle_id=vehicle_combo.currentData(),
                driver_id=driver_combo.currentData(),
                fine_no=fine_no.text(),
                date=date_edit.date().toString("yyyy-MM-dd"),
                amount=float(amount.value()),
                description=description.toPlainText(),
                status=status.currentData(),
                payment_date=
                    payment_date.date().toString("yyyy-MM-dd") if payment_date.isEnabled() else None,
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
                    "vehicle_id": updated.vehicle_id,
                    "driver_id": updated.driver_id,
                    "date": updated.date,
                    "amount": updated.amount,
                    "status": updated.status,
                    "payment_date": updated.payment_date,
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
            rows.append([self.model.item(row, col).text() for col in range(self.model.columnCount())])
        self.exporter.export_csv(headers, rows, Path("exports/fines.csv"))

    def export_pdf(self) -> None:
        headers = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
        rows = []
        for row in range(self.model.rowCount()):
            rows.append([self.model.item(row, col).text() for col in range(self.model.columnCount())])
        self.exporter.export_pdf(self.ui_service.t("fines.title"), headers, rows, Path("exports/fines.pdf"))

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("fines.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.export_csv_btn.setText(self.ui_service.t("export.csv"))
        self.export_pdf_btn.setText(self.ui_service.t("export.pdf"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("fines.form.fine_no"),
            self.ui_service.t("fines.form.vehicle"),
            self.ui_service.t("fines.form.driver"),
            self.ui_service.t("fines.form.date"),
            self.ui_service.t("fines.form.amount"),
            self.ui_service.t("fines.form.status"),
            self.ui_service.t("fines.form.description"),
            self.ui_service.t("fines.form.attachments"),
        ])
        self.refresh()
