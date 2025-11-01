"""Main window implementation for the application."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
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

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._config_panel)
        self._stack.addWidget(self._log_panel)

        central = QWidget(self)
        self.setCentralWidget(central)

        central_layout = QHBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(central_layout)

        self._sidebar = QListWidget(central)
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setSpacing(4)
        self._sidebar.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._sidebar.setFixedWidth(200)

        first_item: QListWidgetItem | None = None
        for index, title in enumerate(("配置管理", "运行日志")):
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, title)
            self._sidebar.addItem(item)
            if index == 0:
                first_item = item

        if first_item is not None:
            self._sidebar.setCurrentItem(first_item)

        content_frame = QFrame(central)
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        self._breadcrumb = QLabel("首页 / 配置管理", content_frame)
        self._breadcrumb.setObjectName("breadcrumb")
        content_layout.addWidget(self._breadcrumb)
        content_layout.addWidget(self._stack, stretch=1)

        central_layout.addWidget(self._sidebar)
        central_layout.addWidget(content_frame, stretch=1)

        self._toolbar = self._create_toolbar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        self._apply_styles()
        self._sidebar.currentRowChanged.connect(self._handle_navigation)

    @property
    def config_panel(self) -> ConfigurationPanel:
        return self._config_panel

    @property
    def log_panel(self) -> LogPanel:
        return self._log_panel

    def _handle_navigation(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        item = self._sidebar.item(index)
        if item is None:
            return
        title = item.data(Qt.ItemDataRole.UserRole) or item.text()
        self._breadcrumb.setText(f"首页 / {title}")

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
        background = "#f5f6fa"
        sidebar_bg = "#10192e"
        sidebar_hover = "#1d2b4f"
        accent = "#00a3ff"
        text_primary = "#0f172a"
        text_on_dark = "#e8f4ff"

        stylesheet = f"""
        QMainWindow {{
            background-color: {background};
            color: {text_primary};
        }}
        QWidget#contentFrame {{
            background-color: white;
            border-radius: 12px;
        }}
        QLabel#breadcrumb {{
            font-size: 15px;
            color: {text_primary};
            font-weight: 500;
        }}
        QListWidget#sidebar {{
            background-color: {sidebar_bg};
            color: {text_on_dark};
            border: none;
            padding: 24px 12px;
        }}
        QListWidget#sidebar::item {{
            padding: 12px 16px;
            border-radius: 8px;
            margin: 4px 0;
        }}
        QListWidget#sidebar::item:selected {{
            background-color: {accent};
            color: white;
        }}
        QListWidget#sidebar::item:hover {{
            background-color: {sidebar_hover};
        }}
        QLabel#logHeader {{
            font-weight: 600;
            font-size: 16px;
            color: {text_primary};
        }}
        QLabel#summaryLabel {{
            color: {text_primary};
        }}
        QGroupBox {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-top: 12px;
            background-color: #f9fafc;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px;
            color: {text_primary};
            font-weight: 600;
        }}
        QPushButton {{
            background-color: {accent};
            color: white;
            border-radius: 6px;
            padding: 8px 18px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: #0090e8;
        }}
        QPushButton:pressed {{
            background-color: #007ac4;
        }}
        QPlainTextEdit#logView {{
            background-color: #0f172a;
            color: {text_on_dark};
            border: 1px solid #1d2b4f;
            border-radius: 8px;
        }}
        QToolBar {{
            background: white;
            spacing: 12px;
            padding: 4px 12px;
        }}
        QStatusBar {{
            background: white;
            color: {text_primary};
        }}
        """
        self.setStyleSheet(stylesheet)

    def apply_config(self, config: AppConfig) -> None:
        self._config_panel.set_config(config)

    def display_log(self, message: str) -> None:
        self._log_panel.messageEmitted.emit(message)
