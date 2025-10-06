"""Drivers CRUD page."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QTextEdit, QVBoxLayout, QWidget

from ...models.driver import Driver
from ...repo.drivers_repo import DriverRepository
from ...services.ui_service import UIService
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class DriversPage(BasePage):
    """Manage driver records."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = DriverRepository()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 4, self)
        self.model.setHorizontalHeaderLabels([
            ui.t("drivers.form.first_name"),
            ui.t("drivers.form.last_name"),
            ui.t("drivers.form.phone"),
            ui.t("drivers.form.license"),
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
        self.add_btn.clicked.connect(self.add_driver)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for driver in self.repo.list():
            row = [
                QStandardItem(driver.first_name),
                QStandardItem(driver.last_name),
                QStandardItem(driver.phone),
                QStandardItem(driver.license_no),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(driver.id)
            self.model.appendRow(row)

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
        driver_id = index.sibling(index.row(), 0).data()
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
        driver_id = index.sibling(index.row(), 0).data()
        self.repo.soft_delete(int(driver_id))
        self.refresh()

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
        ])
