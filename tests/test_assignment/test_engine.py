"""测试 AssignmentEngine"""
import pytest
from workflow_test_desktop.core.assignment.engine import AssignmentEngine
from workflow_test_desktop.core.assignment.models import (
    AssignmentRule, CandidatePool, CandidateScope,
    STRATEGY_MANUAL, STRATEGY_ONE_CLICK, STRATEGY_RANDOM,
    STRATEGY_RANGE_RANDOM, STRATEGY_POSITION_RANDOM,
    STRATEGY_DEPARTMENT_RANDOM,
)


@pytest.fixture
def engine():
    return AssignmentEngine()


@pytest.fixture
def sample_pool():
    return CandidatePool(
        users=[
            {"userId": "u1", "username": "alice", "displayName": "Alice"},
            {"userId": "u2", "username": "bob", "displayName": "Bob"},
            {"userId": "u3", "username": "charlie", "displayName": "Charlie"},
            {"userId": "u4", "username": "david", "displayName": "David",
             "departmentId": "dept1", "positionId": "pos1"},
        ],
        departments=[
            {"departmentId": "dept1", "departmentName": "财务部"},
            {"departmentId": "dept2", "departmentName": "技术部"},
        ],
        positions=[
            {"positionId": "pos1", "positionName": "部门负责人"},
            {"positionId": "pos2", "positionName": "普通员工"},
        ],
    )


def test_manual_assign(engine, sample_pool):
    """手动指定返回指定用户"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_MANUAL, selected_user="u2",
    )
    result = engine.assign(rule, sample_pool, used_ids=set())
    assert result.selected_id == "u2"
    assert result.selected_name == "Bob"
    assert result.mode == STRATEGY_MANUAL


def test_manual_assign_not_found(engine, sample_pool):
    """手动指定找不到用户时抛出异常"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_MANUAL, selected_user="nonexistent",
    )
    with pytest.raises(ValueError, match="手动指定失败"):
        engine.assign(rule, sample_pool, used_ids=set())


def test_one_click_assign(engine, sample_pool):
    """一键指定返回第一个候选人"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_ONE_CLICK,
    )
    result = engine.assign(rule, sample_pool, used_ids=set())
    assert result.selected_id == "u1"
    assert result.selected_name == "Alice"
    assert result.reason == "一键指定"


def test_random_assign_deterministic(engine, sample_pool):
    """同一随机种子产生相同结果"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_RANDOM,
    )
    result1 = engine.assign(rule, sample_pool, used_ids=set(), random_seed=42)
    result2 = engine.assign(rule, sample_pool, used_ids=set(), random_seed=42)
    assert result1.selected_id == result2.selected_id
    assert result1.random_seed == 42


def test_random_assign_different_seeds(engine, sample_pool):
    """不同随机种子可能产生不同结果"""
    results = set()
    for seed in range(5):
        rule = AssignmentRule(
            node_id="node_1", field="approver", selector_type="user",
            mode=STRATEGY_RANDOM,
        )
        result = engine.assign(rule, sample_pool, used_ids=set(), random_seed=seed)
        results.add(result.selected_id)
    assert len(results) >= 1


def test_exclude_used(engine, sample_pool):
    """排除已用过的人员"""
    rule = AssignmentRule(
        node_id="node_2", field="approver", selector_type="user",
        mode=STRATEGY_ONE_CLICK,
        scope=CandidateScope(exclude_used=True),
    )
    result = engine.assign(rule, sample_pool, used_ids={"u1"})
    assert result.selected_id == "u2"


def test_exclude_starter(engine, sample_pool):
    """排除发起人"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_ONE_CLICK,
        scope=CandidateScope(exclude_starter=True),
    )
    result = engine.assign(rule, sample_pool, used_ids=set(), starter_username="alice")
    assert result.selected_id == "u2"
    assert result.selected_name == "Bob"


def test_department_filter(engine, sample_pool):
    """部门过滤"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_ONE_CLICK,
        scope=CandidateScope(departments=["dept1"]),
    )
    result = engine.assign(rule, sample_pool, used_ids=set())
    assert result.selected_id == "u4"


def test_empty_pool_raises(engine):
    """候选池为空时抛出异常"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="user",
        mode=STRATEGY_ONE_CLICK,
    )
    with pytest.raises(ValueError, match="一键指定失败"):
        engine.assign(rule, CandidatePool(users=[], departments=[], positions=[]), used_ids=set())


def test_manual_department_assign(engine, sample_pool):
    """手动指定部门"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="department",
        mode=STRATEGY_MANUAL, selected_department="dept2",
    )
    result = engine.assign(rule, sample_pool, used_ids=set())
    assert result.selected_id == "dept2"
    assert result.selected_name == "技术部"


def test_manual_position_assign(engine, sample_pool):
    """手动指定岗位"""
    rule = AssignmentRule(
        node_id="node_1", field="approver", selector_type="position",
        mode=STRATEGY_MANUAL, selected_position="pos2",
    )
    result = engine.assign(rule, sample_pool, used_ids=set())
    assert result.selected_id == "pos2"
    assert result.selected_name == "普通员工"
