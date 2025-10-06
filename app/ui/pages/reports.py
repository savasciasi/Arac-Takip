"""Reports page for generating simple exports."""
from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ...repo.fines_repo import FineRepository
from ...repo.vehicles_repo import VehicleRepository
from ...repo.drivers_repo import DriverRepository
from ...services.exporter import Exporter
from ...services.ui_service import UIService
from .base_page import BasePage


class ReportsPage(BasePage):
    """Create CSV/PDF exports for key datasets."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.fines = FineRepository()
        self.vehicles = VehicleRepository()
        self.drivers = DriverRepository()
        self.exporter = Exporter()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        layout.addWidget(self.header)
        self.fines_csv = QPushButton()
        self.fines_pdf = QPushButton()
        self.vehicles_csv = QPushButton()
        self.drivers_csv = QPushButton()
        for btn in (self.fines_csv, self.fines_pdf, self.vehicles_csv, self.drivers_csv):
            layout.addWidget(btn)
        self.fines_csv.clicked.connect(self.export_fines_csv)
        self.fines_pdf.clicked.connect(self.export_fines_pdf)
        self.vehicles_csv.clicked.connect(self.export_vehicles_csv)
        self.drivers_csv.clicked.connect(self.export_drivers_csv)
        self.retranslate(ui.language)

    def export_fines_csv(self) -> None:
        data = self.fines.list()
        headers = [
            self.ui_service.t("fines.form.fine_no"),
            self.ui_service.t("fines.form.date"),
            self.ui_service.t("fines.form.amount"),
        ]
        rows = [[fine.fine_no, fine.date, str(fine.amount)] for fine in data]
        self.exporter.export_csv(headers, rows, Path("exports/fines_report.csv"))

    def export_fines_pdf(self) -> None:
        data = self.fines.list()
        headers = [
            self.ui_service.t("fines.form.fine_no"),
            self.ui_service.t("fines.form.date"),
            self.ui_service.t("fines.form.amount"),
        ]
        rows = [[fine.fine_no, fine.date, f"{fine.amount:.2f}"] for fine in data]
        self.exporter.export_pdf("Fines Report", headers, rows, Path("exports/fines_report.pdf"))

    def export_vehicles_csv(self) -> None:
        data = self.vehicles.list()
        headers = [
            self.ui_service.t("vehicles.form.plate"),
            self.ui_service.t("vehicles.form.brand"),
            self.ui_service.t("vehicles.form.model"),
        ]
        rows = [[v.plate, v.brand, v.model] for v in data]
        self.exporter.export_csv(headers, rows, Path("exports/vehicles_report.csv"))

    def export_drivers_csv(self) -> None:
        data = self.drivers.list()
        headers = [
            self.ui_service.t("drivers.form.first_name"),
            self.ui_service.t("drivers.form.last_name"),
            self.ui_service.t("drivers.form.phone"),
        ]
        rows = [[d.first_name, d.last_name, d.phone] for d in data]
        self.exporter.export_csv(headers, rows, Path("exports/drivers_report.csv"))

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("reports.title"))
        self.fines_csv.setText(self.ui_service.t("reports.generateCsv"))
        self.fines_pdf.setText(self.ui_service.t("reports.generatePdf"))
        self.vehicles_csv.setText(self.ui_service.t("reports.vehicles"))
        self.drivers_csv.setText(self.ui_service.t("reports.drivers"))
