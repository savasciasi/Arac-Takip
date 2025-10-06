"""Vehicles management page with CRUD functionality."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QTextEdit, QVBoxLayout, QWidget

from ...models.vehicle import Vehicle
from ...repo.vehicles_repo import VehicleRepository
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class VehiclesPage(BasePage):
    """Page providing CRUD for vehicles."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = VehicleRepository()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 4, self)
        self.model.setHorizontalHeaderLabels([
            ui.t("vehicles.form.plate"),
            ui.t("vehicles.form.brand"),
            ui.t("vehicles.form.model"),
            ui.t("vehicles.form.year"),
        ])
        self.table.setModel(self.model)
        button_row = QHBoxLayout()
        self.add_btn = QPushButton()
        self.edit_btn = QPushButton()
        self.delete_btn = QPushButton()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.edit_btn)
        button_row.addWidget(self.delete_btn)
        layout.addWidget(self.header)
        layout.addLayout(button_row)
        layout.addWidget(self.table)
        self.add_btn.clicked.connect(self.add_vehicle)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for vehicle in self.repo.list():
            row = [
                QStandardItem(vehicle.plate),
                QStandardItem(vehicle.brand),
                QStandardItem(vehicle.model),
                QStandardItem(str(vehicle.year or "")),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(vehicle.id)
            self.model.appendRow(row)

    def _vehicle_form(self, vehicle: Optional[Vehicle] = None) -> Vehicle | None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        plate = QLineEdit(vehicle.plate if vehicle else "")
        brand = QLineEdit(vehicle.brand if vehicle else "")
        model = QLineEdit(vehicle.model if vehicle else "")
        year = QLineEdit(str(vehicle.year) if vehicle and vehicle.year else "")
        notes = QTextEdit(vehicle.notes if vehicle else "")
        form.addRow(self.ui_service.t("vehicles.form.plate"), plate)
        form.addRow(self.ui_service.t("vehicles.form.brand"), brand)
        form.addRow(self.ui_service.t("vehicles.form.model"), model)
        form.addRow(self.ui_service.t("vehicles.form.year"), year)
        form.addRow(self.ui_service.t("vehicles.form.notes"), notes)
        dialog = ModalDialog(dialog_widget, self)
        dialog.setWindowTitle(self.ui_service.t("vehicles.title"))
        if dialog.exec_() == ModalDialog.Accepted:
            return Vehicle(
                id=vehicle.id if vehicle else None,
                plate=plate.text(),
                brand=brand.text(),
                model=model.text(),
                year=int(year.text()) if year.text() else None,
                notes=notes.toPlainText(),
            )
        return None

    def add_vehicle(self) -> None:
        data = self._vehicle_form(Vehicle())
        if data:
            self.repo.insert(data)
            self.refresh()

    def edit_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        vehicle_id = index.sibling(index.row(), 0).data()
        vehicle = self.repo.get(int(vehicle_id))
        if not vehicle:
            return
        updated = self._vehicle_form(vehicle)
        if updated:
            self.repo.update(int(vehicle_id), {
                "plate": updated.plate,
                "brand": updated.brand,
                "model": updated.model,
                "year": updated.year,
                "notes": updated.notes,
            })
            self.refresh()

    def delete_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        vehicle_id = index.sibling(index.row(), 0).data()
        self.repo.soft_delete(int(vehicle_id))
        self.refresh()

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("vehicles.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("vehicles.form.plate"),
            self.ui_service.t("vehicles.form.brand"),
            self.ui_service.t("vehicles.form.model"),
            self.ui_service.t("vehicles.form.year"),
        ])
