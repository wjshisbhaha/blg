"""Main window implementation for the application."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QToolBar,
)

from app.config import AppConfig
from app.ui.config_panel import ConfigurationPanel
from app.ui.log_panel import LogPanel


class MainWindow(QMainWindow):
    """Application main window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Logic Gateway")
        self.resize(1100, 720)

        self._config_panel = ConfigurationPanel(self)
        self._log_panel = LogPanel(self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._config_panel)
        splitter.addWidget(self._log_panel)
        splitter.setSizes([400, 700])

        self.setCentralWidget(splitter)

        self._toolbar = self._create_toolbar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        self._apply_styles()

    @property
    def config_panel(self) -> ConfigurationPanel:
        return self._config_panel

    @property
    def log_panel(self) -> LogPanel:
        return self._log_panel

    def set_status(self, message: str, timeout: int = 5000) -> None:
        self._status_bar.showMessage(message, timeout)

    def ask_config_path(self, *, save: bool) -> Path | None:
        dialog_func = QFileDialog.getSaveFileName if save else QFileDialog.getOpenFileName
        title = "Save Configuration" if save else "Load Configuration"
        path, _ = dialog_func(self, title, "", "JSON Files (*.json)")
        if path:
            return Path(path)
        return None

    def _create_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))

        self.save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        self.reload_action = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        self.execute_action = QAction(QIcon.fromTheme("system-run"), "Execute", self)
        self.clear_log_action = QAction(QIcon.fromTheme("edit-clear"), "Clear Log", self)

        for action in (
            self.save_action,
            self.reload_action,
            self.execute_action,
            self.clear_log_action,
        ):
            toolbar.addAction(action)

        return toolbar

    def _apply_styles(self) -> None:
        palette_color = "#0F172A"
        accent = "#2563EB"
        secondary = "#1E293B"
        text_color = "#E2E8F0"

        stylesheet = f"""
        QMainWindow {{
            background-color: {palette_color};
            color: {text_color};
        }}
        QLabel#logHeader {{
            font-weight: 600;
            font-size: 16px;
            color: {text_color};
        }}
        QLabel#summaryLabel {{
            color: {text_color};
        }}
        QGroupBox {{
            border: 1px solid {secondary};
            border-radius: 6px;
            margin-top: 12px;
            background-color: {secondary};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px;
            color: {text_color};
            font-weight: 600;
        }}
        QPushButton {{
            background-color: {accent};
            color: {text_color};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: #1D4ED8;
        }}
        QPushButton:pressed {{
            background-color: #1E40AF;
        }}
        QPlainTextEdit#logView {{
            background-color: #0B1120;
            color: {text_color};
            border: 1px solid {secondary};
            border-radius: 6px;
        }}
        QToolBar {{
            background: {secondary};
            spacing: 12px;
            padding: 4px 12px;
        }}
        QStatusBar {{
            background: {secondary};
            color: {text_color};
        }}
        """
        self.setStyleSheet(stylesheet)

    def apply_config(self, config: AppConfig) -> None:
        self._config_panel.set_config(config)

    def display_log(self, message: str) -> None:
        self._log_panel.messageEmitted.emit(message)
