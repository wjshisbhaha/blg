#!/usr/bin/env python3
"""Unified HUD application with automatic testing and brightness analysis tabs."""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg

from brightness_analyzer import MainWindow as BrightnessAnalyzerWindow
from hud_client import (
    HudClient,
    export_results_excel,
    load_test_plan,
    run_test_plan,
)


APP_STYLE = """
QMainWindow, QWidget#AppRoot {
    background: #151A21;
}
QWidget {
    color: #D9E1EA;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2E3742;
    background: #151A21;
    top: -1px;
}
QTabBar::tab {
    background: #1B222B;
    color: #8F9CAA;
    border: 1px solid #2E3742;
    border-bottom: none;
    padding: 11px 26px;
    min-width: 100px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #252D37;
    color: #FFFFFF;
    border-top: 2px solid #4A95D1;
}
QTabBar::tab:hover:!selected {
    color: #D9E1EA;
    background: #202832;
}
#MainTitle {
    font-size: 24px;
    font-weight: 600;
    color: #F2F6FA;
}
#SubTitle {
    color: #7F8B99;
    font-size: 12px;
}
#AutoStatus {
    color: #43D17A;
    background: #17271F;
    border: 1px solid #285D3D;
    border-radius: 12px;
    padding: 5px 12px;
}
QPushButton {
    background: #252D37;
    border: 1px solid #36414E;
    border-radius: 5px;
    padding: 7px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background: #303A46;
    border-color: #4A95D1;
}
QPushButton:pressed {
    background: #1E252D;
}
QPushButton:disabled {
    color: #66717D;
    background: #1D242C;
    border-color: #2A333D;
}
#PrimaryButton {
    background: #2878B5;
    color: white;
    border: 1px solid #4A95D1;
    font-weight: 600;
    padding: 8px 22px;
}
#PrimaryButton:hover {
    background: #3288C8;
}
QLineEdit, QSpinBox, QTextEdit {
    background: #10151B;
    border: 1px solid #2E3742;
    border-radius: 5px;
    color: #E8EDF2;
    selection-background-color: #2878B5;
}
QLineEdit, QSpinBox {
    padding: 7px 9px;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #4A95D1;
}
QTextEdit {
    padding: 10px;
    font-family: "SFMono-Regular", "Consolas", monospace;
    font-size: 12px;
}
QGroupBox {
    background: #181E26;
    border: 1px solid #2E3742;
    border-radius: 7px;
    margin-top: 13px;
    padding: 14px 12px 12px 12px;
    font-weight: 600;
    color: #C9D2DD;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 7px;
}
QScrollArea {
    border: 1px solid #2A333D;
    background: #0F1318;
}
#InfoLabel {
    background: #10151B;
    border: 1px solid #2A333D;
    padding: 7px;
    color: #AEB9C6;
}
#ValueCard {
    background: #1B222B;
    border: 1px solid #303A46;
    border-radius: 6px;
}
#CardTitle { color: #8795A5; font-size: 12px; }
#CardValue { color: #FFFFFF; font-size: 21px; font-weight: 600; }
QCheckBox { spacing: 7px; }
"""


class SignalWriter:
    """File-like object that forwards printed output to a Qt signal."""

    def __init__(self, signal: pyqtSignal):
        self.signal = signal
        self.pending = ""

    def write(self, text: str) -> int:
        self.pending += text
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line:
                self.signal.emit(line)
        return len(text)

    def flush(self) -> None:
        if self.pending:
            self.signal.emit(self.pending)
            self.pending = ""


class AutoTestWorker(QObject):
    log = pyqtSignal(str)
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        host: str,
        port: int,
        plan_path: str,
        sparkle_source_dir: str,
        save_root: str,
        folder_name: str,
        excel_name: str,
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.plan_path = plan_path
        self.sparkle_source_dir = sparkle_source_dir
        self.save_root = save_root
        self.folder_name = folder_name
        self.excel_name = excel_name

    @pyqtSlot()
    def run(self) -> None:
        writer = SignalWriter(self.log)
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                plan = load_test_plan(self.plan_path)
                run_dir = (Path(self.save_root).expanduser() / self.folder_name).resolve()
                if run_dir.exists() and any(run_dir.iterdir()):
                    raise ValueError(f"测试文件夹已存在且不为空：{run_dir}")
                run_dir.mkdir(parents=True, exist_ok=True)
                output_path = run_dir / self.excel_name
                with HudClient(self.host, self.port, timeout=60.0, debug=True) as client:
                    results = run_test_plan(
                        client,
                        plan,
                        switch_delay=0.2,
                        sparkle_source_dir=self.sparkle_source_dir,
                        run_dir=str(run_dir),
                    )
                if any(result.command.split("/", 1)[0] in {"t24", "t6"} for result in results):
                    output = export_results_excel(results, str(output_path))
                    print(f"Excel saved: {output}")
                else:
                    output = output_path
                    print("No t24/t6 results; Excel was not generated")
            writer.flush()
            self.completed.emit(str(output))
        except Exception as exc:
            writer.flush()
            self.failed.emit(str(exc))


