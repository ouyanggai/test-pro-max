"""步骤4：节点配置 - 表格 + 一键指定/随机"""
from __future__ import annotations

import asyncio
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton,
    QHeaderView, QFrame,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX
from workflow_test_desktop.api.client import ApiClient
from workflow_test_desktop.ui.error_bus import ErrorBus

logger = logging.getLogger(__name__)


ASSIGNMENT_MODES = [
    ("手动指定", "manual"),
    ("一键指定", "one_click"),
    ("随机", "random"),
    ("范围随机", "range_random"),
    ("岗位随机", "position_random"),
    ("部门随机", "department_random"),
]


class StepNodes(QWidget):
    """节点配置步骤"""

    nodes_configured = Signal(list)

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._nodes: list[dict] = []
        self._setup_ui()
        self._load_nodes_from_flow()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("配置审核节点")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        for label_text, action in [
            ("一键指定", self._on_one_click_assign),
            ("一键随机", self._on_one_click_random),
            ("重置全部", self._on_reset_all),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.setProperty("theme", "secondary")
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 节点表格
        self._table = QTableWidget()
        self._table.setFont(FONT_FAMILY)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["#", "节点名称", "类型", "审核方式", "指派模式", "状态"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 150)
        self._table.setColumnWidth(5, 120)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        # 验证提示
        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("color: #EF4444; font-size: 13px; padding: 8px 12px;")
        self._hint_label.setVisible(False)
        self._hint_label.setFont(FONT_FAMILY)
        layout.addWidget(self._hint_label)

    # ─── 加载节点 ───────────────────────────────────────────────

    def _load_nodes_from_flow(self):
        """从 shared_data 或 API 加载节点列表"""
        flow_id = self._shared_data.get("flow_id")
        if not flow_id:
            return

        # 优先从缓存的 flow detail 读取
        flow_detail = self._shared_data.get("_flow_detail")
        if flow_detail:
            nodes = flow_detail.get("flowNodeList", [])
            if nodes:
                self._set_nodes(nodes)
                return

        # 否则从 API 加载
        async def _fetch():
            gateway = self._config.get("GATEWAY_URL", "")
            if not gateway:
                return
            try:
                async with ApiClient(gateway) as client:
                    resp = await client.post(
                        "/web/flowTemplateApi/detail",
                        json={"id": flow_id},
                    )
                    data = resp.json()
                    if data.get("code") == 0:
                        nodes = data.get("data", {}).get("flowNodeList", [])
                        self._shared_data["_flow_detail"] = data.get("data", {})
                        self._set_nodes(nodes)
                    else:
                        ErrorBus().emit(
                            "加载节点失败",
                            data.get("message", "未知错误"),
                            source="StepNodes",
                        )
            except Exception as e:
                ErrorBus().emit(
                    "加载节点失败",
                    str(e),
                    source="StepNodes",
                )

        def _run():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            asyncio.ensure_future(_fetch(), loop=loop)

        QTimer.singleShot(50, _run)

    def _set_nodes(self, nodes: list):
        """在主线程设置节点列表"""
        self._nodes = nodes
        self._table.setRowCount(len(nodes))

        for i, node in enumerate(nodes):
            # 序号
            seq_item = QTableWidgetItem(str(i + 1))
            seq_item.setFlags(Qt.ItemIsEnabled)
            seq_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 0, seq_item)

            # 节点名称（携带完整数据）
            name_item = QTableWidgetItem(node.get("nodeName", ""))
            name_item.setData(Qt.UserRole, node)
            self._table.setItem(i, 1, name_item)

            # 节点类型
            type_item = QTableWidgetItem(node.get("nodeType", ""))
            type_item.setFlags(Qt.ItemIsEnabled)
            self._table.setItem(i, 2, type_item)

            # 审核方式
            audit_way = node.get("auditWay", "")
            way_display = {"SCRAMBLE": "竞签", "COUNTERSIGN": "会签"}.get(audit_way, audit_way)
            way_item = QTableWidgetItem(way_display or "--")
            way_item.setFlags(Qt.ItemIsEnabled)
            self._table.setItem(i, 3, way_item)

            # 指派模式下拉
            combo = QComboBox()
            combo.setFont(FONT_FAMILY)
            for label, value in ASSIGNMENT_MODES:
                combo.addItem(label, value)
            # 根据 auditType 预选
            audit_type = node.get("auditType", "").lower()
            default_mode = "manual"
            if audit_type == "assign":
                default_mode = "one_click"
            elif audit_type in ("position", "role", "department"):
                default_mode = "position_random"
            elif audit_type == "initiator":
                default_mode = "random"
            for idx in range(combo.count()):
                if combo.itemData(idx) == default_mode:
                    combo.setCurrentIndex(idx)
                    break
            combo.currentIndexChanged.connect(self._on_mode_changed)
            self._table.setCellWidget(i, 4, combo)

            # 状态
            status_item = QTableWidgetItem("⚠ 待配置")
            status_item.setForeground(Qt.darkYellow)
            self._table.setItem(i, 5, status_item)

        logger.info("[StepNodes] 加载了 %d 个节点", len(nodes))

    # ─── 导出 ───────────────────────────────────────────────

    def get_assignment_rules(self) -> list[dict]:
        """导出指派规则，供 ExecutionController 使用"""
        rules = []
        for i in range(self._table.rowCount()):
            node = self._table.item(i, 1).data(Qt.UserRole)
            combo = self._table.cellWidget(i, 4)
            mode = combo.currentData()
            node_users = node.get("flowNodeUserList", [])
            rules.append({
                "node_id": node.get("nodeId", ""),
                "node_name": node.get("nodeName", ""),
                "mode": mode,
                "preassigned_users": [
                    {"userId": u.get("userId", ""), "userName": u.get("userName", "")}
                    for u in node_users
                ],
            })
        return rules

    # ─── 操作 ───────────────────────────────────────────────

    def _on_mode_changed(self):
        """实时更新状态列"""
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 4)
            mode = combo.currentData()
            status_item = self._table.item(i, 5)
            if mode == "manual":
                status_item.setText("⚠ 待指定")
                status_item.setForeground(Qt.darkYellow)
            elif mode == "one_click":
                status_item.setText("✓ 已指定")
                status_item.setForeground(Qt.darkGreen)
            elif mode == "random":
                status_item.setText("🎲 随机")
                status_item.setForeground(Qt.darkBlue)
            else:
                status_item.setText("✓ 已设置")
                status_item.setForeground(Qt.darkGreen)

    def _on_one_click_assign(self):
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 4)
            for idx in range(combo.count()):
                if combo.itemData(idx) == "one_click":
                    combo.setCurrentIndex(idx)
                    break

    def _on_one_click_random(self):
        import random
        modes_random = ["random", "range_random", "position_random", "department_random"]
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 4)
            mode = random.choice(modes_random)
            for idx in range(combo.count()):
                if combo.itemData(idx) == mode:
                    combo.setCurrentIndex(idx)
                    break

    def _on_reset_all(self):
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 4)
            combo.setCurrentIndex(0)
            self._table.item(i, 5).setText("⚠ 待配置")
            self._table.item(i, 5).setForeground(Qt.darkYellow)

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """验证：所有节点必须已配置（非 manual 或已指定）"""
        self._hint_label.setVisible(False)
        unconfigured = []
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 4)
            mode = combo.currentData()
            node_name = self._table.item(i, 1).text()
            if mode == "manual":
                unconfigured.append(node_name)

        if unconfigured:
            names = "、".join(unconfigured[:3])
            if len(unconfigured) > 3:
                names += f" 等{len(unconfigured)}个"
            self._hint_label.setText(f"⚠ 请配置以下节点：{names}")
            self._hint_label.setVisible(True)
            self._shake_widget(self._hint_label)
            return False, f"请配置节点：{names}"
        return True, ""

    def _shake_widget(self, widget):
        """抖动动画"""
        anim = QPropertyAnimation(widget, b"pos")
        orig_pos = widget.pos()
        anim.setDuration(400)
        anim.setKeyValueAt(0, orig_pos)
        anim.setKeyValueAt(0.25, orig_pos + QPoint(10, 0))
        anim.setKeyValueAt(0.5, orig_pos + QPoint(-10, 0))
        anim.setKeyValueAt(0.75, orig_pos + QPoint(10, 0))
        anim.setKeyValueAt(1, orig_pos)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start()
