"""Vehicles management page with CRUD functionality."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...models.vehicle import Vehicle
from ...repo.assignments_repo import AssignmentRepository
from ...repo.drivers_repo import DriverRepository
from ...repo.documents_repo import DocumentRepository
from ...repo.vehicles_repo import VehicleRepository
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


ID_ROLE = Qt.UserRole

class VehiclesPage(BasePage):
    """Page providing CRUD for vehicles."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = VehicleRepository()
        self.documents = DocumentRepository()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 5, self)
        self.model.setHorizontalHeaderLabels([
            ui.t("vehicles.form.plate"),
            ui.t("vehicles.form.brand"),
            ui.t("vehicles.form.model"),
            ui.t("vehicles.form.year"),
            ui.t("vehicles.table.active_driver"),
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
        self.doc_label = QLabel()
        self.doc_label.setProperty("role", "muted")
        self.doc_list = QListWidget()
        self.doc_list.setObjectName("VehicleDocuments")
        layout.addWidget(self.doc_label)
        layout.addWidget(self.doc_list)
        self.add_btn.clicked.connect(self.add_vehicle)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.table.selectionModel().currentChanged.connect(self._update_document_panel)
        self.doc_list.itemDoubleClicked.connect(self._open_document)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        assignments = AssignmentRepository().active_map()
        drivers = {driver.id: driver for driver in DriverRepository().list()}
        for vehicle in self.repo.list():
            assignment = assignments.get(vehicle.id)
            driver_label = self.ui_service.t("vehicles.table.no_driver")
            if assignment and assignment.driver_id:
                driver = drivers.get(assignment.driver_id)
                if driver:
                    driver_label = f"{driver.first_name} {driver.last_name}".strip()
            row = [
                QStandardItem(vehicle.plate),
                QStandardItem(vehicle.brand),
                QStandardItem(vehicle.model),
                QStandardItem(str(vehicle.year or "")),
                QStandardItem(driver_label),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(vehicle.id, ID_ROLE)
            self.model.appendRow(row)
        self._update_document_panel()

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
        vehicle_id = index.sibling(index.row(), 0).data(ID_ROLE)
        if vehicle_id is None:
            return
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
        vehicle_id = index.sibling(index.row(), 0).data(ID_ROLE)
        if vehicle_id is None:
            return
        self.repo.soft_delete(int(vehicle_id))
        self.refresh()

    def _current_vehicle_id(self) -> Optional[int]:
        selection = self.table.selectionModel().currentIndex()
        if not selection.isValid():
            return None
        value = selection.sibling(selection.row(), 0).data(ID_ROLE)
        return int(value) if value is not None else None

    def _update_document_panel(self, *_) -> None:
        self.doc_list.clear()
        vehicle_id = self._current_vehicle_id()
        if vehicle_id is None:
            return
        for doc in self.documents.for_vehicle(vehicle_id):
            item = QListWidgetItem(doc.title or doc.path)
            item.setData(ID_ROLE, doc.path)
            item.setToolTip(doc.path)
            self.doc_list.addItem(item)

    def _open_document(self, item: QListWidgetItem) -> None:
        path = item.data(ID_ROLE)
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))

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
            self.ui_service.t("vehicles.table.active_driver"),
        ])
        self.doc_label.setText(self.ui_service.t("vehicles.documents.title"))
