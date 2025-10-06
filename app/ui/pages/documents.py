"""Documents page supporting image preview and upload."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from PIL import Image
from ...qt import (
    QComboBox,
    QDesktopServices,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPixmap,
    QPushButton,
    QStandardItem,
    QStandardItemModel,
    QTableView,
    Qt,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from ...models.document import Document
from ...repo.documents_repo import DocumentRepository
from ...repo.drivers_repo import DriverRepository
from ...repo.vehicles_repo import VehicleRepository
from ...services.ui_service import UIService
from ..components.file_picker import FilePicker
from ..widgets.modal import ModalDialog
from .base_page import BasePage

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"
ID_ROLE = Qt.UserRole


class DocumentsPage(BasePage):
    """Manage document records with preview."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = DocumentRepository()
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.file_picker = FilePicker(self)
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 5, self)
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
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)
        self.table.selectionModel().currentChanged.connect(self.show_preview)
        self.table.doubleClicked.connect(self.open_document)
        self.table.clicked.connect(self.show_preview)
        self.add_btn.clicked.connect(self.add_document)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        vehicles = {vehicle.id: vehicle for vehicle in self.vehicle_repo.list()}
        drivers = {driver.id: driver for driver in self.driver_repo.list()}
        for doc in self.repo.list():
            vehicle_label = vehicles.get(doc.vehicle_id).plate if doc.vehicle_id and doc.vehicle_id in vehicles else "-"
            driver = drivers.get(doc.driver_id) if doc.driver_id else None
            driver_label = f"{driver.first_name} {driver.last_name}".strip() if driver else "-"
            row = [
                QStandardItem(doc.title),
                QStandardItem(vehicle_label),
                QStandardItem(driver_label),
                QStandardItem(doc.tags or ""),
                QStandardItem(doc.path),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(doc.id, ID_ROLE)
            row[-1].setToolTip(doc.path)
            self.model.appendRow(row)

    def _document_form(self, document: Optional[Document] = None) -> Document | None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        title = QLineEdit(document.title if document else "")
        file_path_input = QLineEdit(document.path if document else "")
        browse_btn = QPushButton(self.ui_service.t("ui.form.upload"))
        tags = QLineEdit(document.tags if document else "")
        preview = QLabel()
        preview.setAlignment(Qt.AlignCenter)
        if document and document.preview_path and Path(document.preview_path).exists():
            pix = QPixmap(document.preview_path)
            preview.setPixmap(pix.scaled(200, 200, aspectRatioMode=Qt.KeepAspectRatio))
        vehicle_combo = QComboBox()
        vehicle_combo.addItem(self.ui_service.t("documents.form.any_vehicle"), None)
        for vehicle in self.vehicle_repo.list():
            vehicle_combo.addItem(vehicle.plate, vehicle.id)
        driver_combo = QComboBox()
        driver_combo.addItem(self.ui_service.t("documents.form.any_driver"), None)
        for driver in self.driver_repo.list():
            driver_combo.addItem(f"{driver.first_name} {driver.last_name}".strip(), driver.id)
        if document and document.vehicle_id:
            idx = vehicle_combo.findData(document.vehicle_id)
            if idx >= 0:
                vehicle_combo.setCurrentIndex(idx)
        if document and document.driver_id:
            idx = driver_combo.findData(document.driver_id)
            if idx >= 0:
                driver_combo.setCurrentIndex(idx)

        def pick_file() -> None:
            file_path = self.file_picker.open(self.ui_service.t("filepicker.title"))
            if file_path:
                file_path_input.setText(str(file_path))
                pix = QPixmap(str(file_path))
                preview.setPixmap(pix.scaled(200, 200, aspectRatioMode=Qt.KeepAspectRatio))

        browse_btn.clicked.connect(pick_file)
        form.addRow(self.ui_service.t("documents.form.title"), title)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.addWidget(file_path_input)
        row_layout.addWidget(browse_btn)
        form.addRow(self.ui_service.t("documents.form.path"), row_widget)
        form.addRow(self.ui_service.t("documents.form.vehicle"), vehicle_combo)
        form.addRow(self.ui_service.t("documents.form.driver"), driver_combo)
        form.addRow(self.ui_service.t("documents.form.tags"), tags)
        form.addRow(self.ui_service.t("documents.preview"), preview)
        hint = QLabel(self.ui_service.t("documents.form.link_hint"))
        hint.setWordWrap(True)
        form.addRow(hint)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            stored_path = file_path_input.text().strip()
            preview_path = document.preview_path if document else None
            if stored_path:
                if document and stored_path == document.path:
                    pass
                else:
                    original = Path(stored_path)
                    if original.exists():
                        stored_path, preview_path = self._persist_file(original)
            return Document(
                id=document.id if document else None,
                title=title.text(),
                path=stored_path,
                preview_path=preview_path,
                tags=tags.text(),
                vehicle_id=vehicle_combo.currentData(),
                driver_id=driver_combo.currentData(),
            )
        return None

    def add_document(self) -> None:
        data = self._document_form(Document())
        if data:
            self.repo.insert(data)
            self.refresh()

    def edit_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        document_id = index.sibling(index.row(), 0).data(ID_ROLE)
        document = self.repo.get(int(document_id))
        if not document:
            return
        updated = self._document_form(document)
        if updated:
            self.repo.update(
                int(document_id),
                {
                    "title": updated.title,
                    "path": updated.path,
                    "preview_path": updated.preview_path,
                    "tags": updated.tags,
                    "vehicle_id": updated.vehicle_id,
                    "driver_id": updated.driver_id,
                },
            )
            self.refresh()

    def delete_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        document_id = index.sibling(index.row(), 0).data(ID_ROLE)
        self.repo.soft_delete(int(document_id))
        self.refresh()

    def show_preview(self, index, *_args) -> None:
        if not index.isValid():
            self.preview_label.clear()
            return
        path = index.sibling(index.row(), 4).data()
        if path and Path(path).exists():
            pix = QPixmap(path)
            self.preview_label.setPixmap(pix.scaled(240, 240, aspectRatioMode=Qt.KeepAspectRatio))
        else:
            self.preview_label.clear()

    def open_document(self, index) -> None:
        path = index.sibling(index.row(), 4).data()
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))

    def _persist_file(self, original: Path) -> tuple[str, Optional[str]]:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        destination = STORAGE_DIR / original.name
        counter = 1
        while destination.exists():
            destination = STORAGE_DIR / f"{original.stem}_{counter}{original.suffix}"
            counter += 1
        shutil.copy2(original, destination)
        preview_path = None
        try:
            with Image.open(destination) as img:
                img.thumbnail((256, 256))
                thumb = destination.with_name(f"thumb_{destination.name}")
                img.save(thumb)
                preview_path = str(thumb)
        except Exception:
            preview_path = None
        return str(destination), preview_path

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("documents.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("documents.form.title"),
            self.ui_service.t("documents.table.vehicle"),
            self.ui_service.t("documents.table.driver"),
            self.ui_service.t("documents.form.tags"),
            self.ui_service.t("documents.form.path"),
        ])
