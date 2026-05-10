"""日志查看器弹窗：实时展示日志内容，支持级别过滤"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QComboBox, QPushButton, QLabel, QLineEdit,
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

from workflow_test_desktop.core.logging_config import get_log_dir, get_log_file_path
from workflow_test_desktop.config.themes import FONT_FAMILY


# 级别颜色映射
LEVEL_COLORS = {
    "ERROR": "#EF4444",
    "WARNING": "#F59E0B",
    "INFO": "#10B981",
    "DEBUG": "#6B7280",
}


class LogViewerDialog(QDialog):
    """日志查看器弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_file = get_log_file_path()
        self._last_size = 0
        self._filter_level = "全部"
        self._filter_text = ""
        self._setup_ui()
        self._load_initial_logs()
        self._start_watch()

    def _setup_ui(self):
        self.setWindowTitle("日志查看器")
        self.resize(900, 500)
        self.setMinimumSize(600, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("级别:"))
        self._level_combo = QComboBox()
        self._level_combo.addItems(["全部", "ERROR", "WARNING", "INFO", "DEBUG"])
        self._level_combo.setFont(FONT_FAMILY)
        self._level_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._level_combo)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("搜索日志内容...")
        self._filter_input.setFont(FONT_FAMILY)
        self._filter_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._filter_input, 1)

        btn_open_dir = QPushButton("打开日志目录")
        btn_open_dir.setFont(FONT_FAMILY)
        btn_open_dir.clicked.connect(self._open_log_dir)
        toolbar.addWidget(btn_open_dir)

        btn_clear = QPushButton("清空")
        btn_clear.setFont(FONT_FAMILY)
        btn_clear.clicked.connect(self._clear_display)
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # 日志显示区
        self._log_display = QTextEdit()
        self._log_display.setFont(FONT_FAMILY)
        self._log_display.setReadOnly(True)
        self._log_display.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._log_display, 1)

        # 底部状态栏
        status_bar = QHBoxLayout()
        self._status_label = QLabel(f"日志文件: {self._log_file.name}")
        self._status_label.setFont(FONT_FAMILY)
        status_bar.addWidget(self._status_label)
        status_bar.addStretch()

        btn_close = QPushButton("关闭")
        btn_close.setFont(FONT_FAMILY)
        btn_close.clicked.connect(self.accept)
        status_bar.addWidget(btn_close)
        layout.addLayout(status_bar)

    def _load_initial_logs(self):
        """加载已有日志内容"""
        if self._log_file.exists():
            self._last_size = self._log_file.stat().st_size
            self._append_logs_from_file(0)

    def _start_watch(self):
        """每 2 秒检查日志文件更新"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_new_logs)
        self._timer.start(2000)

    def _check_new_logs(self):
        if not self._log_file.exists():
            return
        current_size = self._log_file.stat().st_size
        if current_size > self._last_size:
            self._append_logs_from_file(self._last_size)
            self._last_size = current_size
        elif current_size < self._last_size:
            # 日志轮转，重新从头读
            self._clear_display()
            self._last_size = 0
            self._append_logs_from_file(0)
            self._last_size = current_size

    def _append_logs_from_file(self, start_pos: int):
        with open(self._log_file, "r", encoding="utf-8") as f:
            f.seek(start_pos)
            lines = f.readlines()
        for line in lines:
            self._append_line(line)

    def _append_line(self, line: str):
        """追加一行日志，按级别着色"""
        if not line.strip():
            return

        # 级别过滤
        if self._filter_level != "全部":
            if self._filter_level not in line:
                return

        # 文本过滤
        if self._filter_text and self._filter_text.lower() not in line.lower():
            return

        # 提取级别用于着色
        level = "INFO"
        for lvl in ["ERROR", "WARNING", "DEBUG"]:
            if f"[{lvl}]" in line:
                level = lvl
                break

        color = QColor(LEVEL_COLORS.get(level, "#6B7280"))

        cursor = self._log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.setCharFormat(fmt)
        cursor.insertText(line)
        self._log_display.setTextCursor(cursor)
        self._log_display.ensureCursorVisible()

    def _on_filter_changed(self):
        self._filter_level = self._level_combo.currentText()
        self._filter_text = self._filter_input.text()
        # 重新加载过滤后的日志
        self._clear_display()
        if self._log_file.exists():
            self._append_logs_from_file(0)

    def _clear_display(self):
        self._log_display.clear()

    def _open_log_dir(self):
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(log_dir)])
