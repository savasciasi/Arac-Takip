from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppSetting:
    """Key/value store item."""

    key: str
    value: str
