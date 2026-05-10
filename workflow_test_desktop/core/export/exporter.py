"""ReportExporter：读取 SQLite 生成 HTML / JSON 报告"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from workflow_test_desktop.core.storage.database import DBManager
from workflow_test_desktop.core.export.templates import (
    HTML_TEMPLATE, build_summary_item, build_node_item, build_log_entry,
)


class ReportExporter:
    """
    报告导出器。
    敏感字段已在 RunRecorder 层统一脱敏，此处直接使用。
    """

    def __init__(self, db: DBManager):
        self._db = db

    async def export_html(self, run_id: int, output_path: str | Path) -> Path:
        """生成 HTML 报告"""
        data = await self._load_report_data(run_id)
        html = HTML_TEMPLATE.format(
            title=f"执行报告 - {data.get('flow_id', '未知')} - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            summary_items=self._build_summary(data),
            branch_details=self._build_branch_details(data),
            session_log=self._build_session_log(data),
        )
        path = Path(output_path)
        path.write_text(html, encoding="utf-8")
        return path

    async def export_json(self, run_id: int, output_path: str | Path) -> Path:
        """生成 JSON 报告"""
        data = await self._load_report_data(run_id)
        path = Path(output_path)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    async def _load_report_data(self, run_id: int) -> dict[str, Any]:
        """从数据库加载报告所需数据"""
        # 查运行记录
        runs = await self._db.fetchall(
            "SELECT * FROM runs WHERE id = :id",
            {"id": run_id},
        )
        execution = runs[0] if runs else {}

        # 查 HTTP 日志
        http_logs = await self._db.fetchall(
            "SELECT * FROM http_logs WHERE run_id = :run_id ORDER BY created_at",
            {"run_id": run_id},
        )

        # 查会话日志
        session_logs = await self._db.fetchall(
            "SELECT * FROM session_logs WHERE run_id = :run_id ORDER BY created_at",
            {"run_id": run_id},
        )

        return {
            "run": dict(execution) if execution else {},
            "http_logs": [dict(log) for log in http_logs],
            "session_logs": [dict(log) for log in session_logs],
            "flow_id": execution.get("flow_id", "未知") if execution else "未知",
        }

    def _build_summary(self, data: dict) -> str:
        run = data.get("run", {})
        flow_id = data.get("flow_id", "未知")
        status = run.get("status", "未知")
        started = run.get("started_at", "")
        finished = run.get("finished_at", "")

        # 计算用时
        elapsed_str = "--"
        if started and finished:
            try:
                start_ts = time.mktime(time.strptime(started, "%Y-%m-%dT%H:%M:%S"))
                end_ts = time.mktime(time.strptime(finished, "%Y-%m-%dT%H:%M:%S"))
                elapsed = int(end_ts - start_ts)
                elapsed_str = f"{elapsed}s"
            except (ValueError, TypeError):
                elapsed_str = "--"

        # 统计
        http_logs = data.get("http_logs", [])
        request_count = sum(1 for log in http_logs if log.get("direction") == "request")
        session_logs = data.get("session_logs", [])

        items = [
            build_summary_item("流程 ID", flow_id),
            build_summary_item("状态", status),
            build_summary_item("开始时间", started[:19] if started else "--"),
            build_summary_item("结束时间", finished[:19] if finished else "--"),
            build_summary_item("用时", elapsed_str),
            build_summary_item("HTTP 请求数", str(request_count)),
            build_summary_item("会话切换数", str(len(session_logs))),
            build_summary_item("发起人", run.get("summary", "")),
        ]
        return "\n".join(items)

    def _build_branch_details(self, data: dict) -> str:
        """根据 HTTP 日志构建执行详情"""
        http_logs = data.get("http_logs", [])
        if not http_logs:
            return "<div>无执行记录</div>"

        lines = []
        current_branch = "主流程"

        for log in http_logs:
            direction = log.get("direction", "")
            step_name = log.get("step_name", "")
            method = log.get("method", "")
            url = log.get("url", "")
            status_code = log.get("status_code")
            duration_ms = log.get("duration_ms")
            body_preview = log.get("body_preview", "")

            if direction == "request":
                lines.append(
                    f'<div class="node-item running">'
                    f'&#9654; {step_name or url} <span>{method} {duration_ms or 0}ms</span>'
                    f'</div>'
                )
                current_branch = step_name or url

            elif direction == "response":
                status_color = "#10B981" if status_code and status_code < 400 else "#EF4444"
                lines.append(
                    f'<div class="node-item completed">'
                    f'&#10003; {step_name or "响应"} <span style="color:{status_color}">{status_code or "?"}</span>'
                    f'<span>{duration_ms or 0}ms</span>'
                    f'</div>'
                )

        return "\n".join(lines) if lines else "<div>无执行记录</div>"

    def _build_session_log(self, data: dict) -> str:
        logs = data.get("session_logs", [])
        if not logs:
            return '<div class="log-entry">无会话记录</div>'

        lines = []
        for log in logs:
            created_at = log.get("created_at", "")
            ts = created_at[11:19] if len(created_at) > 19 else created_at
            username = log.get("username", "")
            action = log.get("action", "")
            reason = log.get("reason", "")
            lines.append(build_log_entry(ts, username, action, reason))

        return "\n".join(lines)
