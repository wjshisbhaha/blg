"""Application controller orchestrating UI interactions."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QObject

from app import config as config_module
from app.config import AppConfig
from app.logging_utils import QtLogHandler, setup_logging
from app.ui.main_window import MainWindow


class MainController(QObject):
    """Glue layer between UI widgets and application services."""

    def __init__(self, window: MainWindow, config_path: Path | None = None) -> None:
        super().__init__(window)
        self._window = window
        self._config_path = config_path or config_module.get_default_config_path()
        self._config = config_module.load_config(self._config_path)
        self._setup_logging()
        self._connect_signals()
        self._window.apply_config(self._config)
        self._window.set_status("Configuration loaded")

    def _connect_signals(self) -> None:
        panel = self._window.config_panel
        panel.configChanged.connect(self._handle_config_changed)

        self._window.save_action.triggered.connect(self._save_config_dialog)
        self._window.reload_action.triggered.connect(self._reload_config)
        self._window.execute_action.triggered.connect(self._execute_job)
        self._window.clear_log_action.triggered.connect(self._window.log_panel.log_view.clear)

    def _setup_logging(self) -> None:
        log_file = self._config_path.parent / "application.log"
        ui_handler = QtLogHandler(self._window.display_log)
        level = self._get_log_level(self._config.log_level)
        setup_logging(log_file=log_file, level=level, ui_handler=ui_handler)
        self._update_log_levels(level)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Logger initialised")

    def _handle_config_changed(self, config: AppConfig) -> None:
        self._config = config
        self._window.config_panel.set_config(config)
        self._logger.info("Configuration updated via UI: %s", config)
        self._window.set_status("Configuration updated (not yet saved)")
        self._update_log_levels(self._get_log_level(config.log_level))

    def _save_config_dialog(self) -> None:
        path = self._window.ask_config_path(save=True)
        target = path or self._config_path
        config_module.save_config(self._config, target)
        self._window.set_status(f"Configuration saved to {target}")
        self._logger.info("Configuration persisted to %s", target)

    def _reload_config(self) -> None:
        path = self._window.ask_config_path(save=False)
        target = path or self._config_path
        self._config = config_module.load_config(target)
        self._window.apply_config(self._config)
        self._window.set_status(f"Configuration loaded from {target}")
        self._logger.info("Configuration reloaded from %s", target)
        self._update_log_levels(self._get_log_level(self._config.log_level))

    def _execute_job(self) -> None:
        self._window.set_status("Executing workflow...")
        self._logger.info("Starting workflow in %s environment", self._config.environment)
        # Placeholder for real business logic execution. Demonstrate lifecycle logs.
        self._emit_progress("Validating configuration")
        self._emit_progress("Connecting to endpoint %s", self._config.api_endpoint)
        self._emit_progress("Processing data batches")
        self._logger.info("Workflow completed successfully")
        self._window.set_status("Execution complete")

    def _emit_progress(self, message: str, *args) -> None:
        self._logger.debug(message, *args)
        self._logger.info(message, *args)

    @staticmethod
    def _get_log_level(level_name: str) -> int:
        return getattr(logging, level_name.upper(), logging.INFO)

    @staticmethod
    def _update_log_levels(level: int) -> None:
        root = logging.getLogger()
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)
