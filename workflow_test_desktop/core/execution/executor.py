"""NodeExecutor：单节点执行器"""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Any

from workflow_test_desktop.core.session.manager import SessionManager
from workflow_test_desktop.core.session.lease import SessionLease
from workflow_test_desktop.core.assignment.models import AssignmentResult
from workflow_test_desktop.core.storage.recorder import RunRecorder
from workflow_test_desktop.data.models import FlowNodeDescriptor

logger = logging.getLogger(__name__)


class NodeStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeExecutor:
    """
    单节点执行器。

    流程：
    1. 检查暂停状态
    2. 根据 AssignmentResult 解析当前处理人
    3. 通过 SessionManager 获取处理人会话
    4. 构造 API 请求（审计/审批）
    5. 发送请求（带 SID 重试逻辑）
    6. 解析响应
    7. 记录日志并更新节点状态
    """

    # API 路径（配置端 /api/web/flowInstanceApi/）
    AUDIT_PATH = "/web/flowInstanceApi/audit"

    def __init__(
        self,
        session_manager: SessionManager,
        recorder: RunRecorder,
        http_client,
    ):
        self._sm = session_manager
        self._recorder = recorder
        self._http = http_client
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    async def execute(
        self,
        node_run_id: str,
        node: FlowNodeDescriptor,
        assignment: AssignmentResult | None,
        execution_id: str,
        branch_id: str,
        env_id: str,
        flow_instance_id: str,
        job_task_link_id: str,
        action_type: str = "APPROVE",
        comment: str = "",
    ) -> dict[str, Any]:
        """执行单个审批节点，返回执行结果"""
        await self._pause_event.wait()

        start_time = time.time()
        await self._recorder.log_request(
            run_id=int(execution_id) if execution_id.isdigit() else 0,
            step_name=node.node_name,
            method="POST",
            url=self.AUDIT_PATH,
            params=None,
        )

        try:
            # 步骤1：解析处理人
            handler_username = self._resolve_handler(assignment)

            # 步骤2：获取处理人会话
            lease = await self._sm.get_session(env_id, "user_login", handler_username)
            self._http.set_sid(lease.sid)

            # 步骤3：构造请求体（符合 API 数据规范 Section 4.2）
            request_body = self._build_audit_request(
                flow_instance_id=flow_instance_id,
                job_task_link_id=job_task_link_id,
                action_type=action_type,
                comment=comment,
                assignment=assignment,
            )

            # 步骤4：发送请求（带 SID 失效重试）
            duration_ms = 0
            response_status = 0
            response_body = ""
            resp = None
            try:
                resp = await self._http.post(self.AUDIT_PATH, json=request_body)
                response_status = resp.status_code
                response_body = resp.text[:500] if resp.text else ""
            except Exception as e:
                logger.warning(f"节点请求失败: {e}")
                # SID 失效？尝试重登
                new_lease = await self._sm.refresh_if_needed(lease, 0, str(e))
                if new_lease.sid != lease.sid:
                    self._http.set_sid(new_lease.sid)
                    resp = await self._http.post(self.AUDIT_PATH, json=request_body)
                    response_status = resp.status_code
                    response_body = resp.text[:500] if resp.text else ""

            duration_ms = int((time.time() - start_time) * 1000)

            # 步骤5：记录响应
            await self._recorder.log_response(
                run_id=int(execution_id) if execution_id.isdigit() else 0,
                step_name=node.node_name,
                status_code=response_status,
                body_preview=response_body,
                duration_ms=duration_ms,
            )

            # 步骤6：判断成功（对标 invest 前端：isSuccess 或 code==0）
            success = response_status == 200
            if resp is not None:
                try:
                    body_json = resp.json()
                    success = body_json.get("isSuccess") is not False and body_json.get("code", -1) == 0
                except Exception:
                    pass

            return {
                "status": "completed" if success else "failed",
                "node_id": node.node_id,
                "node_run_id": node_run_id,
                "handler": handler_username,
                "response_status": response_status,
                "duration_ms": duration_ms,
                "response_body": response_body,
            }

        except Exception as e:
            logger.exception(f"节点执行失败: {node.node_id}")
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "failed",
                "node_id": node.node_id,
                "node_run_id": node_run_id,
                "error": str(e),
                "duration_ms": duration_ms,
            }

    def _resolve_handler(self, assignment: AssignmentResult | None) -> str:
        """从指派结果解析处理人用户名"""
        if assignment and assignment.selected_id:
            return assignment.selected_id
        raise ValueError("无法解析处理人：assignment 为空")

    def _build_audit_request(
        self,
        flow_instance_id: str,
        job_task_link_id: str,
        action_type: str,
        comment: str,
        assignment: AssignmentResult | None,
    ) -> dict[str, Any]:
        """
        构造审批请求体。

        符合 API 数据规范 Section 4.2：
        POST /web/flowInstanceApi/audit
        """
        body = {
            "flowInstanceId": flow_instance_id,
            "jobTaskLinkId": job_task_link_id,
            "auditType": action_type,  # APPROVE / REJECT / TRANSFER
            "comment": comment,
        }
        return body
