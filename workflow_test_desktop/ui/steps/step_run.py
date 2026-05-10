"""步骤5：运行监控"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QTreeWidget, QTreeWidgetItem, QPushButton,
)
from PySide6.QtCore import Qt, QTimer, Signal
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


class StepRun(QWidget):
    """运行监控步骤"""
    execution_completed = Signal(dict)

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._is_running = False
        self._timer = None
        self._start_time = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        # 状态栏
        status_bar = QFrame()
        status_bar.setStyleSheet(
            f"background: var(--bg-card); border-radius: {RADIUS_CARD}; padding: 12px;"
        )
        sl = QHBoxLayout(status_bar)
        self._progress_bar = QProgressBar()
        self._progress_bar.setFont(FONT_FAMILY)
        sl.addWidget(self._progress_bar, 1)
        self._elapsed_label = QLabel("已用时间: 0s")
        self._elapsed_label.setFont(FONT_FAMILY)
        sl.addWidget(self._elapsed_label)
        self._node_count_label = QLabel("节点: 0/0")
        self._node_count_label.setFont(FONT_FAMILY)
        sl.addWidget(self._node_count_label)
        btn_pause = QPushButton("暂停")
        btn_pause.setFont(FONT_FAMILY)
        btn_pause.clicked.connect(self._on_pause)
        sl.addWidget(btn_pause)
        btn_stop = QPushButton("停止")
        btn_stop.setFont(FONT_FAMILY)
        btn_stop.setStyleSheet("QPushButton { background: #EF4444; color: white; }")
        btn_stop.clicked.connect(self._on_stop)
        sl.addWidget(btn_stop)
        layout.addWidget(status_bar)

        # 执行树
        self._branch_tree = QTreeWidget()
        self._branch_tree.setFont(FONT_FAMILY)
        self._branch_tree.setHeaderLabels(["项目", "状态", "用时"])
        layout.addWidget(self._branch_tree, 1)

        # 控制栏
        controls = QHBoxLayout()
        controls.addStretch()
        self._btn_start = QPushButton("▶ 开始运行")
        self._btn_start.setFont(FONT_FAMILY)
        self._btn_start.clicked.connect(self._on_start)
        controls.addWidget(self._btn_start)
        layout.addLayout(controls)

    def _on_start(self):
        if self._is_running:
            return
        self._is_running = True
        self._btn_start.setEnabled(False)
        self._start_time = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._timer.start(1000)

    def _update_elapsed(self):
        self._elapsed_label.setText(f"已用时间: {self._start_time}s")
        self._start_time += 1

    def _on_pause(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()
        elif self._timer:
            self._timer.start()

    def _on_stop(self):
        self._is_running = False
        if self._timer:
            self._timer.stop()
        self._btn_start.setEnabled(True)

    def set_result(self, result: dict):
        """ExecutionController 执行完成后调用"""
        self._is_running = False
        if self._timer:
            self._timer.stop()
        self._btn_start.setEnabled(True)

        all_completed = result.get("all_completed", False)
        status_text = "✅ 全部完成" if all_completed else "❌ 有分支失败"
        self._node_count_label.setText(status_text)

        self._shared_data["last_run_result"] = result
        self.execution_completed.emit(result)
