"""步骤4：节点配置"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QHeaderView,
)
from PySide6.QtCore import Signal, Qt
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


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
        self._nodes = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        title = QLabel("配置审核节点")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        for label_text, action in [
            ("一键指定", self._on_one_click_assign),
            ("一键随机", self._on_one_click_random),
            ("重置全部", self._on_reset_all),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setFont(FONT_FAMILY)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["#", "节点名称", "类型", "指派方式", "结果"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 150)
        self._table.setColumnWidth(4, 150)
        layout.addWidget(self._table, 1)

        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("color: #EF4444;")
        self._hint_label.setFont(FONT_FAMILY)
        layout.addWidget(self._hint_label)

    def set_nodes(self, nodes: list):
        """从 StepFlow 选择流程并解析后调用"""
        self._nodes = nodes
        self._table.setRowCount(len(nodes))
        for i, node in enumerate(nodes):
            self._table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table.item(i, 0).setFlags(Qt.ItemIsEnabled)

            name_item = QTableWidgetItem(node.get("node_name", ""))
            name_item.setData(Qt.UserRole, node)
            self._table.setItem(i, 1, name_item)

            type_item = QTableWidgetItem(node.get("node_type", ""))
            type_item.setFlags(Qt.ItemIsEnabled)
            self._table.setItem(i, 2, type_item)

            combo = QComboBox()
            combo.setFont(FONT_FAMILY)
            for label, value in ASSIGNMENT_MODES:
                combo.addItem(label, value)
            combo.currentIndexChanged.connect(self._on_mode_changed)
            self._table.setCellWidget(i, 3, combo)

            result_item = QTableWidgetItem("⚠ 待配置")
            result_item.setForeground(Qt.red)
            self._table.setItem(i, 4, result_item)

    def get_assignment_rules(self) -> list[dict]:
        """导出指派规则，供 ExecutionController 使用"""
        rules = []
        for i in range(self._table.rowCount()):
            node = self._table.item(i, 1).data(Qt.UserRole)
            combo = self._table.cellWidget(i, 3)
            mode = combo.currentData()
            rules.append({
                "node_id": node.get("node_id", ""),
                "node_name": node.get("node_name", ""),
                "mode": mode,
            })
        return rules

    def _on_mode_changed(self):
        pass  # 实时校验

    def _on_one_click_assign(self):
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 3)
            for idx in range(combo.count()):
                if combo.itemData(idx) == "one_click":
                    combo.setCurrentIndex(idx)
                    self._table.item(i, 4).setText("✓ 已指定")

    def _on_one_click_random(self):
        for i in range(self._table.rowCount()):
            combo = self._table.cellWidget(i, 3)
            for idx in range(combo.count()):
                if combo.itemData(idx) == "random":
                    combo.setCurrentIndex(idx)
                    self._table.item(i, 4).setText("✓ 已随机")

    def _on_reset_all(self):
        for i in range(self._table.rowCount()):
            self._table.cellWidget(i, 3).setCurrentIndex(0)
            self._table.item(i, 4).setText("⚠ 待配置")
