"""Helpers to resolve resource and runtime directories across environments."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "AracTakip"


def _package_root() -> Path:
    """Return the directory containing bundled application resources."""

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def runtime_root() -> Path:
    """Return a writable directory used for mutable runtime data."""

    if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
        if sys.platform.startswith("win"):
            base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        target = base / APP_DIR_NAME
    else:
        target = _package_root()
    target.mkdir(parents=True, exist_ok=True)
    return target


def package_path(*parts: str) -> Path:
    """Resolve a path relative to the packaged resources."""

    return _package_root().joinpath(*parts)


def runtime_subdir(*parts: str) -> Path:
    """Ensure and return a writable subdirectory under runtime_root."""

    directory = runtime_root().joinpath(*parts)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def runtime_file(path: str, ensure_parent: bool = True) -> Path:
    """Return a file path inside the runtime root creating parents as needed."""

    target = runtime_root() / path
    if ensure_parent:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target


def config_path(name: str) -> Path:
    """Return the runtime config file, cloning the packaged default if missing."""

    runtime_cfg = runtime_subdir("config") / name
    if not runtime_cfg.exists():
        default_cfg = package_path("config", name)
        if default_cfg.exists():
            runtime_cfg.write_text(default_cfg.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            runtime_cfg.touch()
    return runtime_cfg


def package_config_path(name: str) -> Path:
    """Return the immutable packaged config path."""

    return package_path("config", name)


def storage_root() -> Path:
    """Return the root folder for document storage."""

    return runtime_subdir("storage")


def backups_root() -> Path:
    """Return the directory containing per-brand backups."""

    return runtime_subdir("backups")


def exports_root() -> Path:
    """Return the directory used for generated export files."""

    return runtime_subdir("exports")


def state_file(name: str) -> Path:
    """Return a persistent file used for migration bookkeeping, etc."""

    return runtime_subdir("state") / name
