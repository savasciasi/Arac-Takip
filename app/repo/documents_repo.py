from __future__ import annotations

from typing import List

from .base import Repository
from ..models.document import Document


class DocumentRepository(Repository):
    """Document repository handling file metadata."""

    def __init__(self) -> None:
        super().__init__("documents", Document)

    def search_text(self, text: str) -> List[Document]:
        like = f"%{text.lower()}%"
        return self.search("LOWER(title) LIKE ? AND is_deleted = 0", (like,))

    def for_vehicle(self, vehicle_id: int) -> List[Document]:
        return self.search("vehicle_id = ? AND is_deleted = 0", (vehicle_id,))

    def for_driver(self, driver_id: int) -> List[Document]:
        return self.search("driver_id = ? AND is_deleted = 0", (driver_id,))
