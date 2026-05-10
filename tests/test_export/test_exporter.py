"""测试 ReportExporter"""
import pytest
from workflow_test_desktop.core.export.exporter import ReportExporter
from workflow_test_desktop.core.export.templates import (
    build_summary_item, build_node_item, build_log_entry,
)


def test_build_summary_item():
    """测试摘要项生成"""
    html = build_summary_item("流程名", "付款审批")
    assert "流程名" in html
    assert "付款审批" in html


def test_build_node_item():
    """测试节点项生成"""
    html = build_node_item("部门审批", "completed", 350)
    assert "部门审批" in html
    assert "350ms" in html
    assert "completed" in html


def test_build_node_item_failed():
    """测试失败节点"""
    html = build_node_item("财务复核", "failed", 120)
    assert "failed" in html
    assert "120ms" in html


def test_build_log_entry():
    """测试会话日志条目"""
    html = build_log_entry("14:30:05", "user1", "login", "首次登录")
    assert "14:30:05" in html
    assert "user1" in html
    assert "login" in html
    assert "首次登录" in html


def test_build_summary():
    """测试摘要生成"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    data = {
        "run": {
            "flow_id": "test_flow",
            "status": "completed",
            "started_at": "2026-05-10T10:00:00",
            "finished_at": "2026-05-10T10:00:10",
            "summary": '{"starter": "user1"}',
        },
        "flow_id": "test_flow",
        "http_logs": [
            {"direction": "request", "method": "POST", "step_name": "submit"},
            {"direction": "response", "status_code": 200, "step_name": "submit"},
        ],
        "session_logs": [],
    }
    summary = exporter._build_summary(data)
    assert "test_flow" in summary
    assert "completed" in summary
    assert "10s" in summary


def test_build_branch_details():
    """测试分支详情生成"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    data = {
        "http_logs": [
            {"direction": "request", "method": "POST", "url": "/submit", "step_name": "submit", "duration_ms": 50},
            {"direction": "response", "status_code": 200, "step_name": "submit", "duration_ms": 50},
        ],
    }
    details = exporter._build_branch_details(data)
    assert "submit" in details
    assert "completed" in details


def test_build_session_log():
    """测试会话日志生成"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    data = {
        "session_logs": [
            {"created_at": "2026-05-10T14:30:05", "username": "user1", "action": "login", "reason": "首次登录"},
        ],
    }
    log = exporter._build_session_log(data)
    assert "user1" in log
    assert "login" in log
    assert "14:30:05" in log


def test_build_session_log_empty():
    """空会话日志"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    log = exporter._build_session_log({})
    assert "无会话记录" in log


def test_build_summary_with_no_timing():
    """无时间数据时摘要正常"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    data = {
        "run": {"status": "running"},
        "flow_id": "flow_xyz",
        "http_logs": [],
        "session_logs": [],
    }
    summary = exporter._build_summary(data)
    assert "flow_xyz" in summary
    assert "--" in summary


def test_build_branch_details_empty():
    """空 HTTP 日志"""
    from unittest.mock import MagicMock
    exporter = ReportExporter(MagicMock())
    details = exporter._build_branch_details({"http_logs": []})
    assert "无执行记录" in details
