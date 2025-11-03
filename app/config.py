from __future__ import annotations

"""Application configuration models and helpers."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import json


CONFIG_FILE_NAME = "settings.json"
CONFIG_DIR_NAME = ".blg_app"


@dataclass
class DeviceProfile:
    """Persisted description of a device used for connectivity tests."""

    name: str
    ip_address: str
    port: str | None = None
    protocol: str = "Modbus TCP"
    operations: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "port": self.port,
            "protocol": self.protocol,
            "operations": self.operations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceProfile":
        return cls(
            name=str(data.get("name", "未命名设备")),
            ip_address=str(data.get("ip_address", "0.0.0.0")),
            port=(
                str(data.get("port"))
                if data.get("port") not in (None, "", "—")
                else None
            ),
            protocol=str(data.get("protocol", "Modbus TCP")),
            operations=str(data.get("operations", "")),
        )


@dataclass
class PiControlBinding:
    """Represents a single axis/button mapping for the Pi controller."""

    axis: str
    gpio_pin: str
    command: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis": self.axis,
            "gpio_pin": self.gpio_pin,
            "command": self.command,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PiControlBinding":
        return cls(
            axis=str(data.get("axis", "X+")),
            gpio_pin=str(data.get("gpio_pin", "17")),
            command=str(data.get("command", "")),
            description=str(data.get("description", "")),
        )


def default_pi_bindings() -> list[PiControlBinding]:
    """Return Ele.me-styled defaults for the Pi six-axis controller."""

    defaults = [
        ("X+", "17", "move_x_positive"),
        ("X-", "27", "move_x_negative"),
        ("Y+", "22", "move_y_positive"),
        ("Y-", "23", "move_y_negative"),
        ("Z+", "24", "move_z_positive"),
        ("Z-", "25", "move_z_negative"),
    ]
    return [
        PiControlBinding(axis=axis, gpio_pin=gpio, command=command) for axis, gpio, command in defaults
    ]


@dataclass
class AppConfig:
    """Configuration container for the desktop client."""

    environment: str = "Production"
    api_endpoint: str = "https://api.example.com"
    refresh_interval: int = 5
    enable_notifications: bool = True
    log_level: str = "INFO"
    devices: list[DeviceProfile] = field(default_factory=list)
    pi_controls: list[PiControlBinding] = field(default_factory=default_pi_bindings)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        raw_notifications = data.get("enable_notifications", True)
        if isinstance(raw_notifications, str):
            enable_notifications = raw_notifications.strip().lower() in {"1", "true", "yes", "on"}
        else:
            enable_notifications = bool(raw_notifications)

        devices_data = data.get("devices", [])
        devices: list[DeviceProfile] = []
        if isinstance(devices_data, list):
            for entry in devices_data:
                if isinstance(entry, dict):
                    devices.append(DeviceProfile.from_dict(entry))

        controls_data = data.get("pi_controls")
        pi_controls: list[PiControlBinding]
        if isinstance(controls_data, list):
            pi_controls = []
            for entry in controls_data:
                if isinstance(entry, dict):
                    pi_controls.append(PiControlBinding.from_dict(entry))
        else:
            pi_controls = default_pi_bindings()

        return cls(
            environment=data.get("environment", "Production"),
            api_endpoint=data.get("api_endpoint", "https://api.example.com"),
            refresh_interval=int(data.get("refresh_interval", 5)),
            enable_notifications=enable_notifications,
            log_level=str(data.get("log_level", "INFO")).upper(),
            devices=devices,
            pi_controls=pi_controls,
        )


def get_default_config_path() -> Path:
    """Return the default configuration file path."""

    home = Path.home()
    config_dir = home / CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / CONFIG_FILE_NAME


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from JSON file."""

    file_path = path or get_default_config_path()
    if not file_path.exists():
        return AppConfig()

    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Persist configuration to disk."""

    file_path = path or get_default_config_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(config.to_dict(), fh, indent=2, ensure_ascii=False)
