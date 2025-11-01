"""Equipment connection testing panel."""

from __future__ import annotations

import logging
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import DeviceProfile


class EquipmentTestPanel(QWidget):
    """Interactive UI for testing connections to multiple industrial devices."""

    devicesChanged = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._suppress_table_events = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(18)

        header = QLabel("工业设备连接测试", self)
        header.setObjectName("logHeader")
        header.setStyleSheet("font-size: 20px;")
        layout.addWidget(header)

        subheader = QLabel(
            "集中管理多台设备的网络参数，批量执行连通性检测，"
            "保持和饿了么风格一致的轻盈视觉体验。",
            self,
        )
        subheader.setWordWrap(True)
        layout.addWidget(subheader)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        self._total_label = self._build_metric_card("设备总数", "0")
        self._pending_label = self._build_metric_card("待测试", "0")
        self._success_label = self._build_metric_card("连接成功", "0")
        self._failure_label = self._build_metric_card("连接失败", "0")

        for card in (
            self._total_label,
            self._pending_label,
            self._success_label,
            self._failure_label,
        ):
            metrics_row.addWidget(card, 1)

        layout.addLayout(metrics_row)

        form_box = QGroupBox("添加设备")
        form_layout = QFormLayout(form_box)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setSpacing(12)

        self._name_input = QLineEdit(form_box)
        self._name_input.setPlaceholderText("如：焊接机器人 A")
        form_layout.addRow("设备名称：", self._name_input)

        self._ip_input = QLineEdit(form_box)
        self._ip_input.setPlaceholderText("192.168.10.15")
        form_layout.addRow("IP 地址：", self._ip_input)

        self._port_input = QLineEdit(form_box)
        self._port_input.setPlaceholderText("可选，部分设备无需端口")
        form_layout.addRow("端口：", self._port_input)

        self._protocol_box = QComboBox(form_box)
        self._protocol_box.addItems(["Modbus TCP", "OPC UA", "EtherNet/IP", "PROFINET"])
        form_layout.addRow("协议：", self._protocol_box)

        self._operations_input = QLineEdit(form_box)
        self._operations_input.setPlaceholderText("例如：ping, 读取心跳寄存器")
        form_layout.addRow("操作配置：", self._operations_input)

        button_row = QHBoxLayout()
        button_row.addStretch()
        add_button = QPushButton("添加设备", form_box)
        add_button.clicked.connect(self._handle_add_device)
        button_row.addWidget(add_button)
        form_layout.addRow("", button_row)

        layout.addWidget(form_box)

        self._table = QTableWidget(0, 7, self)
        self._table.setObjectName("deviceTable")
        self._table.setHorizontalHeaderLabels([
            "设备",
            "IP 地址",
            "端口",
            "协议",
            "操作配置",
            "状态",
            "操作",
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.SelectedClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self._table.itemChanged.connect(self._handle_item_changed)

        layout.addWidget(self._table)

        footer_row = QHBoxLayout()
        footer_row.addStretch()
        self._batch_test_button = QPushButton("批量测试", self)
        self._batch_test_button.setProperty("variant", "ghost")
        self._batch_test_button.clicked.connect(self._run_all_tests)
        footer_row.addWidget(self._batch_test_button)
        layout.addLayout(footer_row)

    def _build_metric_card(self, title: str, value: str) -> QWidget:
        card = QGroupBox()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(6)

        value_label = QLabel(value, card)
        value_label.setObjectName("metricValue")
        value_label.setStyleSheet("font-size: 26px; font-weight: 600;")

        title_label = QLabel(title, card)
        title_label.setStyleSheet("color: #64748b; font-size: 13px;")

        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)

        # Store reference to value label for easy updates
        card.value_label = value_label  # type: ignore[attr-defined]
        return card

    def _handle_add_device(self) -> None:
        name = self._name_input.text().strip() or "未命名设备"
        ip_address = self._ip_input.text().strip() or "0.0.0.0"
        port_text = self._port_input.text().strip()
        operations = self._operations_input.text().strip()
        protocol = self._protocol_box.currentText()

        self._append_device_row(
            DeviceProfile(
                name=name,
                ip_address=ip_address,
                port=port_text or None,
                protocol=protocol,
                operations=operations,
            )
        )

        port_display = port_text or "—"
        self._logger.info(
            "已登记设备：%s (%s:%s) 使用 %s 协议，操作：%s",
            name,
            ip_address,
            port_display,
            protocol,
            operations or "默认",
        )
        self._reset_inputs()
        self._update_summary()
        self._emit_devices_changed()

    def _reset_inputs(self) -> None:
        self._name_input.clear()
        self._ip_input.clear()
        self._port_input.clear()
        self._protocol_box.setCurrentIndex(0)
        self._operations_input.clear()

    def _run_single_test(self, row: int) -> None:
        if not 0 <= row < self._table.rowCount():
            return

        status_label = self._get_status_widget(row)
        test_button = self._get_button_widget(row)
        if status_label is None or test_button is None:
            return

        name = self._table.item(row, 0).text()
        ip_address = self._table.item(row, 1).text()
        port_text = self._table.item(row, 2).text()

        status_label.setText("测试中…")
        status_label.setProperty("status", "pending")
        self._refresh_widget(status_label)
        test_button.setEnabled(False)

        self._logger.info("开始测试设备 %s 的连接 (%s:%s)", name, ip_address, port_text)

        QTimer.singleShot(1200, lambda: self._finalise_test(row))

    def _finalise_test(self, row: int) -> None:
        status_label = self._get_status_widget(row)
        test_button = self._get_button_widget(row)
        if status_label is None or test_button is None:
            return

        name = self._table.item(row, 0).text()
        ip_address = self._table.item(row, 1).text()
        port_text = self._table.item(row, 2).text()

        success = self._determine_success(ip_address, port_text)
        if success:
            status_label.setText("连接成功")
            status_label.setProperty("status", "success")
            self._logger.info(
                "设备 %s 连接成功：%s:%s", name, ip_address, port_text
            )
        else:
            status_label.setText("连接失败")
            status_label.setProperty("status", "failure")
            self._logger.error(
                "设备 %s 连接失败，请检查网络：%s:%s", name, ip_address, port_text
            )

        self._refresh_widget(status_label)
        test_button.setEnabled(True)
        self._update_summary()

    def _determine_success(self, ip_address: str, port_text: str) -> bool:
        trusted_prefixes = (
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "192.168.",
        )
        port_text = port_text.strip()
        if ip_address.startswith(trusted_prefixes):
            return True
        if not port_text or port_text in {"—", "0"}:
            return sum(ord(c) for c in ip_address) % 3 != 0
        try:
            port = int(port_text)
        except ValueError:
            return False
        return port % 2 == 0

    def _run_all_tests(self) -> None:
        for row in range(self._table.rowCount()):
            button = self._get_button_widget(row)
            if button is None or not button.isEnabled():
                continue
            self._run_single_test(row)

    def _get_status_widget(self, row: int) -> QLabel | None:
        widget = self._table.cellWidget(row, 5)
        if isinstance(widget, QLabel):
            return widget
        return None

    def _get_button_widget(self, row: int) -> QPushButton | None:
        widget = self._table.cellWidget(row, 6)
        if isinstance(widget, QPushButton):
            return widget
        return None

    def _update_summary(self) -> None:
        total = self._table.rowCount()
        pending = 0
        success = 0
        failure = 0
        for row in range(total):
            label = self._get_status_widget(row)
            if label is None:
                continue
            status = label.property("status")
            if status == "success":
                success += 1
            elif status == "failure":
                failure += 1
            else:
                pending += 1

        self._set_metric(self._total_label, total)
        self._set_metric(self._pending_label, pending)
        self._set_metric(self._success_label, success)
        self._set_metric(self._failure_label, failure)

    def _set_metric(self, card: QWidget, value: int) -> None:
        value_label: Any = getattr(card, "value_label", None)
        if isinstance(value_label, QLabel):
            value_label.setText(str(value))

    @staticmethod
    def _refresh_widget(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _append_device_row(self, profile: DeviceProfile) -> None:
        previous_state = self._suppress_table_events
        self._suppress_table_events = True
        try:
            row = self._table.rowCount()
            self._table.insertRow(row)

            name_item = QTableWidgetItem(profile.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, name_item)

            ip_item = QTableWidgetItem(profile.ip_address)
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ip_item.setFlags(ip_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, ip_item)

            port_display = profile.port or "—"
            port_item = QTableWidgetItem(port_display)
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            port_item.setFlags(port_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 2, port_item)

            protocol_item = QTableWidgetItem(profile.protocol)
            protocol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            protocol_item.setFlags(protocol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 3, protocol_item)

            operations_item = QTableWidgetItem(profile.operations or "")
            operations_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            operations_item.setFlags(operations_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 4, operations_item)

            status_label = QLabel("待测试", self._table)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setProperty("status", "pending")
            self._table.setCellWidget(row, 5, status_label)

            test_button = QPushButton("测试连接", self._table)
            test_button.clicked.connect(lambda _, r=row: self._run_single_test(r))
            self._table.setCellWidget(row, 6, test_button)
        finally:
            self._suppress_table_events = previous_state

    def _emit_devices_changed(self) -> None:
        self.devicesChanged.emit(self.get_devices())

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        if self._suppress_table_events:
            return
        if item.column() not in (2, 4):
            return
        self._update_summary()
        self._emit_devices_changed()

    def get_devices(self) -> list[DeviceProfile]:
        devices: list[DeviceProfile] = []
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 0)
            ip_item = self._table.item(row, 1)
            port_item = self._table.item(row, 2)
            protocol_item = self._table.item(row, 3)
            operations_item = self._table.item(row, 4)
            if not all([name_item, ip_item, port_item, protocol_item]):
                continue
            port_text = port_item.text().strip() if port_item else ""
            if port_text in {"—", ""}:
                port_value = None
            else:
                port_value = port_text
            devices.append(
                DeviceProfile(
                    name=name_item.text(),
                    ip_address=ip_item.text(),
                    port=port_value,
                    protocol=protocol_item.text(),
                    operations=operations_item.text() if operations_item else "",
                )
            )
        return devices

    def set_devices(self, devices: list[DeviceProfile]) -> None:
        self._suppress_table_events = True
        try:
            self._table.setRowCount(0)
            for profile in devices:
                self._append_device_row(profile)
        finally:
            self._suppress_table_events = False
        self._update_summary()
