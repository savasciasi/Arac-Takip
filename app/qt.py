"""Centralised PyQt5 import helpers with graceful error messaging."""
from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Iterable


def _load_pyqt5() -> tuple[ModuleType, ModuleType, ModuleType]:
    """Import PyQt5 submodules or exit with a friendly hint."""

    try:
        qt_core = importlib.import_module("PyQt5.QtCore")
        qt_gui = importlib.import_module("PyQt5.QtGui")
        qt_widgets = importlib.import_module("PyQt5.QtWidgets")
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        message = (
            "PyQt5 bulunamadı.\n"
            "Lütfen uygulamayı çalıştırmadan önce bağımlılıkları kurun:\n"
            "    pip install -r requirements.txt\n"
            "veya PyQt5 paketini ayrı olarak yükleyin."
        )
        print(message, file=sys.stderr)
        raise SystemExit(1) from exc
    return qt_core, qt_gui, qt_widgets


QtCore, QtGui, QtWidgets = _load_pyqt5()


def __getattr__(name: str):  # pragma: no cover - dynamic attribute forwarding
    for module in _module_iter():
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(name)


def _module_iter() -> Iterable[ModuleType]:
    return (QtCore, QtGui, QtWidgets)


__all__ = sorted({name for module in _module_iter() for name in dir(module) if not name.startswith("_")})
