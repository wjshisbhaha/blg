# Business Logic Gateway Desktop Client

A PyQt6-based desktop shell that separates UI design, configuration management, and execution logic. The application features a configuration editor and real-time log viewer.

## Project Layout

```
app/
├── config.py                # Configuration dataclass and persistence helpers
├── controllers/
│   └── main_controller.py   # Signal orchestration and business workflow hooks
├── logging_utils.py         # Rotating file logging and Qt log handler
└── ui/
    ├── config_panel.py      # Standalone configuration editor widget
    ├── log_panel.py         # Log viewer widget
    └── main_window.py       # Main window assembly and styling
main.py                      # Application entry point
```

## Getting Started

1. Install dependencies:
   ```bash
   pip install PyQt6
   ```
2. Launch the application:
   ```bash
   python main.py
   ```

Configuration is stored in `~/.blg_app/settings.json` by default and can be exported/imported using the toolbar actions. Logs are streamed to the interface and rotated log file `application.log` in the same directory.
