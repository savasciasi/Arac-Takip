"""Documents page supporting image preview and upload."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from PIL import Image
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QPixmap

from ...models.document import Document
from ...repo.documents_repo import DocumentRepository
from ...services.ui_service import UIService
from ..components.file_picker import FilePicker
from ..widgets.modal import ModalDialog
from .base_page import BasePage


class DocumentsPage(BasePage):
    """Manage document records with preview."""

    def __init__(self, ui: UIService, parent=None) -> None:
        super().__init__(ui, parent)
        self.repo = DocumentRepository()
        self.file_picker = FilePicker(self)
        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 3, self)
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
        layout.addWidget(self.preview_label)
        self.table.clicked.connect(self.show_preview)
        self.add_btn.clicked.connect(self.add_document)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.refresh()
        self.retranslate(ui.language)

    def refresh(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for doc in self.repo.list():
            row = [
                QStandardItem(doc.title),
                QStandardItem(doc.path),
                QStandardItem(doc.tags or ""),
            ]
            for item in row:
                item.setEditable(False)
            row[0].setData(doc.id)
            self.model.appendRow(row)

    def _document_form(self, document: Optional[Document] = None) -> Document | None:
        dialog_widget = QWidget()
        form = QFormLayout(dialog_widget)
        title = QLineEdit(document.title if document else "")
        file_path_input = QLineEdit(document.path if document else "")
        browse_btn = QPushButton(self.ui_service.t("ui.form.upload"))
        tags = QLineEdit(document.tags if document else "")
        notes = QTextEdit()
        preview = QLabel()

        def pick_file() -> None:
            file_path = self.file_picker.open(self.ui_service.t("filepicker.title"))
            if file_path:
                file_path_input.setText(str(file_path))
                pix = QPixmap(str(file_path))
                preview.setPixmap(pix.scaled(200, 200, aspectRatioMode=1))

        browse_btn.clicked.connect(pick_file)
        form.addRow(self.ui_service.t("documents.form.title"), title)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.addWidget(file_path_input)
        row_layout.addWidget(browse_btn)
        form.addRow(self.ui_service.t("documents.form.path"), row_widget)
        form.addRow(self.ui_service.t("documents.form.tags"), tags)
        form.addRow(self.ui_service.t("documents.form.notes"), notes)
        form.addRow(self.ui_service.t("documents.preview"), preview)
        dialog = ModalDialog(dialog_widget, self)
        if dialog.exec_() == ModalDialog.Accepted:
            stored_path = file_path_input.text()
            if Path(stored_path).exists():
                destination = Path("storage") / Path(stored_path).name
                destination.parent.mkdir(exist_ok=True)
                shutil.copy2(stored_path, destination)
                stored_path = str(destination)
                try:
                    with Image.open(destination) as img:
                        img.thumbnail((256, 256))
                        thumb_path = destination.with_name(f"thumb_{destination.name}")
                        img.save(thumb_path)
                except Exception:
                    thumb_path = None
            else:
                thumb_path = None
            return Document(
                id=document.id if document else None,
                title=title.text(),
                path=stored_path,
                preview_path=str(thumb_path) if thumb_path else None,
                tags=tags.text(),
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
        document_id = index.sibling(index.row(), 0).data()
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
                },
            )
            self.refresh()

    def delete_selected(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        document_id = index.sibling(index.row(), 0).data()
        self.repo.soft_delete(int(document_id))
        self.refresh()

    def show_preview(self, index) -> None:
        path = index.sibling(index.row(), 1).data()
        if path and Path(path).exists():
            pix = QPixmap(path)
            self.preview_label.setPixmap(pix.scaled(240, 240, aspectRatioMode=1))

    def retranslate(self, _: str) -> None:  # type: ignore[override]
        self.header.setText(self.ui_service.t("documents.title"))
        self.add_btn.setText(self.ui_service.t("ui.form.add"))
        self.edit_btn.setText(self.ui_service.t("ui.form.edit"))
        self.delete_btn.setText(self.ui_service.t("ui.dialog.delete"))
        self.model.setHorizontalHeaderLabels([
            self.ui_service.t("documents.form.title"),
            self.ui_service.t("documents.form.path"),
            self.ui_service.t("documents.form.tags"),
        ])
