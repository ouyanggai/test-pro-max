"""RunPlan 数据类 + RunPlanBuilder"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class RunPlan:
    """运行计划（内部契约）"""
    version: int = 1
    name: str = ""
    environment: dict[str, Any] = field(default_factory=dict)
    starter: dict[str, Any] = field(default_factory=dict)
    flow: dict[str, Any] = field(default_factory=dict)
    form_data: dict[str, Any] = field(default_factory=dict)
    assignments: dict[str, Any] = field(default_factory=dict)
    branch_execution: dict[str, Any] = field(default_factory=dict)
    session_policy: dict[str, Any] = field(default_factory=dict)
    assertions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunPlan:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, json_str: str) -> RunPlan:
        return cls.from_dict(json.loads(json_str))


class RunPlanBuilder:
    """将 UI 配置转换为 RunPlan"""

    def __init__(self):
        self._plan = RunPlan()

    def set_name(self, name: str) -> RunPlanBuilder:
        self._plan.name = name
        return self

    def set_environment(self, env_id: str, gateway_url: str) -> RunPlanBuilder:
        self._plan.environment = {"env_id": env_id, "gateway_ref": "config.env.GATEWAY_URL"}
        return self

    def set_starter(self, username: str, display_name: str, mode: str = "default_super_account") -> RunPlanBuilder:
        self._plan.starter = {"mode": mode, "user": {"username": username, "display_name": display_name}}
        return self

    def set_flow(self, flow_id: str, flow_name: str) -> RunPlanBuilder:
        self._plan.flow = {"flow_id": flow_id, "flow_name": flow_name, "select_mode": "starter_visible_flows"}
        return self

    def set_form_data(self, strategy: str = "fixed", fields: dict[str, Any] | None = None) -> RunPlanBuilder:
        self._plan.form_data = {"strategy": strategy, "fields": fields or {}}
        return self

    def set_assignments(
        self,
        default_policy: str = "manual_first",
        random_seed: int | None = None,
        rules: list[dict[str, Any]] | None = None,
    ) -> RunPlanBuilder:
        self._plan.assignments = {
            "default_policy": default_policy,
            "random_seed": random_seed or int(time.time()),
            "rules": rules or [],
        }
        return self

    def set_branch_execution(
        self,
        mode: str = "parallel_branches",
        max_concurrency: int = 5,
        failure_policy: str = "wait_all_then_fail",
    ) -> RunPlanBuilder:
        self._plan.branch_execution = {
            "mode": mode,
            "max_branch_concurrency": max_concurrency,
            "failure_policy": failure_policy,
        }
        return self

    def set_session_policy(
        self,
        sid_reuse: bool = True,
        relogin: str = "only_when_missing_or_expired",
        duplicate_login_guard: bool = True,
    ) -> RunPlanBuilder:
        self._plan.session_policy = {
            "sid_reuse": sid_reuse,
            "relogin": relogin,
            "duplicate_login_guard": duplicate_login_guard,
        }
        return self

    def build(self) -> RunPlan:
        return RunPlan(
            version=self._plan.version,
            name=self._plan.name,
            environment=self._plan.environment,
            starter=self._plan.starter,
            flow=self._plan.flow,
            form_data=self._plan.form_data,
            assignments=self._plan.assignments,
            branch_execution=self._plan.branch_execution,
            session_policy=self._plan.session_policy,
            assertions=self._plan.assertions,
        )
