from __future__ import annotations

from typing import List

from .base import Repository
from ..models.driver import Driver


class DriverRepository(Repository):
    """Driver repository with search helpers."""

    def __init__(self) -> None:
        super().__init__("drivers", Driver)

    def search_by_name(self, text: str) -> List[Driver]:
        like = f"%{text.lower()}%"
        return self.search(
            "LOWER(first_name || ' ' || last_name) LIKE ? AND is_deleted = 0",
            (like,),
        )
