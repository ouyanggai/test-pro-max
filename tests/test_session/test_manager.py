"""测试 SessionManager"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from workflow_test_desktop.core.session.manager import SessionManager, SessionManagerError
from workflow_test_desktop.core.session.lease import SessionLease


@pytest.fixture
def mock_secrets():
    mock = MagicMock()
    mock.get = MagicMock(return_value="test_password")
    return mock


@pytest.fixture
def mock_login_func():
    call_count = {"count": 0}

    async def login(env_id, login_type, username, password):
        call_count["count"] += 1
        # 模拟真实 API 响应：{code, message, data: {sid, ...}}
        return {
            "code": 0,
            "message": "ok",
            "data": {"sid": f"sid_{username}_{call_count['count']}", "expires_in": 3600},
        }
    return AsyncMock(side_effect=login)


@pytest.fixture
def session_manager(mock_secrets, mock_login_func):
    SessionManager.reset()
    sm = SessionManager(secret_provider=mock_secrets, login_func=mock_login_func)
    SessionManager.set_instance(sm)
    return sm


@pytest.fixture
def log_entries():
    entries = []

    def callback(exec_id, env_id, login_type, username, gen, action, reason):
        entries.append((exec_id, env_id, login_type, username, gen, action, reason))
    return entries, callback


@pytest.mark.asyncio
async def test_get_session_first_time(session_manager, log_entries):
    """首次获取会话应触发登录"""
    entries, callback = log_entries
    session_manager.set_log_callback(callback)

    lease = await session_manager.get_session("test", "user_login", "user1")

    assert lease.sid == "sid_user1_1"
    assert lease.username == "user1"
    assert lease.generation == 1
    assert len(entries) == 1
    assert entries[0][6] == "首次登录"


@pytest.mark.asyncio
async def test_get_session_cache_hit(session_manager):
    """缓存命中时不应重新登录"""
    lease1 = await session_manager.get_session("test", "user_login", "user2")
    lease2 = await session_manager.get_session("test", "user_login", "user2")
    assert lease1 is lease2


@pytest.mark.asyncio
async def test_concurrent_same_user_one_login(session_manager):
    """同一账号并发请求只登录一次"""
    results = await asyncio.gather(
        session_manager.get_session("test", "user_login", "user3"),
        session_manager.get_session("test", "user_login", "user3"),
        session_manager.get_session("test", "user_login", "user3"),
    )
    assert results[0] is results[1] is results[2]


@pytest.mark.asyncio
async def test_different_users_different_sessions(session_manager):
    """不同账号有不同 SID"""
    lease1 = await session_manager.get_session("test", "user_login", "alice")
    lease2 = await session_manager.get_session("test", "user_login", "bob")
    assert lease1.sid == "sid_alice_1"
    assert lease2.sid == "sid_bob_2"
    assert lease1.sid != lease2.sid


@pytest.mark.asyncio
async def test_mark_invalid_triggers_relogin(session_manager, mock_login_func):
    """mark_invalid 后下次 get_session 应重新登录"""
    lease1 = await session_manager.get_session("test", "user_login", "user4")
    assert lease1.generation == 1
    sid1 = lease1.sid

    await session_manager.mark_invalid(lease1, execution_id=0, reason="SID 失效")

    lease2 = await session_manager.get_session("test", "user_login", "user4")
    assert lease2.generation == 2
    # generation 递增 + 登录被重新调用 → SID 应该变化
    # mock 返回的 SID 包含 call_count，每次 login 调用递增
    assert lease2.sid != sid1, f"SID should change after relogin: {lease2.sid} vs {sid1}"


@pytest.mark.asyncio
async def test_singleton_access(session_manager):
    """get_instance 返回单例"""
    instance = SessionManager.get_instance()
    assert instance is session_manager


@pytest.mark.asyncio
async def test_refresh_if_needed_generation_update(session_manager):
    """refresh_if_needed 检测到 generation 更新时返回新 lease"""
    lease1 = await session_manager.get_session("test", "user_login", "user5")
    assert lease1.generation == 1

    # 手动更新 cache 中的 generation（模拟其他协程已重登）
    new_lease = SessionLease(
        env_id="test", login_type="user_login", username="user5",
        sid="new_sid", generation=2, expires_at=None,
    )
    key = session_manager._cache_key("test", "user_login", "user5")
    session_manager._cache[key] = new_lease

    lease2 = await session_manager.refresh_if_needed(lease1, execution_id=0, reason="test")
    assert lease2.generation == 2
    assert lease2.sid == "new_sid"
