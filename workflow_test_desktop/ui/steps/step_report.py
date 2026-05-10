"""步骤6：执行报告 - 概览卡片 + 结果树 + 导出"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX, SPACE_MD_PX

logger = logging.getLogger(__name__)


class StepReport(QWidget):
    """报告查看步骤"""

    save_as_plan = Signal()
    rerun_requested = Signal()

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._setup_ui()
        self._load_from_shared()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("执行报告")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        for label_text, action in [
            ("导出 HTML", self._on_export_html),
            ("导出 JSON", self._on_export_json),
            ("重新运行", self._on_rerun),
            ("另存为运行计划", self._on_save_as_plan),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.setProperty("theme", "secondary")
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 概览卡片
        overview_card = QFrame()
        overview_card.setObjectName("card")
        overview_card.setStyleSheet(
            "QFrame#card { background-color: #FFFFFF; border: 1px solid #E2E4E9; "
            "border-radius: 12px; padding: 20px; }"
        )
        gl = QHBoxLayout(overview_card)
        gl.setSpacing(SPACE_MD_PX)

        self._summary_items: dict[str, QLabel] = {}
        for key, label_text in [
            ("flow_name", "流程名"),
            ("status", "状态"),
            ("branch_count", "分支数"),
            ("node_count", "节点数"),
            ("duration", "用时"),
            ("initiator", "发起人"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(4)
            lbl_title = QLabel(label_text)
            lbl_title.setFont(FONT_FAMILY)
            lbl_title.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            lbl_value = QLabel("--")
            lbl_value.setFont(FONT_FAMILY)
            lbl_value.setStyleSheet("font-size: 18px; font-weight: 700; color: #1A1D26;")
            col.addWidget(lbl_value)
            col.addWidget(lbl_title)
            gl.addLayout(col)
            self._summary_items[key] = lbl_value

        layout.addWidget(overview_card)

        # 结果树
        self._result_tree = QTreeWidget()
        self._result_tree.setFont(FONT_FAMILY)
        self._result_tree.setHeaderLabels(["项目", "状态", "用时", "详情"])
        self._result_tree.setAlternatingRowColors(True)
        self._result_tree.setStyleSheet(
            "QTreeWidget { border: 1px solid #E2E4E9; border-radius: 8px; padding: 4px; }"
        )
        layout.addWidget(self._result_tree, 1)

        # 会话日志
        log_label = QLabel("会话日志")
        log_label.setFont(FONT_FAMILY)
        log_label.setStyleSheet("font-weight: 600; color: #374151; font-size: 14px;")
        layout.addWidget(log_label)

        self._session_log = QTextEdit()
        self._session_log.setFont(FONT_FAMILY)
        self._session_log.setReadOnly(True)
        self._session_log.setPlaceholderText("会话日志...")
        self._session_log.setMaximumHeight(160)
        layout.addWidget(self._session_log)

    # ─── 加载数据 ───────────────────────────────────────────────

    def _load_from_shared(self):
        """从 shared_data 加载上次运行结果"""
        result = self._shared_data.get("last_run_result", {})
        if result:
            self._set_report_data(result)
        else:
            # 显示空状态
            for lbl in self._summary_items.values():
                lbl.setText("--")
            lbl_status = self._summary_items.get("status")
            if lbl_status:
                lbl_status.setText("暂无数据")
                lbl_status.setStyleSheet("font-size: 18px; font-weight: 700; color: #9CA3AF;")

    def _set_report_data(self, result: dict):
        """设置报告数据（从 StepRun 完成后调用）"""
        flow_name = self._shared_data.get("flow_name", "--")
        duration_ms = result.get("duration_ms", 0)
        all_completed = result.get("all_completed", False)
        completed_branches = result.get("completed_branches", [])
        failed_branches = result.get("failed_branches", [])
        node_results = result.get("node_results", {})

        # 概览
        self._summary_items["flow_name"].setText(flow_name)

        status_text = "✅ 全部完成" if all_completed else "⚠ 部分失败"
        status_color = "#10B981" if all_completed else "#EF4444"
        self._summary_items["status"].setText(status_text)
        self._summary_items["status"].setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {status_color};"
        )

        self._summary_items["branch_count"].setText(str(len(completed_branches) + len(failed_branches)))
        self._summary_items["node_count"].setText(str(len(node_results)))
        seconds = duration_ms // 1000
        self._summary_items["duration"].setText(f"{seconds}s")
        self._summary_items["initiator"].setText(
            self._shared_data.get("starter_username", "--")
        )

        # 结果树
        self._result_tree.clear()

        # 分支节点
        all_branches = completed_branches + failed_branches
        for branch in all_branches:
            branch_item = QTreeWidgetItem(
                self._result_tree,
                [
                    branch.get("branchName", "分支"),
                    "✅ 完成" if branch in completed_branches else "❌ 失败",
                    f"{branch.get('duration_ms', 0)}ms",
                    branch.get("condition", ""),
                ],
            )
            branch_item.setExpanded(True)

            # 分支下的节点
            branch_nodes = branch.get("nodes", [])
            for node in branch_nodes:
                node_item = QTreeWidgetItem(
                    branch_item,
                    [
                        node.get("nodeName", "节点"),
                        "✅ 完成" if node.get("status") == "completed" else "❌ 失败",
                        f"{node.get('elapsed_ms', 0)}ms",
                        node.get("error", ""),
                    ],
                )
                status = node.get("status", "pending")
                if status == "completed":
                    node_item.setForeground(1, Qt.darkGreen)
                else:
                    node_item.setForeground(1, Qt.darkRed)

        # 如果没有分支结构，按节点显示
        if not all_branches and node_results:
            for node_id, node_result in node_results.items():
                node_item = QTreeWidgetItem(
                    self._result_tree,
                    [
                        node_result.get("node_name", node_id),
                        "✅ 完成" if node_result.get("status") == "completed" else "❌ 失败",
                        f"{node_result.get('elapsed_ms', 0)}ms",
                        node_result.get("error", ""),
                    ],
                )

        # 日志
        logs = result.get("logs", [])
        if logs:
            self._session_log.setPlainText("\n".join(str(log) for log in logs))
        elif not all_branches and not node_results:
            self._session_log.setPlaceholderText("暂无会话日志")

    # ─── 导出 ───────────────────────────────────────────────

    def _on_export_html(self):
        result = self._shared_data.get("last_run_result", {})
        if not result:
            QMessageBox.information(self, "提示", "暂无运行结果可导出")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 HTML",
            "execution_report.html",
            "HTML Files (*.html)",
        )
        if not path:
            return

        flow_name = self._shared_data.get("flow_name", "unknown")
        duration_ms = result.get("duration_ms", 0)
        all_completed = result.get("all_completed", False)
        node_results = result.get("node_results", {})

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>执行报告 - {flow_name}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 40px; background: #F9FAFB; }}
  .card {{ background: white; border: 1px solid #E2E4E9; border-radius: 12px; padding: 24px; margin-bottom: 16px; }}
  h1 {{ color: #1A1D26; }}
  .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .stat {{ text-align: center; }}
  .stat-value {{ font-size: 28px; font-weight: 700; }}
  .stat-label {{ color: #6B7280; font-size: 13px; }}
  .success {{ color: #10B981; }}
  .error {{ color: #EF4444; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #E2E4E9; }}
  th {{ background: #F4F5F7; font-weight: 600; font-size: 12px; color: #6B7280; text-transform: uppercase; }}
</style>
</head>
<body>
<h1>执行报告</h1>
<div class="card">
  <h2>{flow_name}</h2>
  <div class="summary">
    <div class="stat">
      <div class="stat-value {'success' if all_completed else 'error'}">
        {'✅ 全部完成' if all_completed else '⚠ 部分失败'}
      </div>
      <div class="stat-label">执行状态</div>
    </div>
    <div class="stat">
      <div class="stat-value">{len(node_results)}</div>
      <div class="stat-label">节点数</div>
    </div>
    <div class="stat">
      <div class="stat-value">{duration_ms / 1000:.1f}s</div>
      <div class="stat-label">总用时</div>
    </div>
  </div>
</div>
<div class="card">
  <h3>节点详情</h3>
  <table>
    <thead><tr><th>节点</th><th>状态</th><th>用时</th><th>详情</th></tr></thead>
    <tbody>
"""
        for node_id, nr in node_results.items():
            status = nr.get("status", "pending")
            status_html = '<span class="success">✅ 完成</span>' if status == "completed" else '<span class="error">❌ 失败</span>'
            html += f"""      <tr>
        <td>{nr.get('node_name', node_id)}</td>
        <td>{status_html}</td>
        <td>{nr.get('elapsed_ms', 0)}ms</td>
        <td>{nr.get('error', '')}</td>
      </tr>
"""
        html += """    </tbody>
  </table>
</div>
</body>
</html>"""

        try:
            Path(path).write_text(html, encoding="utf-8")
            logger.info("[StepReport] HTML 报告已导出: %s", path)
            QMessageBox.information(self, "导出成功", f"HTML 报告已保存至:\n{path}")
        except Exception as e:
            logger.error("[StepReport] 导出 HTML 失败: %s", e)
            QMessageBox.warning(self, "导出失败", f"导出失败: {e}")

    def _on_export_json(self):
        result = self._shared_data.get("last_run_result", {})
        if not result:
            QMessageBox.information(self, "提示", "暂无运行结果可导出")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 JSON",
            "execution_report.json",
            "JSON Files (*.json)",
        )
        if not path:
            return

        try:
            export_data = {
                "flow_name": self._shared_data.get("flow_name", ""),
                "flow_id": self._shared_data.get("flow_id", ""),
                "initiator": self._shared_data.get("starter_username", ""),
                **result,
            }
            Path(path).write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("[StepReport] JSON 报告已导出: %s", path)
            QMessageBox.information(self, "导出成功", f"JSON 报告已保存至:\n{path}")
        except Exception as e:
            logger.error("[StepReport] 导出 JSON 失败: %s", e)
            QMessageBox.warning(self, "导出失败", f"导出失败: {e}")

    def _on_rerun(self):
        """重新运行：返回到步骤2"""
        self.rerun_requested.emit()

    def _on_save_as_plan(self):
        self.save_as_plan.emit()

    # ─── 公共方法 ───────────────────────────────────────────────

    def get_report_data(self) -> dict:
        """返回当前报告数据"""
        return {
            "flow_name": self._shared_data.get("flow_name", ""),
            "flow_id": self._shared_data.get("flow_id", ""),
            "result": self._shared_data.get("last_run_result", {}),
        }

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """报告步骤无需验证"""
        return True, ""
