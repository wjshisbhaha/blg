"""Configuration panel widget."""

from __future__ import annotations

from dataclasses import asdict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig, DeviceProfile


class ConfigurationPanel(QWidget):
    """Widget that allows editing of the application configuration."""

    configChanged = pyqtSignal(AppConfig)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._baseline = AppConfig()
        self._devices: list[DeviceProfile] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        general_box = QGroupBox("General Settings", self)
        general_form = QFormLayout(general_box)
        general_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.environment_box = QComboBox(general_box)
        self.environment_box.addItems(["Production", "Staging", "Development"])
        general_form.addRow("Environment:", self.environment_box)

        self.api_endpoint_edit = QLineEdit(general_box)
        self.api_endpoint_edit.setPlaceholderText("https://api.example.com")
        general_form.addRow("API Endpoint:", self.api_endpoint_edit)

        self.refresh_spin = QSpinBox(general_box)
        self.refresh_spin.setRange(1, 1440)
        self.refresh_spin.setSuffix(" min")
        general_form.addRow("Refresh Interval:", self.refresh_spin)

        self.notifications_check = QCheckBox("Enable desktop notifications", general_box)
        general_form.addRow("Notifications:", self.notifications_check)

        self.log_level_box = QComboBox(general_box)
        self.log_level_box.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        general_form.addRow("Log Level:", self.log_level_box)

        general_box.setLayout(general_form)
        layout.addWidget(general_box)

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("summaryLabel")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.apply_button = QPushButton("Apply", self)
        self.reset_button = QPushButton("Reset", self)
        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.apply_button)
        layout.addLayout(button_row)

        self.apply_button.clicked.connect(self._emit_config)
        self.reset_button.clicked.connect(self._reset_to_baseline)

        self.environment_box.currentIndexChanged.connect(self._update_summary)
        self.api_endpoint_edit.textChanged.connect(self._update_summary)
        self.refresh_spin.valueChanged.connect(self._update_summary)
        self.notifications_check.stateChanged.connect(self._update_summary)
        self.log_level_box.currentIndexChanged.connect(self._update_summary)

        self._update_summary()

    def set_config(self, config: AppConfig, *, remember: bool = True) -> None:
        if remember:
            self._baseline = AppConfig.from_dict(config.to_dict())
        self._devices = [DeviceProfile.from_dict(d.to_dict()) for d in config.devices]
        self.environment_box.setCurrentText(config.environment)
        self.api_endpoint_edit.setText(config.api_endpoint)
        self.refresh_spin.setValue(config.refresh_interval)
        self.notifications_check.setChecked(config.enable_notifications)
        self.log_level_box.setCurrentText(config.log_level)
        self._update_summary()

    def get_config(self) -> AppConfig:
        return AppConfig(
            environment=self.environment_box.currentText(),
            api_endpoint=self.api_endpoint_edit.text(),
            refresh_interval=self.refresh_spin.value(),
            enable_notifications=self.notifications_check.isChecked(),
            log_level=self.log_level_box.currentText(),
            devices=[DeviceProfile.from_dict(d.to_dict()) for d in self._devices],
        )

    def set_devices(self, devices: list[DeviceProfile]) -> None:
        self._devices = [DeviceProfile.from_dict(d.to_dict()) for d in devices]
        self._update_summary()

    def _emit_config(self) -> None:
        config = self.get_config()
        self.configChanged.emit(config)
        self._update_summary()

    def _update_summary(self, *_) -> None:
        config = self.get_config()
        parts = []
        for key, value in asdict(config).items():
            if isinstance(value, bool):
                display = "Enabled" if value else "Disabled"
            elif key == "devices" and isinstance(value, list):
                display = f"{len(value)} configured"
            elif isinstance(value, (list, dict)):
                display = str(value)
            else:
                display = value
            parts.append(f"{key.replace('_', ' ').title()}: {display}")
        self.summary_label.setText(" \u2022 ".join(parts))

    def _reset_to_baseline(self) -> None:
        self.set_config(self._baseline, remember=False)
