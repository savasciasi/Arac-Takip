"""Basic smoke tests ensuring modules import."""
from __future__ import annotations

import importlib
import pytest

try:  # noqa: SIM105 - module level skip for missing dependencies
    from app.data import database  # type: ignore
except Exception as exc:  # pragma: no cover - infrastructure dependent
    pytest.skip(f"Database backend unavailable: {exc}", allow_module_level=True)


pytest.importorskip("PyQt5")


def test_import_main() -> None:
    module = importlib.import_module("app.main")
    assert hasattr(module, "main")
