"""测试 StepNodes（步骤4：节点配置）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_nodes import StepNodes, ASSIGNMENT_MODES


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    yield qapp


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get = MagicMock(side_effect=lambda k, d=None: {
        "GATEWAY_URL": "https://dev.example.com",
    }.get(k, d))
    return config


@pytest.fixture
def shared_data():
    return {"flow_id": "test-flow-001"}


@pytest.fixture
def step_nodes(app, mock_config, shared_data):
    """构建 StepNodes widget"""
    with patch("workflow_test_desktop.ui.steps.step_nodes.QTimer.singleShot"):
        widget = StepNodes(
            config=mock_config,
            secrets=MagicMock(),
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared_data,
        )
    yield widget
    widget.deleteLater()


class TestStepNodesInit:
    """测试初始化"""

    def test_widget_created(self, step_nodes):
        assert step_nodes is not None

    def test_has_table(self, step_nodes):
        assert step_nodes._table is not None
        assert step_nodes._table.columnCount() == 6

    def test_assignment_modes_defined(self):
        """ASSIGNMENT_MODES 应包含所有需要的模式"""
        modes = [m[1] for m in ASSIGNMENT_MODES]
        assert "manual" in modes
        assert "one_click" in modes
        assert "random" in modes


class TestStepNodesSetNodes:
    """测试节点加载"""

    def test_set_nodes_populates_table(self, step_nodes):
        nodes = [
            {
                "nodeId": "n1",
                "nodeName": "主管审批",
                "nodeType": "APPROVAL",
                "auditWay": "SCRAMBLE",
                "flowNodeUserList": [],
            },
            {
                "nodeId": "n2",
                "nodeName": "经理审批",
                "nodeType": "APPROVAL",
                "auditWay": "COUNTERSIGN",
                "flowNodeUserList": [],
            },
        ]
        step_nodes._set_nodes(nodes)
        assert step_nodes._table.rowCount() == 2
        assert step_nodes._table.item(0, 1).text() == "主管审批"
        assert step_nodes._table.item(1, 1).text() == "经理审批"

    def test_set_nodes_presets_assignment_mode(self, step_nodes):
        """auditType=assign 应预选「一键指定」"""
        nodes = [
            {
                "nodeId": "n1",
                "nodeName": "主管审批",
                "nodeType": "APPROVAL",
                "auditWay": "SCRAMBLE",
                "auditType": "ASSIGN",
                "flowNodeUserList": [],
            },
        ]
        step_nodes._set_nodes(nodes)
        combo = step_nodes._table.cellWidget(0, 4)
        assert combo.currentData() == "one_click"

    def test_set_nodes_displays_audit_way(self, step_nodes):
        nodes = [
            {
                "nodeId": "n1",
                "nodeName": "审批",
                "nodeType": "APPROVAL",
                "auditWay": "SCRAMBLE",
                "flowNodeUserList": [],
            },
        ]
        step_nodes._set_nodes(nodes)
        assert step_nodes._table.item(0, 3).text() == "竞签"

    def test_set_nodes_combo_count(self, step_nodes):
        nodes = [{"nodeId": "n1", "nodeName": "A", "nodeType": "START", "flowNodeUserList": []}]
        step_nodes._set_nodes(nodes)
        combo = step_nodes._table.cellWidget(0, 4)
        assert combo.count() == len(ASSIGNMENT_MODES)


class TestStepNodesValidation:
    """测试 validate()"""

    def test_validate_fails_when_manual_selected(self, step_nodes):
        nodes = [{"nodeId": "n1", "nodeName": "Test", "nodeType": "APPROVAL", "auditWay": "", "flowNodeUserList": []}]
        step_nodes._set_nodes(nodes)
        # 默认是 manual
        ok, msg = step_nodes.validate()
        assert ok is False
        assert "Test" in msg

    def test_validate_passes_when_one_click_selected(self, step_nodes):
        nodes = [{"nodeId": "n1", "nodeName": "Test", "nodeType": "APPROVAL", "auditWay": "", "flowNodeUserList": []}]
        step_nodes._set_nodes(nodes)
        combo = step_nodes._table.cellWidget(0, 4)
        for idx in range(combo.count()):
            if combo.itemData(idx) == "one_click":
                combo.setCurrentIndex(idx)
                break
        ok, msg = step_nodes.validate()
        assert ok is True

    def test_validate_passes_when_random_selected(self, step_nodes):
        nodes = [{"nodeId": "n1", "nodeName": "Test", "nodeType": "APPROVAL", "auditWay": "", "flowNodeUserList": []}]
        step_nodes._set_nodes(nodes)
        combo = step_nodes._table.cellWidget(0, 4)
        for idx in range(combo.count()):
            if combo.itemData(idx) == "random":
                combo.setCurrentIndex(idx)
                break
        ok, msg = step_nodes.validate()
        assert ok is True


class TestStepNodesActions:
    """测试操作按钮"""

    def test_one_click_assign_sets_all_to_one_click(self, step_nodes):
        nodes = [
            {"nodeId": "n1", "nodeName": "A", "nodeType": "START", "flowNodeUserList": []},
            {"nodeId": "n2", "nodeName": "B", "nodeType": "START", "flowNodeUserList": []},
        ]
        step_nodes._set_nodes(nodes)
        step_nodes._on_one_click_assign()
        for i in range(2):
            assert step_nodes._table.cellWidget(i, 4).currentData() == "one_click"

    def test_reset_all_restores_manual(self, step_nodes):
        nodes = [{"nodeId": "n1", "nodeName": "A", "nodeType": "START", "flowNodeUserList": []}]
        step_nodes._set_nodes(nodes)
        step_nodes._on_one_click_assign()
        step_nodes._on_reset_all()
        assert step_nodes._table.cellWidget(0, 4).currentData() == "manual"


class TestStepNodesExport:
    """测试导出指派规则"""

    def test_get_assignment_rules_returns_list(self, step_nodes):
        nodes = [
            {
                "nodeId": "n1",
                "nodeName": "主管审批",
                "nodeType": "APPROVAL",
                "auditWay": "SCRAMBLE",
                "flowNodeUserList": [
                    {"userId": "u1", "userName": "张三"},
                    {"userId": "u2", "userName": "李四"},
                ],
            },
        ]
        step_nodes._set_nodes(nodes)
        rules = step_nodes.get_assignment_rules()
        assert isinstance(rules, list)
        assert len(rules) == 1
        assert rules[0]["node_id"] == "n1"
        assert rules[0]["node_name"] == "主管审批"
        assert len(rules[0]["preassigned_users"]) == 2
