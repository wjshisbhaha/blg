"""Logging panel widget for the main window."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QPlainTextEdit


class LogPanel(QWidget):
    """Widget that displays log records."""

    messageEmitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_label = QLabel("Runtime Log", self)
        header_label.setObjectName("logHeader")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.clear_button = QPushButton("Clear", self)
        header_layout.addWidget(self.clear_button)
        layout.addLayout(header_layout)

        self.log_view = QPlainTextEdit(self)
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("logView")
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_view, stretch=1)

        self.clear_button.clicked.connect(self.log_view.clear)
        self.messageEmitted.connect(self.append_message)

    def append_message(self, message: str) -> None:
        self.log_view.appendPlainText(message)
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()
