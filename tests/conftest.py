"""pytest-qt fixture + qasync 事件循环支持"""
from __future__ import annotations

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()


@pytest.fixture
def mock_env_file(tmp_path: Path, monkeypatch):
    """创建临时 .env 文件供测试用"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GATEWAY_URL=https://dev.example.com\n"
        "LOGIN_PATH=/api/auth/login\n"
        "TEST_USERNAME=testuser\n"
    )
    monkeypatch.setenv("WORKFLOW_ENV_FILE", str(env_file))
    return env_file


@pytest.fixture
def mock_secret_provider():
    """模拟 SecretProvider"""
    mock = MagicMock()
    mock.get_password = MagicMock(return_value="mock_password_123")
    mock.get_token = MagicMock(return_value="mock_token_abc")
    mock.get_sid = MagicMock(return_value=None)
    return mock


@pytest.fixture
def mock_session_lease():
    """模拟 SessionLease（依赖 Task 3 的 SessionLease 类）"""
    # 延迟导入，确保 Task 3 执行后可用
    try:
        from workflow_test_desktop.core.session.lease import SessionLease
        return SessionLease(
            env_id="test",
            login_type="user_login",
            username="testuser",
            sid="mock_sid_xyz",
            generation=1,
            expires_at=None,
        )
    except ImportError:
        # Task 3 未执行前，返回 MagicMock
        return MagicMock(
            env_id="test",
            login_type="user_login",
            username="testuser",
            sid="mock_sid_xyz",
            generation=1,
            expires_at=None,
        )


@pytest.fixture
def mock_http_client():
    """模拟 httpx.AsyncClient"""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def sample_run_plan_data():
    """示例 RunPlan 数据"""
    return {
        "run_plan_version": 1,
        "name": "付款流程回归-默认场景",
        "environment": {"env_id": "test", "gateway_ref": "config.env.GATEWAY_URL"},
        "starter": {"mode": "default_super_account", "user": {"username": "欧阳改", "display_name": "欧阳改"}},
        "flow": {"flow_id": "flow_xxx", "flow_name": "付款审批流程"},
        "form_data": {"strategy": "fixed", "fields": {"amount": 12000, "reason": "自动化回归测试"}},
        "assignments": {"default_policy": "manual_first", "random_seed": 20260509, "rules": []},
        "branch_execution": {"mode": "parallel_branches", "max_branch_concurrency": 5, "failure_policy": "wait_all_then_fail"},
        "session_policy": {"sid_reuse": True, "relogin": "only_when_missing_or_expired", "duplicate_login_guard": True},
    }
