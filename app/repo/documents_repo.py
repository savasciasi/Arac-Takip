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
