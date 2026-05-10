"""步骤5：运行监控 - 进度条 + 计时器 + 树形状态"""
from __future__ import annotations

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QTreeWidget, QTreeWidgetItem, QPushButton,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX, LIGHT, build_card_style

logger = logging.getLogger(__name__)


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
        self._is_paused = False
        self._timer: QTimer | None = None
        self._elapsed_ms = 0
        self._total_nodes = 0
        self._completed_nodes = 0
        self._step_widgets: dict = {}  # tree item -> step data
        self._setup_ui()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("运行监控")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 状态栏卡片
        status_card = QFrame()
        status_card.setObjectName("card")
        status_card.setStyleSheet(
            "QFrame#card { background-color: #FFFFFF; border: 1px solid #E2E4E9; "
            "border-radius: 12px; padding: 16px; }"
        )
        sl = QVBoxLayout(status_card)
        sl.setSpacing(12)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setFont(FONT_FAMILY)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        sl.addWidget(self._progress_bar)

        # 状态行
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._elapsed_label = QLabel("已用时间: 0s")
        self._elapsed_label.setFont(FONT_FAMILY)
        stats_layout.addWidget(self._elapsed_label)

        self._node_count_label = QLabel("节点: 0/0")
        self._node_count_label.setFont(FONT_FAMILY)
        stats_layout.addWidget(self._node_count_label)

        self._status_label = QLabel("就绪")
        self._status_label.setFont(FONT_FAMILY)
        self._status_label.setStyleSheet("font-weight: 600; color: #6B7280;")
        stats_layout.addWidget(self._status_label)
        stats_layout.addStretch()

        sl.addLayout(stats_layout)

        # 控制按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self._btn_start = QPushButton("▶ 开始运行")
        self._btn_start.setFont(FONT_FAMILY)
        self._btn_start.setProperty("theme", "primary")
        self._btn_start.clicked.connect(self._on_start)
        btn_layout.addWidget(self._btn_start)

        self._btn_pause = QPushButton("⏸ 暂停")
        self._btn_pause.setFont(FONT_FAMILY)
        self._btn_pause.setEnabled(False)
        self._btn_pause.clicked.connect(self._on_pause)
        btn_layout.addWidget(self._btn_pause)

        self._btn_stop = QPushButton("⏹ 停止")
        self._btn_stop.setFont(FONT_FAMILY)
        self._btn_stop.setProperty("theme", "danger")
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)
        btn_layout.addWidget(self._btn_stop)

        sl.addLayout(btn_layout)
        layout.addWidget(status_card)

        # 执行树
        self._branch_tree = QTreeWidget()
        self._branch_tree.setFont(FONT_FAMILY)
        self._branch_tree.setHeaderLabels(["项目", "状态", "用时"])
        self._branch_tree.setAlternatingRowColors(True)
        self._branch_tree.setStyleSheet(
            "QTreeWidget { border: 1px solid #E2E4E9; border-radius: 8px; padding: 4px; }"
        )
        layout.addWidget(self._branch_tree, 1)

        # 初始化树（从 shared_data 读取节点信息）
        self._init_tree_from_shared()

    def _init_tree_from_shared(self):
        """从 shared_data 初始化执行树"""
        flow_detail = self._shared_data.get("_flow_detail", {})
        flow_name = self._shared_data.get("flow_name", "未知流程")
        branches = flow_detail.get("flowBranchList", [])
        nodes = flow_detail.get("flowNodeList", [])

        self._branch_tree.clear()
        self._step_widgets.clear()

        if not nodes:
            # 空状态
            root = QTreeWidgetItem(self._branch_tree, ["📋 暂无节点数据", "—", "—"])
            root.setExpanded(True)
            return

        self._total_nodes = len(nodes)
        self._completed_nodes = 0
        self._update_node_count()

        # 按分支分组
        branch_map: dict[str, list[dict]] = {}
        for node in nodes:
            branch_id = node.get("branchId", "_default")
            branch_map.setdefault(branch_id, []).append(node)

        # 显示分支和节点
        for branch_id, branch_nodes in branch_map.items():
            branch_name = next(
                (b.get("branchName", "") for b in branches if b.get("branchId") == branch_id),
                "默认分支",
            )
            branch_item = QTreeWidgetItem(self._branch_tree, [f"🌳 {branch_name}", "⏳ 待执行", "—"])
            branch_item.setExpanded(True)
            self._step_widgets[branch_item] = {"type": "branch", "branch_id": branch_id}

            for node in branch_nodes:
                node_name = node.get("nodeName", "未知节点")
                node_type = node.get("nodeType", "")
                node_item = QTreeWidgetItem(
                    branch_item,
                    [f"  📌 {node_name}", "⏳ 待执行", "—"],
                )
                node_item.setData(0, Qt.UserRole, node)
                self._step_widgets[node_item] = {
                    "type": "node",
                    "node": node,
                    "status": "pending",
                }

    # ─── 计时器 ───────────────────────────────────────────────

    def _start_timer(self):
        self._elapsed_ms = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._timer.start(1000)

    def _update_elapsed(self):
        if self._is_paused:
            return
        self._elapsed_ms += 1000
        seconds = self._elapsed_ms // 1000
        self._elapsed_label.setText(f"已用时间: {seconds}s")

    # ─── 控制 ───────────────────────────────────────────────

    def _on_start(self):
        if self._is_running:
            return
        self._is_running = True
        self._is_paused = False
        self._btn_start.setEnabled(False)
        self._btn_pause.setEnabled(True)
        self._btn_stop.setEnabled(True)
        self._status_label.setText("运行中")
        self._status_label.setStyleSheet("font-weight: 600; color: #10B981;")
        self._start_timer()
        logger.info("[StepRun] 开始执行")

    def _on_pause(self):
        if not self._is_running:
            return
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._btn_pause.setText("▶ 继续")
            self._status_label.setText("已暂停")
            self._status_label.setStyleSheet("font-weight: 600; color: #F59E0B;")
        else:
            self._btn_pause.setText("⏸ 暂停")
            self._status_label.setText("运行中")
            self._status_label.setStyleSheet("font-weight: 600; color: #10B981;")

    def _on_stop(self):
        self._is_running = False
        self._is_paused = False
        if self._timer:
            self._timer.stop()
        self._btn_start.setEnabled(True)
        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)
        self._btn_pause.setText("⏸ 暂停")
        self._status_label.setText("已停止")
        self._status_label.setStyleSheet("font-weight: 600; color: #EF4444;")
        self._progress_bar.setValue(0)
        logger.info("[StepRun] 执行停止")

    # ─── 结果设置 ───────────────────────────────────────────────

    def set_result(self, result: dict):
        """ExecutionController 执行完成后调用"""
        self._is_running = False
        self._is_paused = False
        if self._timer:
            self._timer.stop()

        self._btn_start.setEnabled(True)
        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)
        self._btn_pause.setText("⏸ 暂停")

        duration_ms = result.get("duration_ms", 0)
        all_completed = result.get("all_completed", False)
        self._elapsed_ms = duration_ms
        seconds = duration_ms // 1000
        self._elapsed_label.setText(f"已用时间: {seconds}s")

        if all_completed:
            self._status_label.setText("✅ 全部完成")
            self._status_label.setStyleSheet("font-weight: 600; color: #10B981;")
        else:
            self._status_label.setText("⚠ 有分支失败")
            self._status_label.setStyleSheet("font-weight: 600; color: #EF4444;")

        self._progress_bar.setValue(100)

        # 更新树
        completed_branches = result.get("completed_branches", [])
        failed_branches = result.get("failed_branches", [])
        node_results = result.get("node_results", {})

        for item, data in self._step_widgets.items():
            if data["type"] == "branch":
                branch_id = data["branch_id"]
                if branch_id in completed_branches:
                    item.setText(1, "✅ 完成")
                    item.setForeground(1, Qt.darkGreen)
                elif branch_id in failed_branches:
                    item.setText(1, "❌ 失败")
                    item.setForeground(1, Qt.darkRed)
            elif data["type"] == "node":
                node_id = data["node"].get("nodeId", "")
                node_result = node_results.get(node_id, {})
                status = node_result.get("status", "pending")
                if status == "completed":
                    item.setText(1, "✅ 完成")
                    item.setForeground(1, Qt.darkGreen)
                    elapsed = node_result.get("elapsed_ms", 0)
                    item.setText(2, f"{elapsed}ms")
                    self._completed_nodes += 1
                elif status == "failed":
                    item.setText(1, "❌ 失败")
                    item.setForeground(1, Qt.darkRed)
                self._update_node_count()

        self._shared_data["last_run_result"] = result
        self.execution_completed.emit(result)
        logger.info("[StepRun] 执行完成，结果: all_completed=%s", all_completed)

    def _update_node_count(self):
        self._node_count_label.setText(f"节点: {self._completed_nodes}/{self._total_nodes}")
        if self._total_nodes > 0:
            pct = int(self._completed_nodes / self._total_nodes * 100)
            self._progress_bar.setValue(pct)
        elif self._total_nodes == 0 and self._completed_nodes == 0:
            # 无节点数据时不更新进度条
            pass

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """运行步骤无需预验证，点击开始即运行"""
        return True, ""
