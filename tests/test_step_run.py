"""测试 StepRun（步骤5：运行监控）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_run import StepRun


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
    return {
        "flow_id": "test-flow-001",
        "flow_name": "测试流程",
        "_flow_detail": {
            "flowNodeList": [
                {"nodeId": "n1", "nodeName": "节点1", "nodeType": "APPROVAL", "branchId": "b1"},
                {"nodeId": "n2", "nodeName": "节点2", "nodeType": "APPROVAL", "branchId": "b1"},
            ],
            "flowBranchList": [
                {"branchId": "b1", "branchName": "分支1"},
            ],
        },
    }


@pytest.fixture
def step_run(app, mock_config, shared_data):
    """构建 StepRun widget"""
    with patch("workflow_test_desktop.ui.steps.step_run.QTimer.singleShot"):
        widget = StepRun(
            config=mock_config,
            secrets=MagicMock(),
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared_data,
        )
    yield widget
    widget.deleteLater()


class TestStepRunInit:
    """测试初始化"""

    def test_widget_created(self, step_run):
        assert step_run is not None

    def test_has_progress_bar(self, step_run):
        assert step_run._progress_bar is not None

    def test_has_start_button(self, step_run):
        assert step_run._btn_start is not None
        assert step_run._btn_start.isEnabled()

    def test_pause_and_stop_disabled_initially(self, step_run):
        assert not step_run._btn_pause.isEnabled()
        assert not step_run._btn_stop.isEnabled()

    def test_has_tree(self, step_run):
        assert step_run._branch_tree is not None


class TestStepRunTreeInit:
    """测试树初始化"""

    def test_tree_populated_from_shared_data(self, step_run):
        """从 shared_data 加载时应显示节点"""
        root_count = step_run._branch_tree.topLevelItemCount()
        # 至少应该有 1 个分支
        assert root_count >= 1


class TestStepRunControls:
    """测试控制按钮"""

    def test_start_sets_running_state(self, step_run):
        step_run._on_start()
        assert step_run._is_running is True
        assert not step_run._btn_start.isEnabled()
        assert step_run._btn_pause.isEnabled()
        assert step_run._btn_stop.isEnabled()

    def test_pause_toggles_paused_state(self, step_run):
        step_run._on_start()
        step_run._on_pause()
        assert step_run._is_paused is True
        assert step_run._btn_pause.text() == "▶ 继续"

    def test_resume_after_pause(self, step_run):
        step_run._on_start()
        step_run._on_pause()
        step_run._on_pause()
        assert step_run._is_paused is False
        assert step_run._btn_pause.text() == "⏸ 暂停"

    def test_stop_resets_state(self, step_run):
        step_run._on_start()
        step_run._on_stop()
        assert step_run._is_running is False
        assert step_run._btn_start.isEnabled()
        assert not step_run._btn_pause.isEnabled()
        assert not step_run._btn_stop.isEnabled()


class TestStepRunResult:
    """测试 set_result()"""

    def test_set_result_updates_status(self, step_run):
        result = {
            "all_completed": True,
            "duration_ms": 5000,
            "completed_branches": [{"branchId": "b1", "branchName": "分支1"}],
            "failed_branches": [],
            "node_results": {
                "n1": {"status": "completed", "node_name": "节点1", "elapsed_ms": 2000},
                "n2": {"status": "completed", "node_name": "节点2", "elapsed_ms": 3000},
            },
        }
        step_run.set_result(result)
        assert step_run._btn_start.isEnabled()

    def test_set_result_sets_progress_to_100(self, step_run):
        # shared_data fixture has 2 nodes in _flow_detail
        # If we pass node_results for all of them, progress reaches 100
        result = {
            "all_completed": True,
            "duration_ms": 1000,
            "node_results": {
                "n1": {"status": "completed", "node_name": "节点1", "elapsed_ms": 500},
                "n2": {"status": "completed", "node_name": "节点2", "elapsed_ms": 500},
            },
        }
        step_run.set_result(result)
        assert step_run._progress_bar.value() == 100

    def test_set_result_stores_in_shared_data(self, step_run, shared_data):
        result = {"all_completed": True, "duration_ms": 1000, "node_results": {}}
        step_run.set_result(result)
        assert "last_run_result" in shared_data


class TestStepRunSignals:
    """测试信号"""

    def test_execution_completed_signal_emitted(self, step_run):
        emitted = []

        def handler(r):
            emitted.append(r)

        step_run.execution_completed.connect(handler)
        result = {"all_completed": True, "duration_ms": 1000, "node_results": {}}
        step_run.set_result(result)
        assert len(emitted) == 1
        assert emitted[0]["all_completed"] is True
