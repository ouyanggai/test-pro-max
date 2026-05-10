"""步骤6：报告查看"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTextEdit, QTreeWidget, QGridLayout,
)
from PySide6.QtCore import Signal
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


class StepReport(QWidget):
    """报告查看步骤"""
    save_as_plan = Signal()

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        title = QLabel("执行报告")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        for label_text, action in [
            ("导出 HTML", self._on_export_html),
            ("导出 JSON", self._on_export_json),
            ("另存为运行计划", self._on_save_as_plan),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        card = QFrame()
        card.setStyleSheet(
            f"background: var(--bg-card); border-radius: {RADIUS_CARD}; padding: 16px;"
        )
        gl = QGridLayout(card)
        gl.setSpacing(SPACE_MD)
        self._summary_labels = []
        for i, text in enumerate(["流程名: --", "状态: --", "分支数: --",
                                  "节点数: --", "用时: --", "发起人: --"]):
            lbl = QLabel(text)
            lbl.setFont(FONT_FAMILY)
            gl.addWidget(lbl, i // 3, i % 3)
            self._summary_labels.append(lbl)
        layout.addWidget(card)

        self._branch_tree = QTreeWidget()
        self._branch_tree.setFont(FONT_FAMILY)
        self._branch_tree.setHeaderLabels(["项目", "状态"])
        layout.addWidget(self._branch_tree, 1)

        self._session_log = QTextEdit()
        self._session_log.setFont(FONT_FAMILY)
        self._session_log.setReadOnly(True)
        self._session_log.setPlaceholderText("会话日志...")
        layout.addWidget(self._session_log, 1)

    def set_report_data(self, result: dict):
        """从 StepRun 执行完成后调用"""
        # 更新摘要
        summaries = [
            f"流程名: {result.get('flow_instance_id', '--')}",
            f"状态: {'完成' if result.get('all_completed') else '有失败'}",
            f"分支数: {len(result.get('completed_branches', []))}",
            f"节点数: --",
            f"用时: {result.get('duration_ms', 0) // 1000}s",
            f"发起人: {self._shared_data.get('starter_username', '--')}",
        ]
        for lbl, text in zip(self._summary_labels, summaries):
            lbl.setText(text)

        # 更新分支树
        self._branch_tree.clear()
        for branch_key in result.get("completed_branches", []):
            QTreeWidgetItem(self._branch_tree, [branch_key, "✅ 完成"])
        for branch_key in result.get("failed_branches", []):
            QTreeWidgetItem(self._branch_tree, [branch_key, "❌ 失败"])

    def _on_export_html(self):
        pass  # TODO: 调用 ReportExporter.export_html

    def _on_export_json(self):
        pass  # TODO: 调用 ReportExporter.export_json

    def _on_save_as_plan(self):
        self.save_as_plan.emit()
