"""Dashboard page with summary cards and upcoming maintenance list."""
from __future__ import annotations

from datetime import date, timedelta

from ...qt import QHBoxLayout, QLabel, QListWidget, QVBoxLayout

from ...repo.fines_repo import FineRepository
from ...repo.maintenance_repo import MaintenanceRepository
from ...repo.vehicles_repo import VehicleRepository
from ...repo.drivers_repo import DriverRepository
from ...services.ui_service import UIService
from ..widgets.card import Card
from .base_page import BasePage


class DashboardPage(BasePage):
    """Displays KPIs and upcoming maintenance reminders."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.fine_repo = FineRepository()
        self.maintenance_repo = MaintenanceRepository()
        layout = QVBoxLayout(self)
        self.cards_container = QHBoxLayout()
        layout.addLayout(self.cards_container)
        self.vehicle_card = Card(ui.t("dashboard.cards.vehicles"), parent=self)
        self.driver_card = Card(ui.t("dashboard.cards.drivers"), parent=self)
        self.fine_card = Card(ui.t("dashboard.cards.fines"), parent=self)
        self.maintenance_card = Card(ui.t("dashboard.cards.maintenance"), parent=self)
        for card in (self.vehicle_card, self.driver_card, self.fine_card, self.maintenance_card):
            self.cards_container.addWidget(card)
        self.recent_label = QLabel()
        self.recent_fines = QListWidget()
        self.upcoming_label = QLabel()
        self.upcoming_list = QListWidget()
        layout.addWidget(self.recent_label)
        layout.addWidget(self.recent_fines)
        layout.addWidget(self.upcoming_label)
        layout.addWidget(self.upcoming_list)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        vehicles = self.vehicle_repo.list()
        drivers = self.driver_repo.list()
        fines = self.fine_repo.summary()
        upcoming = self.maintenance_repo.upcoming((date.today() + timedelta(days=14)).isoformat())
        self.vehicle_card.set_value(str(len(vehicles)))
        self.driver_card.set_value(str(len(drivers)))
        self.fine_card.set_value(f"{fines['open']:.0f}")
        self.maintenance_card.set_value(str(len(upcoming)))
        self.recent_fines.clear()
        for item in self.fine_repo.list()[:5]:
            self.recent_fines.addItem(f"{item.fine_no} — {item.amount:.2f}")
        self.upcoming_list.clear()
        for reminder in upcoming:
            self.upcoming_list.addItem(f"{reminder.title} ({reminder.next_date})")

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.vehicle_card.set_title(self.ui_service.t("dashboard.cards.vehicles"))
        self.driver_card.set_title(self.ui_service.t("dashboard.cards.drivers"))
        self.fine_card.set_title(self.ui_service.t("dashboard.cards.fines"))
        self.maintenance_card.set_title(self.ui_service.t("dashboard.cards.maintenance"))
        self.recent_label.setText(self.ui_service.t("dashboard.recentFines"))
        self.upcoming_label.setText(self.ui_service.t("dashboard.upcomingMaintenance"))
