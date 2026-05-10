"""指派引擎数据类"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# 指派策略常量
STRATEGY_MANUAL = "manual"
STRATEGY_ONE_CLICK = "one_click"
STRATEGY_RANDOM = "random"
STRATEGY_RANGE_RANDOM = "range_random"
STRATEGY_POSITION_RANDOM = "position_random"
STRATEGY_DEPARTMENT_RANDOM = "department_random"


@dataclass
class CandidateScope:
    """候选人过滤范围"""
    departments: list[str] = field(default_factory=list)
    positions: list[str] = field(default_factory=list)
    users: list[str] = field(default_factory=list)
    exclude_users: list[str] = field(default_factory=list)
    exclude_starter: bool = False
    exclude_used: bool = False


@dataclass
class CandidatePool:
    """候选池"""
    users: list[dict[str, Any]] = field(default_factory=list)
    departments: list[dict[str, Any]] = field(default_factory=list)
    positions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AssignmentRule:
    """指派规则（从 RunPlan 读取）"""
    node_id: str
    field: str
    selector_type: str  # user / department / position
    mode: str  # manual / one_click / random / range_random / position_random / department_random
    scope: CandidateScope | None = None
    selected_user: str | None = None
    selected_department: str | None = None
    selected_position: str | None = None


@dataclass
class AssignmentResult:
    """每次指派的完整决策信息"""
    node_id: str
    field: str
    selector_type: str
    mode: str
    selected_id: str
    selected_name: str
    candidate_count: int
    random_seed: int | None
    reason: str
    candidate_snapshot_id: str | None = None
