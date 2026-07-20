"""Logging helpers for the PyQt application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    *,
    log_file: Path,
    level: int = logging.INFO,
    ui_handler: logging.Handler | None = None,
) -> None:
    """Configure the root logger for the application."""

    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)

    if ui_handler is not None:
        ui_handler.setFormatter(formatter)
        ui_handler.setLevel(level)
        root_logger.addHandler(ui_handler)


class QtLogHandler(logging.Handler):
    """Logging handler that delegates messages to a Qt slot."""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - small wrapper
        msg = self.format(record)
        self._callback(msg)
