"""Drivers CRUD page."""
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

from ...models.driver import Driver
from ...repo.assignments_repo import AssignmentRepository
from ...repo.vehicles_repo import VehicleRepository
from ...repo.drivers_repo import DriverRepository
from ...repo.documents_repo import DocumentRepository
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


ID_ROLE = Qt.UserRole


class DriversPage(BasePage):
    """Manage driver records."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = DriverRepository()
        self.documents = DocumentRepository()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 5, self)
        self.model.setHorizontalHeaderLabels([
            ui.t("drivers.form.first_name"),
            ui.t("drivers.form.last_name"),
            ui.t("drivers.form.phone"),
            ui.t("drivers.form.license"),
            ui.t("drivers.table.active_vehicle"),
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
        self.doc_list.setObjectName("DriverDocuments")
        layout.addWidget(self.doc_label)
        layout.addWidget(self.doc_list)
        self.add_btn.clicked.connect(self.add_driver)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.table.selectionModel().currentChanged.connect(self._update_document_panel)
        self.doc_list.itemDoubleClicked.connect(self._open_document)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        vehicles = {vehicle.id: vehicle for vehicle in VehicleRepository().list()}
        assignments = AssignmentRepository().active_by_driver()
        for driver in self.repo.list():
            assignment = assignments.get(driver.id)
            vehicle_label = self.ui_service.t("drivers.table.no_vehicle")
            if assignment and assignment.vehicle_id:
                vehicle = vehicles.get(assignment.vehicle_id)
                if vehicle:
                    vehicle_label = vehicle.plate
            row = [
                QStandardItem(driver.first_name),
                QStandardItem(driver.last_name),
                QStandardItem(driver.phone),
                QStandardItem(driver.license_no),
                QStandardItem(vehicle_label),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(driver.id, ID_ROLE)
            self.model.appendRow(row)
        self._update_document_panel()

    def _driver_form(self, driver: Optional[Driver] = None) -> Driver | None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        first_name = QLineEdit(driver.first_name if driver else "")
        last_name = QLineEdit(driver.last_name if driver else "")
        phone = QLineEdit(driver.phone if driver else "")
        license_no = QLineEdit(driver.license_no if driver else "")
        notes = QTextEdit(driver.notes if driver else "")
        form.addRow(self.ui_service.t("drivers.form.first_name"), first_name)
        form.addRow(self.ui_service.t("drivers.form.last_name"), last_name)
        form.addRow(self.ui_service.t("drivers.form.phone"), phone)
        form.addRow(self.ui_service.t("drivers.form.license"), license_no)
        form.addRow(self.ui_service.t("drivers.form.notes"), notes)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            return Driver(
                id=driver.id if driver else None,
                first_name=first_name.text(),
                last_name=last_name.text(),
                phone=phone.text(),
                license_no=license_no.text(),
                notes=notes.toPlainText(),
            )
        return None

    def add_driver(self) -> None:
        data = self._driver_form(Driver())
        if data:
            self.repo.insert(data)
            self.refresh()

    def edit_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        driver_id = index.sibling(index.row(), 0).data(ID_ROLE)
        if driver_id is None:
            return
        driver = self.repo.get(int(driver_id))
        if not driver:
            return
        updated = self._driver_form(driver)
        if updated:
            self.repo.update(int(driver_id), {
                "first_name": updated.first_name,
                "last_name": updated.last_name,
                "phone": updated.phone,
                "license_no": updated.license_no,
                "notes": updated.notes,
            })
            self.refresh()

    def delete_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        driver_id = index.sibling(index.row(), 0).data(ID_ROLE)
        if driver_id is None:
            return
        self.repo.soft_delete(int(driver_id))
        self.refresh()

    def _current_driver_id(self) -> Optional[int]:
        selection = self.table.selectionModel().currentIndex()
        if not selection.isValid():
            return None
        value = selection.sibling(selection.row(), 0).data(ID_ROLE)
        return int(value) if value is not None else None

    def _update_document_panel(self, *_) -> None:
        self.doc_list.clear()
        driver_id = self._current_driver_id()
        if driver_id is None:
            return
        for doc in self.documents.for_driver(driver_id):
            item = QListWidgetItem(doc.title or doc.path)
            item.setData(ID_ROLE, doc.path)
            item.setToolTip(doc.path)
            self.doc_list.addItem(item)

    def _open_document(self, item: QListWidgetItem) -> None:
        path = item.data(ID_ROLE)
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("drivers.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("drivers.form.first_name"),
            self.ui_service.t("drivers.form.last_name"),
            self.ui_service.t("drivers.form.phone"),
            self.ui_service.t("drivers.form.license"),
            self.ui_service.t("drivers.table.active_vehicle"),
        ])
        self.doc_label.setText(self.ui_service.t("drivers.documents.title"))
