"""FlowInspector：解析流程定义，返回节点+分支+表单"""
from __future__ import annotations

from workflow_test_desktop.core.session.manager import SessionManager
from workflow_test_desktop.core.config.environment import AppConfig
from workflow_test_desktop.data.models import (
    FlowNodeDescriptor, AssignmentTarget,
    BranchDescriptor, ParsedFlow, FormField,
)


class FlowInspector:
    """
    解析流程定义，返回：
    - 起始表单字段
    - 节点列表（含审核人配置）
    - 分支关系
    """

    def __init__(self, config: AppConfig, http_client, session_manager: SessionManager):
        self._config = config
        self._http = http_client
        self._sm = session_manager

    async def inspect(
        self,
        env_id: str,
        username: str,
        flow_id: str,
    ) -> ParsedFlow:
        """解析指定流程，返回完整结构"""
        lease = await self._sm.get_session(env_id, "user_login", username)
        self._http.set_sid(lease.sid)

        resp = await self._http.post(
            self._config.flow_detail_path,
            json={"id": flow_id},
        )
        raw = resp.json()
        data = raw.get("data", raw) if isinstance(raw, dict) else raw

        form_fields = self._parse_form_fields(data.get("formConfig", []))
        branches = self._parse_branches(data.get("flowBranchList", []))
        nodes = self._parse_nodes(data.get("flowNodeList", []), branches)

        return ParsedFlow(
            flow_id=flow_id,
            flow_name=data.get("flowTemplateName", ""),
            start_form_fields=form_fields,
            nodes=nodes,
            branches=branches,
            raw=data,
        )

    def _parse_form_fields(self, form_config: list) -> list[FormField]:
        fields = []
        for item in form_config:
            fields.append(FormField(
                field_id=item["fieldId"],
                field_name=item.get("label", item["fieldId"]),
                field_type=item.get("type", "text"),
                required=item.get("required", False),
                readonly=item.get("readonly", False),
                options=item.get("options"),
                default_value=item.get("default"),
                raw=item,
            ))
        return fields

    def _parse_branches(self, branches_config: list) -> list[BranchDescriptor]:
        branches = []
        for item in branches_config:
            branches.append(BranchDescriptor(
                branch_id=item["branchId"],
                branch_name=item.get("branchName", item["branchId"]),
                parent_branch_id=item.get("parentBranchId"),
                condition=item.get("condition"),
                raw=item,
            ))
        return branches

    def _parse_nodes(self, nodes_config: list, branches: list[BranchDescriptor]) -> list[FlowNodeDescriptor]:
        descriptors = []
        for item in nodes_config:
            # 解析 flowNodeUserList -> AssignmentTarget
            assignment_targets = []
            for user in item.get("flowNodeUserList", []):
                assignment_targets.append(AssignmentTarget(
                    user_id=user.get("userId", ""),
                    user_name=user.get("userName", ""),
                    audit_type=user.get("auditType", ""),
                ))

            descriptors.append(FlowNodeDescriptor(
                node_id=item["nodeId"],
                node_name=item.get("nodeName", item["nodeId"]),
                node_type=item.get("nodeType", ""),
                audit_type=item.get("auditType", ""),
                branch_id=item.get("branchId"),
                requires_assignment=bool(assignment_targets),
                assignment_targets=assignment_targets,
                raw=item,
            ))
        return descriptors
