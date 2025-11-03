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
from app.ui.test_panel import EquipmentTestPanel


class MainWindow(QMainWindow):
    """Application main window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Business Logic Gateway")
        self.resize(1100, 720)

        self._config_panel = ConfigurationPanel(self)
        self._test_panel = EquipmentTestPanel(self)
        self._log_footer = LogPanel(self)
        self._log_footer.setMinimumHeight(200)
        self._log_page = LogPanel(self)
        self._log_panels: tuple[LogPanel, ...] = (self._log_footer, self._log_page)

        self._stack = QStackedWidget(self)

        self._navigation: list[tuple[str, QWidget]] = [
            ("配置管理", self._config_panel),
            ("运行日志", self._log_page),
            ("设备联调", self._test_panel),
        ]

        for _, widget in self._navigation:
            self._stack.addWidget(widget)

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
        for index, (title, _) in enumerate(self._navigation):
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
        content_layout.addWidget(self._log_footer)

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
        return self._log_footer

    @property
    def test_panel(self) -> EquipmentTestPanel:
        return self._test_panel

    def _handle_navigation(self, index: int) -> None:
        if not 0 <= index < len(self._navigation):
            return
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
        sidebar_bg = "#f1f2f4"
        sidebar_hover = "#e2e5ea"
        accent = "#00a3ff"
        text_primary = "#0f172a"
        text_on_sidebar = "#1f2937"
        text_on_dark = "#e8f4ff"
        success = "#00c853"
        warning = "#ffb300"
        danger = "#ff5252"

        stylesheet = f"""
        QMainWindow {{
            background-color: {background};
            color: {text_primary};
        }}
        QWidget#contentFrame {{
            background-color: white;
            border-radius: 12px;
        }}
        QWidget#logContainer {{
            background-color: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }}
        QLabel#breadcrumb {{
            font-size: 15px;
            color: {text_primary};
            font-weight: 500;
        }}
        QListWidget#sidebar {{
            background-color: {sidebar_bg};
            color: {text_on_sidebar};
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
        QLabel[status="pending"] {{
            color: {warning};
        }}
        QLabel[status="success"] {{
            color: {success};
        }}
        QLabel[status="failure"] {{
            color: {danger};
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
        QPushButton[variant="ghost"] {{
            background-color: transparent;
            color: {accent};
            border: 1px solid rgba(0, 163, 255, 0.25);
        }}
        QPushButton[variant="ghost"]:hover {{
            background-color: rgba(0, 163, 255, 0.08);
        }}
        QPlainTextEdit#logView {{
            background-color: #0f172a;
            color: {text_on_dark};
            border: 1px solid #1d2b4f;
            border-radius: 8px;
        }}
        QTableWidget#deviceTable {{
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            gridline-color: #e2e8f0;
            selection-background-color: rgba(0, 163, 255, 0.12);
            selection-color: {text_primary};
        }}
        QHeaderView::section {{
            background-color: #f1f5f9;
            border: none;
            border-bottom: 1px solid #e2e8f0;
            padding: 10px 12px;
            font-weight: 600;
            color: {text_primary};
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
        self._test_panel.set_devices(config.devices)

    def display_log(self, message: str) -> None:
        for panel in self._log_panels:
            panel.messageEmitted.emit(message)

    def clear_logs(self) -> None:
        for panel in self._log_panels:
            panel.log_view.clear()
