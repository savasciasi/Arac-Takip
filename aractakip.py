"""Application launcher that prepares the runtime environment."""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "default_language": "tr",
    "default_theme": "light",
    "theme_profile": "minimal",
    "large_text": "false",
    "active_brand": "knk",
}


def _load_dotenv() -> None:
    """Load environment variables from a local .env file if available."""

    try:
        from dotenv import load_dotenv  # type: ignore import-not-found
    except Exception:
        return
    try:
        load_dotenv()
    except Exception:
        # Dotenv loading should never block startup; ignore malformed files.
        pass


def _user_data_dir() -> Path:
    """Determine the writable per-user data directory."""

    if sys.platform.startswith("win"):
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "AracTakip"


def _prepare_runtime_dirs() -> Path:
    """Create runtime directories and seed the default config file."""

    data_dir = Path(os.environ.get("ARACTAKIP_DATA_DIR", _user_data_dir()))
    storage_dir = data_dir / "storage"
    logs_dir = data_dir / "logs"
    storage_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    config_path = storage_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    os.environ["ARACTAKIP_DATA_DIR"] = str(data_dir)
    return data_dir


def _log_fatal(data_dir: Path, error: BaseException) -> Path:
    """Append a fatal error entry to the log file and return its path."""

    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "fatal.log"
    trace = traceback.format_exc()
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n=== Fatal error ===\n")
        handle.write(f"[{timestamp} UTC] {type(error).__name__}: {error}\n")
        handle.write(trace)
    return log_path


def _show_windows_dialog(message: str, title: str = "AracTakip") -> None:
    """Display a message box on Windows without failing elsewhere."""

    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
            None,
            message,
            title,
            0x10,  # MB_ICONERROR
        )
    except Exception:
        # Never let dialog failures prevent the traceback from propagating.
        pass


def run() -> None:
    """Entrypoint invoked by both console and packaged builds."""

    _load_dotenv()
    data_dir = _prepare_runtime_dirs()
    logger = logging.getLogger("aractakip.launcher")
    try:
        from app.utils.logging_utils import configure_logging

        configure_logging()
        logger.info("Launcher initialised (data_dir=%s)", data_dir)
    except Exception:  # pragma: no cover - logging bootstrap failures
        # Logging is a best-effort feature for the launcher. Failures here
        # should not prevent the UI from attempting to start.
        pass
    try:
        from app.main import main

        main()
    except Exception as exc:  # pragma: no cover - runtime guard
        log_path = _log_fatal(data_dir, exc)
        try:
            logger.exception("Fatal error during launch")
        except Exception:
            pass
        _show_windows_dialog(
            (
                "Uygulama kritik bir hatayla kapandı.\n"
                "The application encountered a fatal error.\n\n"
                f"Detaylar log dosyasında: {log_path}"
            )
        )
        raise


if __name__ == "__main__":
    run()
