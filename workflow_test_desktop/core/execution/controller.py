"""ExecutionController：执行编排层，串联所有模块"""
from __future__ import annotations

import logging
from typing import Any, Callable

from workflow_test_desktop.core.execution.run_plan import RunPlan
from workflow_test_desktop.core.execution.scheduler import BranchScheduler, BranchTask, FailurePolicy
from workflow_test_desktop.core.execution.executor import NodeExecutor
from workflow_test_desktop.core.session.manager import SessionManager
from workflow_test_desktop.core.storage.recorder import RunRecorder
from workflow_test_desktop.core.flow.inspector import FlowInspector
from workflow_test_desktop.core.assignment.engine import AssignmentEngine
from workflow_test_desktop.core.assignment.models import AssignmentRule, CandidatePool, CandidateScope
from workflow_test_desktop.data.models import ParsedFlow, FlowNodeDescriptor
from workflow_test_desktop.api.client import ApiClient

logger = logging.getLogger(__name__)


class ExecutionController:
    """
    执行编排层。

    串联流程：
    1. 发起人登录 → 提交流程实例（submit）
    2. 解析流程节点（FlowInspector.inspect）
    3. 查找待办任务（findPendingByFlowInstanceId）
    4. 对每个节点执行指派（AssignmentEngine）
    5. 分支并发执行审批（BranchScheduler → NodeExecutor）
    6. 记录日志（RunRecorder）

    符合 API 数据规范：POST /web/flowInstanceApi/submit,
    POST /web/flowJobTaskLink/findPendingByFlowInstanceId,
    POST /web/flowInstanceApi/audit
    """

    # API 路径（配置端 /api/web/）
    SUBMIT_PATH = "/web/flowInstanceApi/submit"
    AUDIT_PATH = "/web/flowInstanceApi/audit"
    PENDING_PATH = "/web/flowJobTaskLink/findPendingByFlowInstanceId"

    def __init__(
        self,
        run_plan: RunPlan,
        recorder: RunRecorder,
        session_manager: SessionManager,
        flow_inspector: FlowInspector,
        assignment_engine: AssignmentEngine,
        http_client: ApiClient,
        progress_callback: Callable[[str, str, Any], None] | None = None,
    ):
        self._plan = run_plan
        self._recorder = recorder
        self._sm = session_manager
        self._inspector = flow_inspector
        self._engine = assignment_engine
        self._http = http_client
        self._progress = progress_callback

        be = run_plan.branch_execution
        self._scheduler = BranchScheduler(
            max_concurrency=be.get("max_branch_concurrency", 5),
            failure_policy=FailurePolicy(be.get("failure_policy", "wait_all_then_fail")),
        )
        self._executor = NodeExecutor(session_manager, recorder, http_client)
        self._used_ids: set[str] = set()

    async def run(self) -> dict[str, Any]:
        """执行完整运行计划"""
        starter_user = self._plan.starter["user"]
        starter_username = starter_user["username"]
        env_id = self._plan.environment.get("env_id", "dev")

        # 创建执行记录
        flow_id = self._plan.flow["flow_id"]
        run_id = await self._recorder.start_run(
            flow_id=flow_id,
            plan=self._plan.to_dict(),
        )

        try:
            # 步骤1：发起人登录
            starter_lease = await self._sm.get_session(env_id, "user_login", starter_username)
            self._http.set_sid(starter_lease.sid)

            # 步骤2：提交流程实例
            flow_instance_id = await self._submit_flow(flow_id)
            self._report_progress("submit", "submitted", {"flow_instance_id": flow_instance_id})

            # 步骤3：查找待办任务
            pending_tasks = await self._find_pending_tasks(flow_instance_id)
            task_map = {_t.get("nodeProxyId"): _t for _t in pending_tasks}

            # 步骤4：解析流程节点
            parsed_flow = await self._inspector.inspect(env_id, starter_username, flow_id)

            # 步骤5：构建分支任务
            branches = self._build_branch_tasks(
                run_id, parsed_flow, env_id, starter_username, flow_instance_id, task_map
            )

            # 步骤6：并发执行调度
            scheduler_result = await self._scheduler.schedule(
                branches, progress_callback=self._report_progress
            )

            # 步骤7：更新执行状态
            final_status = "completed" if scheduler_result.all_completed else "failed"
            await self._recorder.end_run(run_id, final_status)

            return {
                "run_id": run_id,
                "flow_instance_id": flow_instance_id,
                "all_completed": scheduler_result.all_completed,
                "failed_branches": scheduler_result.failed_branches,
                "completed_branches": scheduler_result.completed_branches,
                "duration_ms": scheduler_result.total_duration_ms,
            }

        except Exception as e:
            logger.exception("执行失败")
            await self._recorder.end_run(run_id, "failed", str(e))
            raise

    async def _submit_flow(self, flow_template_id: str) -> str:
        """
        提交流程实例。

        POST /web/flowInstanceApi/submit
        请求：{"flowTemplateId": "...", "formData": {...}, "bizId": "", "bizType": ""}
        响应：{"code": 0, "data": {"flowInstanceId": "..."}}
        """
        request_body = {
            "flowTemplateId": flow_template_id,
            "formData": self._plan.form_data.get("fields", {}),
            "bizId": "",
            "bizType": "",
        }
        resp = await self._http.post(self.SUBMIT_PATH, json=request_body)
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"提交流程失败: {body}")
        flow_instance_id = body.get("data", {}).get("flowInstanceId")
        if not flow_instance_id:
            raise RuntimeError(f"提交流程返回无 flowInstanceId: {body}")
        return flow_instance_id

    async def _find_pending_tasks(self, flow_instance_id: str) -> list[dict[str, Any]]:
        """
        查找流程实例的待办任务。

        POST /web/flowJobTaskLink/findPendingByFlowInstanceId
        请求：{"flowInstanceId": "..."}
        响应：{"code": 0, "data": [...]}
        """
        resp = await self._http.post(
            self.PENDING_PATH,
            json={"flowInstanceId": flow_instance_id},
        )
        body = resp.json()
        if body.get("code") != 0:
            logger.warning(f"查找待办失败: {body}")
            return []
        data = body.get("data", {})
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("records", [])
        return []

    def _build_branch_tasks(
        self,
        run_id: int,
        parsed_flow: ParsedFlow,
        env_id: str,
        starter_username: str,
        flow_instance_id: str,
        task_map: dict[str, Any],
    ) -> list[BranchTask]:
        """根据解析的流程构建分支任务"""
        tasks: list[BranchTask] = []

        # 按 branch_id 分组节点
        nodes_by_branch: dict[str, list[FlowNodeDescriptor]] = {}
        for node in parsed_flow.nodes:
            bid = node.branch_id or "main"
            nodes_by_branch.setdefault(bid, []).append(node)

        for branch_key, node_list in nodes_by_branch.items():
            async def branch_coro(
                key: str = branch_key,
                nodes: list[FlowNodeDescriptor] = node_list,
                _run_id: int = run_id,
                _env_id: str = env_id,
                _starter: str = starter_username,
                _fiid: str = flow_instance_id,
                _task_map: dict = task_map,
            ) -> list[dict[str, Any]]:
                results: list[dict[str, Any]] = []
                for node in nodes:
                    # 查找对应待办任务
                    task_info = None
                    for proxy_id, task in _task_map.items():
                        if task.get("nodeName") == node.node_name:
                            task_info = task
                            break

                    if task_info is None:
                        logger.warning(f"节点 {node.node_name} 无待办任务，跳过")
                        results.append({"status": "skipped", "node_id": node.node_id})
                        continue

                    job_task_link_id = task_info.get("nodeProxyId", "")

                    # 执行指派
                    assignment_result = self._assign_node(node, _starter, _env_id)

                    # 执行审批
                    node_result = await self._executor.execute(
                        node_run_id="",
                        node=node,
                        assignment=assignment_result,
                        execution_id=str(_run_id),
                        branch_id=key,
                        env_id=_env_id,
                        flow_instance_id=_fiid,
                        job_task_link_id=job_task_link_id,
                        action_type="APPROVE",
                        comment="自动化测试审批",
                    )
                    results.append(node_result)

                    # 记录已用 ID
                    handler = node_result.get("handler")
                    if handler:
                        self._used_ids.add(handler)

                return results

            tasks.append(BranchTask(branch_key=branch_key, coroutine=branch_coro))

        return tasks

    def _assign_node(
        self,
        node: FlowNodeDescriptor,
        starter_username: str,
        env_id: str,
    ):
        """对单个节点执行指派（使用 AssignmentEngine）"""
        # 构建候选池
        pool = CandidatePool(
            users=[
                {
                    "userId": u.user_id,
                    "username": u.user_name,
                    "displayName": u.user_name,
                }
                for u in node.assignment_targets
            ],
            departments=[],
            positions=[],
        )

        # 从 plan 的 assignments 读取规则
        assignments_config = self._plan.assignments
        rules = assignments_config.get("rules", [])
        random_seed = assignments_config.get("random_seed")

        # 查找该节点的规则
        rule_dict = next(
            (r for r in rules if r.get("node_id") == node.node_id), None
        )

        if rule_dict:
            rule = AssignmentRule(
                node_id=node.node_id,
                field="approver",
                selector_type="user",
                mode=rule_dict.get("mode", "manual"),
                scope=CandidateScope(
                    exclude_starter=rule_dict.get("exclude_starter", True),
                ),
                selected_user=rule_dict.get("selected_user"),
            )
        else:
            # 默认策略：一键指定（第一个候选人）
            rule = AssignmentRule(
                node_id=node.node_id,
                field="approver",
                selector_type="user",
                mode="one_click",
                scope=CandidateScope(exclude_starter=True),
            )

        return self._engine.assign(rule, pool, self._used_ids, starter_username, random_seed)

    def _report_progress(self, branch_key: str, status: str, info: Any) -> None:
        if self._progress:
            self._progress(branch_key, status, info)
