"""RunRecorder：唯一写入接口，所有 DB 写入必须经此"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from workflow_test_desktop.core.storage.database import get_db, DBManager
from workflow_test_desktop.core.storage.sanitizer import (
    sanitize_request_summary,
    sanitize_response_summary,
)


class DBConnection(Protocol):
    """DB 连接接口（aiosqlite.Connection 或 DBManager）"""
    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...
    async def fetchall(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...
    async def fetchone(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None: ...


class RunRecorder:
    """
    所有数据库写入的唯一入口。
    关键原则：
    - 所有写入必须经此
    - 写入前自动脱敏（由 sanitizer 处理）
    - 不直接持有连接，由调用方传入
    """

    def __init__(self, db: DBConnection):
        self._db = db

    async def start_run(self, flow_id: str, plan: dict[str, Any]) -> int:
        """启动一次运行，返回 run_id"""
        started_at = datetime.now(timezone.utc).isoformat()
        cursor = await self._db.execute(
            """INSERT INTO runs (flow_id, started_at, status, summary)
               VALUES (:flow_id, :started_at, 'running', :summary)""",
            {"flow_id": flow_id, "started_at": started_at, "summary": json.dumps(plan)},
        )
        # aiosqlite returns cursor.lastrowid
        return cursor.lastrowid if hasattr(cursor, "lastrowid") else cursor.last_insert_id()

    async def end_run(self, run_id: int, status: str,
                      error_message: str | None = None) -> None:
        """结束一次运行"""
        finished_at = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """UPDATE runs
               SET finished_at = :finished_at, status = :status, error_message = :error_message
               WHERE id = :id""",
            {
                "finished_at": finished_at,
                "status": status,
                "error_message": error_message,
                "id": run_id,
            },
        )

    async def log_request(self, run_id: int, step_name: str,
                          method: str, url: str,
                          params: dict[str, Any] | None = None,
                          headers: dict[str, Any] | None = None) -> None:
        """记录 HTTP 请求（自动脱敏）"""
        summary = sanitize_request_summary(method, url, params, headers)
        await self._db.execute(
            """INSERT INTO http_logs
               (run_id, step_name, direction, method, url, params, headers, status_code, body_preview, duration_ms)
               VALUES (:run_id, :step_name, 'request', :method, :url, :params, :headers, NULL, NULL, NULL)""",
            {
                "run_id": run_id,
                "step_name": step_name,
                "method": summary["method"],
                "url": summary["url"],
                "params": json.dumps(summary.get("params")),
                "headers": json.dumps(summary.get("headers")),
            },
        )

    async def log_response(self, run_id: int, step_name: str,
                           status_code: int,
                           body_preview: str | None = None,
                           duration_ms: int | None = None) -> None:
        """记录 HTTP 响应（自动脱敏）"""
        summary = sanitize_response_summary(status_code, body_preview)
        await self._db.execute(
            """INSERT INTO http_logs
               (run_id, step_name, direction, method, url, params, headers, status_code, body_preview, duration_ms)
               VALUES (:run_id, :step_name, 'response', NULL, NULL, NULL, NULL, :status_code, :body_preview, :duration_ms)""",
            {
                "run_id": run_id,
                "step_name": step_name,
                "status_code": summary["status_code"],
                "body_preview": summary.get("body_preview"),
                "duration_ms": duration_ms,
            },
        )

    async def query_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """查询运行列表（按 id 倒序）"""
        rows = await self._db.fetchall(
            "SELECT * FROM runs ORDER BY id DESC LIMIT :limit",
            {"limit": limit},
        )
        return rows

    async def log_session(
        self,
        run_id: int,
        env_id: str,
        login_type: str,
        username: str,
        generation: int,
        action: str,
        reason: str,
    ) -> None:
        """记录会话日志（登录/重登/失效）"""
        await self._db.execute(
            """INSERT INTO session_logs
               (run_id, env_id, login_type, username, generation, action, reason)
               VALUES (:run_id, :env_id, :login_type, :username, :generation, :action, :reason)""",
            {
                "run_id": run_id,
                "env_id": env_id,
                "login_type": login_type,
                "username": username,
                "generation": generation,
                "action": action,
                "reason": reason,
            },
        )
