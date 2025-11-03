"""Pi six-axis button control panel."""

from __future__ import annotations

import logging
from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import PiControlBinding, default_pi_bindings


class PiControlPanel(QWidget):
    """Ele.me-inspired interface for Raspberry Pi six-axis button mappings."""

    controlsChanged = pyqtSignal(object)
    commandIssued = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._controls: list[PiControlBinding] = default_pi_bindings()
        self._button_map: Dict[str, QPushButton] = {}
        self._suppress_table = False
        self._build_ui()
        self._populate_table()
        self._refresh_buttons()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(18)

        header = QLabel("Pi 六轴按键控制", self)
        header.setObjectName("logHeader")
        header.setStyleSheet("font-size: 20px;")
        layout.addWidget(header)

        subheader = QLabel(
            "以饿了么清爽风格构建的树莓派六轴控制台，可自定义 GPIO 和指令映射，",
            self,
        )
        subheader.setWordWrap(True)
        layout.addWidget(subheader)

        content_row = QHBoxLayout()
        content_row.setSpacing(18)
        layout.addLayout(content_row)

        self._control_box = QGroupBox("实时控制台", self)
        control_layout = QVBoxLayout(self._control_box)
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(12)

        instruction = QLabel("点击按键可立即触发预设动作，并记录到全局日志。", self._control_box)
        instruction.setStyleSheet("color: #64748b;")
        control_layout.addWidget(instruction)

        grid = QGridLayout()
        grid.setSpacing(12)
        control_layout.addLayout(grid)
        self._control_grid = grid

        content_row.addWidget(self._control_box, 1)

        config_box = QGroupBox("按钮映射配置", self)
        config_layout = QVBoxLayout(config_box)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(12)

        help_label = QLabel("支持自定义 GPIO、指令和文案，保存后会自动记忆。", config_box)
        help_label.setStyleSheet("color: #64748b;")
        config_layout.addWidget(help_label)

        self._table = QTableWidget(0, 4, config_box)
        self._table.setHorizontalHeaderLabels(["轴向", "GPIO", "指令", "描述"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setObjectName("deviceTable")
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.SelectedClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self._table.itemChanged.connect(self._handle_item_changed)
        config_layout.addWidget(self._table, 1)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self._reset_button = QPushButton("恢复默认布局", config_box)
        self._reset_button.setProperty("variant", "ghost")
        self._reset_button.clicked.connect(self._reset_defaults)
        action_row.addWidget(self._reset_button)

        config_layout.addLayout(action_row)
        content_row.addWidget(config_box, 1)

    def _refresh_buttons(self) -> None:
        for button in self._button_map.values():
            button.deleteLater()
        self._button_map.clear()

        positions = {
            "X+": (1, 2),
            "X-": (1, 0),
            "Y+": (0, 1),
            "Y-": (2, 1),
            "Z+": (0, 2),
            "Z-": (2, 0),
        }

        for row in range(3):
            for col in range(3):
                item = self._control_grid.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)

        center_label = QLabel("原点", self._control_box)
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_label.setStyleSheet("color: #94a3b8;")
        self._control_grid.addWidget(center_label, 1, 1)

        for binding in self._controls:
            button = QPushButton(binding.axis, self._control_box)
            button.setMinimumHeight(56)
            button.setProperty("variant", "ghost")
            button.clicked.connect(lambda checked=False, b=binding: self._trigger_binding(b))
            self._button_map[binding.axis] = button
            position = positions.get(binding.axis)
            if position:
                self._control_grid.addWidget(button, *position)
            else:
                row = self._control_grid.rowCount()
                self._control_grid.addWidget(button, row, 0, 1, 3)

    def _populate_table(self) -> None:
        self._suppress_table = True
        self._table.setRowCount(len(self._controls))
        for row, binding in enumerate(self._controls):
            for col, value in enumerate(
                [binding.axis, binding.gpio_pin, binding.command, binding.description]
            ):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)
        self._suppress_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        if self._suppress_table:
            return
        row = item.row()
        if not 0 <= row < len(self._controls):
            return
        binding = self._controls[row]
        column = item.column()
        text = item.text().strip()
        if column == 1:
            binding.gpio_pin = text or binding.gpio_pin
        elif column == 2:
            binding.command = text
        elif column == 3:
            binding.description = text
        else:
            return
        self.controlsChanged.emit(self.get_controls())
        self._logger.info(
            "Pi 控制轴 %s 更新：GPIO=%s, 指令=%s, 描述=%s",
            binding.axis,
            binding.gpio_pin,
            binding.command,
            binding.description or "—",
        )

    def _trigger_binding(self, binding: PiControlBinding) -> None:
        self._logger.info(
            "触发 Pi 控制：%s (GPIO %s) -> %s",
            binding.axis,
            binding.gpio_pin,
            binding.command or "未配置指令",
        )
        self.commandIssued.emit(binding.command)

    def _reset_defaults(self) -> None:
        self.set_controls(default_pi_bindings())
        self.controlsChanged.emit(self.get_controls())
        self._logger.info("Pi 六轴映射已恢复默认配置")

    def set_controls(self, controls: List[PiControlBinding]) -> None:
        self._controls = [PiControlBinding.from_dict(c.to_dict()) for c in controls]
        self._populate_table()
        self._refresh_buttons()

    def get_controls(self) -> list[PiControlBinding]:
        return [PiControlBinding.from_dict(c.to_dict()) for c in self._controls]

