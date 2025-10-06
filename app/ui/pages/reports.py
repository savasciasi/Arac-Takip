"""Reports page for generating simple exports."""
from __future__ import annotations

from pathlib import Path

from ...qt import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...repo.assignments_repo import AssignmentRepository
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
        self.assignments = AssignmentRepository()
        self.exporter = Exporter()
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.header.setProperty("role", "page-title")
        self.subtitle = QLabel()
        self.subtitle.setProperty("role", "muted")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.header)
        layout.addWidget(self.subtitle)
        self.cards: dict[str, dict[str, QWidget]] = {}
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 16, 0, 0)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        layout.addLayout(self.grid)
        layout.addStretch(1)
        self._build_cards()
        self.retranslate(ui.language)

    def export_fines_csv(self) -> None:
        headers, rows = self._fines_dataset()
        path = self.exporter.export_csv(headers, rows, Path("exports/fines_report.csv"))
        self._notify_success(path)

    def export_fines_pdf(self) -> None:
        headers, rows = self._fines_dataset()
        path = self.exporter.export_pdf(
            self.ui_service.t("reports.fines.title"),
            headers,
            rows,
            Path("exports/fines_report.pdf"),
        )
        self._notify_success(path)

    def export_vehicles_csv(self) -> None:
        headers, rows = self._vehicles_dataset()
        path = self.exporter.export_csv(headers, rows, Path("exports/vehicles_report.csv"))
        self._notify_success(path)

    def export_vehicles_pdf(self) -> None:
        headers, rows = self._vehicles_dataset()
        path = self.exporter.export_pdf(
            self.ui_service.t("reports.vehicles.title"),
            headers,
            rows,
            Path("exports/vehicles_report.pdf"),
        )
        self._notify_success(path)

    def export_drivers_csv(self) -> None:
        headers, rows = self._drivers_dataset()
        path = self.exporter.export_csv(headers, rows, Path("exports/drivers_report.csv"))
        self._notify_success(path)

    def export_drivers_pdf(self) -> None:
        headers, rows = self._drivers_dataset()
        path = self.exporter.export_pdf(
            self.ui_service.t("reports.drivers.title"),
            headers,
            rows,
            Path("exports/drivers_report.pdf"),
        )
        self._notify_success(path)

    def _build_cards(self) -> None:
        definitions = [
            ("fines", self.export_fines_csv, self.export_fines_pdf),
            ("vehicles", self.export_vehicles_csv, self.export_vehicles_pdf),
            ("drivers", self.export_drivers_csv, self.export_drivers_pdf),
        ]
        for idx, (key, csv_handler, pdf_handler) in enumerate(definitions):
            frame = QFrame()
            frame.setObjectName("Card")
            layout = QVBoxLayout(frame)
            title = QLabel()
            title.setProperty("role", "card-title")
            subtitle = QLabel()
            subtitle.setProperty("role", "muted")
            subtitle.setWordWrap(True)
            button_row = QHBoxLayout()
            csv_btn = QPushButton()
            csv_btn.setProperty("variant", "primary")
            pdf_btn = QPushButton()
            pdf_btn.setProperty("variant", "secondary")
            csv_btn.clicked.connect(csv_handler)
            pdf_btn.clicked.connect(pdf_handler)
            button_row.addWidget(csv_btn)
            button_row.addWidget(pdf_btn)
            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addLayout(button_row)
            self.grid.addWidget(frame, idx // 2, idx % 2)
            self.cards[key] = {
                "frame": frame,
                "title": title,
                "subtitle": subtitle,
                "csv": csv_btn,
                "pdf": pdf_btn,
            }

    def _notify_success(self, path: Path) -> None:
        QMessageBox.information(
            self,
            self.ui_service.t("reports.notice.title"),
            self.ui_service.t("reports.notice.success").format(path=path),
        )

    def _fines_dataset(self) -> tuple[list[str], list[list[str]]]:
        vehicles = {v.id: v for v in self.vehicles.list()}
        drivers = {d.id: d for d in self.drivers.list()}
        headers = [
            self.ui_service.t("fines.form.fine_no"),
            self.ui_service.t("fines.form.vehicle"),
            self.ui_service.t("fines.form.driver"),
            self.ui_service.t("fines.form.date"),
            self.ui_service.t("fines.form.amount"),
            self.ui_service.t("fines.form.status"),
        ]
        rows: list[list[str]] = []
        for fine in self.fines.list():
            vehicle = vehicles.get(fine.vehicle_id)
            vehicle_label = vehicle.plate if vehicle else "-"
            driver = drivers.get(fine.driver_id) if fine.driver_id else None
            driver_label = (
                f"{driver.first_name} {driver.last_name}".strip() if driver else "-"
            )
            rows.append(
                [
                    fine.fine_no,
                    vehicle_label,
                    driver_label,
                    fine.date,
                    f"{fine.amount:.2f}",
                    self.ui_service.t(f"fines.status.{fine.status.lower()}"),
                ]
            )
        return headers, rows

    def _vehicles_dataset(self) -> tuple[list[str], list[list[str]]]:
        drivers = {d.id: d for d in self.drivers.list()}
        active_assignments = self.assignments.active_map()
        headers = [
            self.ui_service.t("vehicles.form.plate"),
            self.ui_service.t("vehicles.form.brand"),
            self.ui_service.t("vehicles.form.model"),
            self.ui_service.t("vehicles.form.year"),
            self.ui_service.t("vehicles.table.active_driver"),
        ]
        rows: list[list[str]] = []
        for vehicle in self.vehicles.list():
            assignment = active_assignments.get(vehicle.id)
            driver_name = "-"
            if assignment and assignment.driver_id:
                driver = drivers.get(assignment.driver_id)
                if driver:
                    driver_name = f"{driver.first_name} {driver.last_name}".strip()
            rows.append(
                [
                    vehicle.plate,
                    vehicle.brand,
                    vehicle.model,
                    str(vehicle.year or ""),
                    driver_name,
                ]
            )
        return headers, rows

    def _drivers_dataset(self) -> tuple[list[str], list[list[str]]]:
        vehicles = {v.id: v for v in self.vehicles.list()}
        assignments = self.assignments.active_by_driver()
        headers = [
            self.ui_service.t("drivers.form.first_name"),
            self.ui_service.t("drivers.form.last_name"),
            self.ui_service.t("drivers.form.phone"),
            self.ui_service.t("drivers.form.license"),
            self.ui_service.t("drivers.table.active_vehicle"),
        ]
        rows: list[list[str]] = []
        for driver in self.drivers.list():
            assignment = assignments.get(driver.id)
            vehicle_label = "-"
            if assignment and assignment.vehicle_id:
                vehicle = vehicles.get(assignment.vehicle_id)
                if vehicle:
                    vehicle_label = vehicle.plate
            rows.append(
                [
                    driver.first_name,
                    driver.last_name,
                    driver.phone,
                    driver.license_no,
                    vehicle_label,
                ]
            )
        return headers, rows

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("reports.title"))
        self.subtitle.setText(self.ui_service.t("reports.subtitle"))
        for key, widgets in self.cards.items():
            widgets["title"].setText(self.ui_service.t(f"reports.{key}.title"))
            widgets["subtitle"].setText(self.ui_service.t(f"reports.{key}.subtitle"))
            widgets["csv"].setText(self.ui_service.t("reports.actions.csv"))
            widgets["pdf"].setText(self.ui_service.t("reports.actions.pdf"))
