"""Vehicle assignments page showing history and allowing new assignments."""
from __future__ import annotations

from datetime import date

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QTextEdit, QVBoxLayout, QWidget

from ...repo.assignments_repo import AssignmentRepository
from ...repo.drivers_repo import DriverRepository
from ...repo.vehicles_repo import VehicleRepository
from ...services.assignment_service import AssignmentService
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class AssignmentsPage(BasePage):
    """Manage assignments between vehicles and drivers."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = AssignmentRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.service = AssignmentService()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        layout.addWidget(self.header)
        self.table = QTableView()
        self.model = QStandardItemModel(0, 4, self)
        self.table.setModel(self.model)
        layout.addWidget(self.table)
        self.add_btn = QPushButton()
        layout.addWidget(self.add_btn)
        self.add_btn.clicked.connect(self.add_assignment)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for assignment in self.repo.list():
            vehicle = self.vehicle_repo.get(assignment.vehicle_id)
            driver = self.driver_repo.get(assignment.driver_id)
            row = [
                QStandardItem(vehicle.plate if vehicle else str(assignment.vehicle_id)),
                QStandardItem(driver.full_name if driver else str(assignment.driver_id)),
                QStandardItem(assignment.from_date),
                QStandardItem(assignment.to_date or "-"),
            ]
            for item in row:
                item.setEditable(False)
            self.model.appendRow(row)

    def add_assignment(self) -> None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        vehicle_combo = QComboBox()
        for vehicle in self.vehicle_repo.list():
            vehicle_combo.addItem(vehicle.plate, vehicle.id)
        driver_combo = QComboBox()
        for driver in self.driver_repo.list():
            driver_combo.addItem(driver.full_name, driver.id)
        notes = QTextEdit()
        form.addRow(self.ui_service.t("assignments.form.vehicle"), vehicle_combo)
        form.addRow(self.ui_service.t("assignments.form.driver"), driver_combo)
        form.addRow(self.ui_service.t("assignments.form.notes"), notes)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            self.service.assign(vehicle_combo.currentData(), driver_combo.currentData(), notes.toPlainText())
            self.refresh()

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("assignments.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("assignments.form.vehicle"),
            self.ui_service.t("assignments.form.driver"),
            self.ui_service.t("assignments.form.from_date"),
            self.ui_service.t("assignments.form.to_date"),
        ])
