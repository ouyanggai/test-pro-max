"""测试 RunPlan 和 RunPlanBuilder"""
import pytest
import json
from workflow_test_desktop.core.execution import RunPlan, RunPlanBuilder


def test_run_plan_to_json():
    plan = RunPlan(
        name="test plan",
        environment={"env_id": "dev"},
        starter={"mode": "default_super_account", "user": {"username": "test"}},
    )
    json_str = plan.to_json()
    data = json.loads(json_str)
    assert data["name"] == "test plan"
    assert data["environment"]["env_id"] == "dev"


def test_run_plan_from_json():
    data = {
        "version": 1, "name": "from json", "environment": {},
        "starter": {}, "flow": {}, "form_data": {},
        "assignments": {}, "branch_execution": {}, "session_policy": {},
        "assertions": [],
    }
    plan = RunPlan.from_json(json.dumps(data, ensure_ascii=False))
    assert plan.name == "from json"


def test_builder_chaining():
    plan = (RunPlanBuilder()
        .set_name("付款回归")
        .set_environment("test", "https://api.example.com")
        .set_starter("user1", "测试用户")
        .set_flow("flow_001", "付款审批")
        .set_form_data(fields={"amount": 1000})
        .set_branch_execution(max_concurrency=3)
        .set_assignments(random_seed=42)
        .build())

    assert plan.name == "付款回归"
    assert plan.starter["user"]["username"] == "user1"
    assert plan.flow["flow_id"] == "flow_001"
    assert plan.form_data["fields"]["amount"] == 1000
    assert plan.branch_execution["max_branch_concurrency"] == 3
    assert plan.assignments["random_seed"] == 42


def test_builder_default_assignments():
    plan = RunPlanBuilder().set_name("x").set_assignments().build()
    assert plan.assignments["random_seed"] is not None


def test_run_plan_to_dict():
    plan = RunPlan(name="dict test", version=1)
    d = plan.to_dict()
    assert d["name"] == "dict test"
    assert d["version"] == 1


def test_run_plan_from_dict_unknown_field():
    data = {"version": 1, "name": "ignore unknown", "unknown_field": 123}
    plan = RunPlan.from_dict(data)
    assert plan.name == "ignore unknown"
    assert not hasattr(plan, "unknown_field")
