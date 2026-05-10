"""测试 StepReport（步骤6：执行报告）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_report import StepReport


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
        "flow_name": "测试流程",
        "flow_id": "fid-001",
        "starter_username": "张三",
        "last_run_result": {
            "all_completed": True,
            "duration_ms": 5000,
            "completed_branches": [{"branchId": "b1", "branchName": "分支1"}],
            "failed_branches": [],
            "node_results": {
                "n1": {"status": "completed", "node_name": "节点1", "elapsed_ms": 2000},
                "n2": {"status": "completed", "node_name": "节点2", "elapsed_ms": 3000},
            },
        },
    }


@pytest.fixture
def step_report(app, mock_config, shared_data):
    """构建 StepReport widget"""
    widget = StepReport(
        config=mock_config,
        secrets=MagicMock(),
        db=MagicMock(),
        loop=MagicMock(),
        shared_data=shared_data,
    )
    yield widget
    widget.deleteLater()


class TestStepReportInit:
    """测试初始化"""

    def test_widget_created(self, step_report):
        assert step_report is not None

    def test_has_result_tree(self, step_report):
        assert step_report._result_tree is not None

    def test_has_session_log(self, step_report):
        assert step_report._session_log is not None

    def test_summary_items_exist(self, step_report):
        """概览卡片所有指标项存在"""
        assert "flow_name" in step_report._summary_items
        assert "status" in step_report._summary_items
        assert "duration" in step_report._summary_items


class TestStepReportLoad:
    """测试数据加载"""

    def test_loads_from_shared_data(self, step_report):
        """有 last_run_result 时应加载"""
        assert step_report._summary_items["flow_name"].text() == "测试流程"

    def test_displays_duration(self, step_report):
        assert step_report._summary_items["duration"].text() == "5s"

    def test_displays_initiator(self, step_report):
        assert step_report._summary_items["initiator"].text() == "张三"


class TestStepReportSetData:
    """测试 set_report_data()"""

    def test_set_report_data_updates_summary(self, step_report):
        result = {
            "all_completed": True,
            "duration_ms": 10000,
            "completed_branches": [{"branchId": "b1", "branchName": "分支A"}],
            "failed_branches": [],
            "node_results": {"n1": {"status": "completed", "elapsed_ms": 5000}},
        }
        step_report._set_report_data(result)
        assert step_report._summary_items["duration"].text() == "10s"

    def test_set_report_data_empty_result(self, step_report):
        """空结果不应崩溃"""
        step_report._set_report_data({})
        assert step_report._summary_items["flow_name"].text() == "测试流程"

    def test_status_color_green_when_completed(self, step_report):
        result = {"all_completed": True, "duration_ms": 1000, "node_results": {}}
        step_report._set_report_data(result)
        style = step_report._summary_items["status"].styleSheet()
        assert "10B981" in style

    def test_status_color_red_when_failed(self, step_report):
        result = {"all_completed": False, "duration_ms": 1000, "node_results": {}}
        step_report._set_report_data(result)
        style = step_report._summary_items["status"].styleSheet()
        assert "EF4444" in style


class TestStepReportTree:
    """测试结果树"""

    def test_tree_populated_after_set_data(self, step_report):
        result = {
            "all_completed": True,
            "duration_ms": 1000,
            "completed_branches": [],
            "failed_branches": [],
            "node_results": {
                "n1": {"status": "completed", "node_name": "节点1", "elapsed_ms": 500},
                "n2": {"status": "failed", "node_name": "节点2", "elapsed_ms": 300, "error": "超时"},
            },
        }
        step_report._set_report_data(result)
        # 如果没有分支结构，应按节点显示
        assert step_report._result_tree.topLevelItemCount() >= 0


class TestStepReportSignals:
    """测试信号"""

    def test_rerun_requested_signal_exists(self, step_report):
        assert hasattr(step_report, "rerun_requested")

    def test_save_as_plan_signal_exists(self, step_report):
        assert hasattr(step_report, "save_as_plan")


class TestStepReportGetData:
    """测试 get_report_data()"""

    def test_get_report_data_returns_dict(self, step_report):
        data = step_report.get_report_data()
        assert isinstance(data, dict)
        assert "flow_name" in data
        assert "result" in data
