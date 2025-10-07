"""Application logging helpers with rotating file handlers."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .runtime_paths import runtime_subdir

_LOG_HANDLER_MARK = "_aractakip_handler"
_LOG_FILE: Path | None = None
_CONFIGURED = False


def _build_handler(target: Path) -> RotatingFileHandler:
    """Create a rotating file handler with a consistent format."""

    handler = RotatingFileHandler(
        target,
        maxBytes=512 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    setattr(handler, _LOG_HANDLER_MARK, True)
    return handler


def configure_logging(brand: str | None = None) -> Path:
    """Initialise logging and return the active log file path."""

    global _LOG_FILE, _CONFIGURED
    log_dir = runtime_subdir("logs")
    filename = "launcher.log" if not brand else f"{brand.lower()}_app.log"
    target = log_dir / filename

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove previous dedicated handlers to avoid duplicate writes when
    # switching between launcher and brand specific logs.
    for handler in list(root_logger.handlers):
        if getattr(handler, _LOG_HANDLER_MARK, False):
            root_logger.removeHandler(handler)
            handler.close()

    file_handler = _build_handler(target)
    root_logger.addHandler(file_handler)

    if not _CONFIGURED:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s: %(message)s")
        )
        root_logger.addHandler(stream_handler)
        logging.captureWarnings(True)
        _CONFIGURED = True

    _LOG_FILE = target
    logging.getLogger(__name__).info(
        "Logging initialised (brand=%s)", brand or "launcher"
    )
    return target


def current_log_file() -> Path:
    """Return the current log file, configuring logging if required."""

    if _LOG_FILE is None:
        return configure_logging()
    return _LOG_FILE


def logs_directory() -> Path:
    """Return the directory containing generated log files."""

    return runtime_subdir("logs")
