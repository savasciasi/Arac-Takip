"""Basic smoke tests ensuring modules import."""
from __future__ import annotations

import importlib
import pytest


pytest.importorskip("PyQt5")


def test_import_main() -> None:
    module = importlib.import_module("app.main")
    assert hasattr(module, "main")
