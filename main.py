"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.ui.main_window import MainWindow


def main(config_path: Path | None = None) -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    MainController(window, config_path=config_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
