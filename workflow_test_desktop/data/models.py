"""项目内共享的数据类"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StartableFlow:
    """可发起的流程"""
    flow_id: str
    flow_code: str | None
    flow_name: str
    category_name: str | None
    starter_username: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowNodeDescriptor:
    """流程节点描述"""
    node_id: str
    node_name: str
    node_type: str  # APPROVAL / ...
    audit_type: str  # ASSIGN / POSITION / COMPANY / ROLE / DEPARTMENT / ...
    branch_id: str | None
    requires_assignment: bool
    assignment_targets: list
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentTarget:
    """节点指派目标（来自 flowNodeUserList）"""
    user_id: str
    user_name: str
    audit_type: str  # assign / company / department / position / role ...


@dataclass
class NodeActionConfig:
    """节点动作配置"""
    action_type: str
    handler_source: str
    requires_login_user: bool
    candidate_source: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class BranchDescriptor:
    """分支描述"""
    branch_id: str
    branch_name: str
    parent_branch_id: str | None
    condition: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedFlow:
    """解析后的完整流程结构"""
    flow_id: str
    flow_name: str
    start_form_fields: list
    nodes: list
    branches: list
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class FormField:
    """表单字段"""
    field_id: str
    field_name: str
    field_type: str
    required: bool
    readonly: bool
    options: list[str] | None
    default_value: Any | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBrief:
    """用户简要信息"""
    user_id: str
    username: str
    display_name: str
    department_id: str | None
    department_name: str | None
    position_id: str | None
    position_name: str | None
    enabled: bool


@dataclass
class DepartmentBrief:
    """部门简要信息"""
    department_id: str
    department_name: str
    parent_id: str | None


@dataclass
class PositionBrief:
    """岗位简要信息"""
    position_id: str
    position_name: str
    department_id: str | None