class AutoTestPage(QWidget):
    def __init__(self):
        super().__init__()
        self.thread: QThread | None = None
        self.worker: AutoTestWorker | None = None
        self._create_ui()

    def _create_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("HUD 自动测试")
        title.setObjectName("MainTitle")
        subtitle = QLabel("配置切换 · 自动测量 · 图片归档 · Excel报告")
        subtitle.setObjectName("SubTitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        self.status_label = QLabel("● 就绪")
        self.status_label.setObjectName("AutoStatus")
        header.addWidget(self.status_label)
        layout.addLayout(header)

        settings_group = QGroupBox("连接与输出设置")
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        self.host_edit = QLineEdit("127.0.0.1")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5555)

        project_dir = Path(__file__).resolve().parent
        self.plan_edit = QLineEdit(str(project_dir / "hud_test_config.py"))
        self.sparkle_source_edit = QLineEdit()
        self.sparkle_source_edit.setPlaceholderText("请选择HUD软件生成 Sparkle.jpg 的目录")
        self.save_root_edit = QLineEdit(str(project_dir / "测试结果"))
        self.folder_name_edit = QLineEdit("本次测试")
        self.excel_name_edit = QLineEdit("测试结果.xlsx")
        form.addRow("服务器IP", self.host_edit)
        form.addRow("端口", self.port_spin)
        form.addRow("测试配置", self._path_row(self.plan_edit, self._choose_plan))
        form.addRow(
            "Sparkle默认目录",
            self._path_row(self.sparkle_source_edit, self._choose_sparkle_source),
        )
        form.addRow("保存根目录", self._path_row(self.save_root_edit, self._choose_save_root))
        form.addRow("测试文件夹名称", self.folder_name_edit)
        form.addRow("Excel文件名称", self.excel_name_edit)
        settings_group.setLayout(form)

        config_group = QGroupBox("测试配置内容（可直接编辑）")
        config_layout = QVBoxLayout(config_group)
        config_toolbar = QHBoxLayout()
        config_hint = QLabel("配置格式：配置文件名对应一个命令列表")
        config_hint.setObjectName("SubTitle")
        self.reload_config_button = QPushButton("重新加载")
        self.save_config_button = QPushButton("保存配置")
        config_toolbar.addWidget(config_hint)
        config_toolbar.addStretch()
        config_toolbar.addWidget(self.reload_config_button)
        config_toolbar.addWidget(self.save_config_button)
        config_layout.addLayout(config_toolbar)
        self.config_edit = QTextEdit()
        self.config_edit.setPlaceholderText(
            'TEST_PLAN = [\n    ("11", ["t24", r"ssf-D:\\test\\11.bin", "t6"]),\n]'
        )
        self.config_edit.setMinimumHeight(170)
        config_layout.addWidget(self.config_edit)

        top_content = QHBoxLayout()
        top_content.setSpacing(12)
        top_content.addWidget(settings_group, 1)
        top_content.addWidget(config_group, 1)
        layout.addLayout(top_content, 1)

        controls = QHBoxLayout()
        self.start_button = QPushButton("开始自动测试")
        self.start_button.setObjectName("PrimaryButton")
        self.clear_button = QPushButton("清空日志")
        controls.addWidget(self.start_button)
        controls.addWidget(self.clear_button)
        controls.addStretch()
        layout.addLayout(controls)

        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("测试日志将在这里显示")
        log_layout.addWidget(self.log_edit)
        layout.addWidget(log_group, 1)

        self.start_button.clicked.connect(self.start_test)
        self.clear_button.clicked.connect(self.log_edit.clear)
        self.reload_config_button.clicked.connect(self._load_plan_content)
        self.save_config_button.clicked.connect(lambda: self._save_plan_content(True))
        self._load_plan_content()

    def _path_row(self, edit: QLineEdit, callback) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("浏览")
        button.clicked.connect(callback)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return widget

    def _choose_plan(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择测试配置", "", "Python (*.py)")
        if path:
            self.plan_edit.setText(path)
            self._load_plan_content()

    @pyqtSlot()
    def _load_plan_content(self) -> None:
        path = Path(self.plan_edit.text().strip())
        if not path.is_file():
            self.config_edit.clear()
            return
        try:
            self.config_edit.setPlainText(path.read_text(encoding="utf-8"))
            self.log_edit.append(f"已加载测试配置：{path}") if hasattr(self, "log_edit") else None
        except OSError as exc:
            QMessageBox.critical(self, "读取失败", str(exc))

    @pyqtSlot()
    def _save_plan_content(self, show_message: bool = True) -> bool:
        path = Path(self.plan_edit.text().strip())
        try:
            path.write_text(self.config_edit.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return False
        if show_message:
            QMessageBox.information(self, "保存成功", f"测试配置已保存\n{path}")
        return True

    def _choose_save_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择测试结果保存根目录")
        if path:
            self.save_root_edit.setText(path)

    def _choose_sparkle_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择Sparkle.jpg默认生成目录")
        if path:
            self.sparkle_source_edit.setText(path)

    @pyqtSlot()
    def start_test(self) -> None:
        plan_path = self.plan_edit.text().strip()
        sparkle_source = self.sparkle_source_edit.text().strip()
        save_root = self.save_root_edit.text().strip()
        folder_name = self.folder_name_edit.text().strip()
        excel_name = self.excel_name_edit.text().strip()
        if not Path(plan_path).is_file():
            QMessageBox.warning(self, "配置错误", "测试配置文件不存在")
            return
        if not sparkle_source or not Path(sparkle_source).is_dir():
            QMessageBox.warning(self, "配置错误", "请选择有效的Sparkle.jpg默认生成目录")
            return
        if not self._save_plan_content(show_message=False):
            return
        if not save_root or not folder_name or not excel_name:
            QMessageBox.warning(self, "配置错误", "保存根目录、测试文件夹名称和Excel名称不能为空")
            return
        if any(separator in folder_name for separator in ("/", "\\")):
            QMessageBox.warning(self, "配置错误", "测试文件夹名称不能包含路径分隔符")
            return
        if not excel_name.lower().endswith(".xlsx"):
            excel_name += ".xlsx"
            self.excel_name_edit.setText(excel_name)

        self.start_button.setEnabled(False)
        self.status_label.setText("● 测试中")
        self.status_label.setStyleSheet("color:#FFD54A; background:#2B2515; border-color:#6A5720;")
        self.log_edit.append("开始自动测试...")
        self.thread = QThread(self)
        self.worker = AutoTestWorker(
            self.host_edit.text().strip(),
            self.port_spin.value(),
            plan_path,
            sparkle_source,
            save_root,
            folder_name,
            excel_name,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.log_edit.append)
        self.worker.completed.connect(self._test_completed)
        self.worker.failed.connect(self._test_failed)
        self.worker.completed.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot(str)
    def _test_completed(self, output: str) -> None:
        self.start_button.setEnabled(True)
        self.status_label.setText("● 已完成")
        self.status_label.setStyleSheet("")
        self.log_edit.append(f"测试完成：{output}")
        QMessageBox.information(self, "测试完成", f"自动测试已完成\n{output}")
        self.thread = None
        self.worker = None

    @pyqtSlot(str)
    def _test_failed(self, message: str) -> None:
        self.start_button.setEnabled(True)
        self.status_label.setText("● 失败")
        self.status_label.setStyleSheet("color:#FF7B8B; background:#2B181D; border-color:#6A2B38;")
        self.log_edit.append(f"ERROR: {message}")
        QMessageBox.critical(self, "测试失败", message)
        self.thread = None
        self.worker = None


class HudApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HUD 自动测试与亮度分析系统")
        self.resize(1600, 980)
        self.setObjectName("AppRoot")
        self.setStyleSheet(APP_STYLE)

        tabs = QTabWidget()
        tabs.addTab(AutoTestPage(), "自动测试")

        # Reuse the supplied brightness analyzer UI inside the second tab.
        self.brightness_window = BrightnessAnalyzerWindow()
        brightness_page = self.brightness_window.takeCentralWidget()
        tabs.addTab(brightness_page, "亮度分析")
        self.setCentralWidget(tabs)


def main() -> int:
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)
    window = HudApplicationWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
