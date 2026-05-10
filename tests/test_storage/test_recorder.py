"""测试 RunRecorder（唯一写入接口）"""
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import MagicMock
from workflow_test_desktop.core.storage.recorder import RunRecorder


@pytest_asyncio.fixture
async def db_path(tmp_path):
    path = tmp_path / "test_runs.db"
    yield path
    if path.exists():
        path.unlink()


@pytest.mark.asyncio
async def test_recorder_start_run(db_path):
    """测试启动一次运行"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    run_id = await recorder.start_run(flow_id="flow_test", plan={})
    assert isinstance(run_id, int)
    assert run_id > 0


@pytest.mark.asyncio
async def test_recorder_end_run(db_path):
    """测试结束运行"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    run_id = await recorder.start_run(flow_id="flow_test", plan={})
    await recorder.end_run(run_id, status="success")
    # 验证 status 更新
    rows = await db.fetchall("SELECT * FROM runs WHERE id = :id", {"id": run_id})
    assert rows[0]["status"] == "success"
    assert rows[0]["finished_at"] is not None


@pytest.mark.asyncio
async def test_recorder_log_request(db_path):
    """测试记录 HTTP 请求（敏感字段必须脱敏）"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    run_id = await recorder.start_run(flow_id="flow_test", plan={})
    await recorder.log_request(
        run_id=run_id,
        step_name="login",
        method="POST",
        url="https://api.example.com/login",
        params={"username": "admin", "password": "secret123"},
        headers={"Authorization": "Bearer my_token"},
    )
    rows = await db.fetchall("SELECT * FROM http_logs WHERE run_id = :rid", {"rid": run_id})
    assert len(rows) == 1
    assert rows[0]["step_name"] == "login"
    assert "secret123" not in rows[0]["params"]
    assert "my_token" not in rows[0]["headers"]


@pytest.mark.asyncio
async def test_recorder_log_response(db_path):
    """测试记录 HTTP 响应（敏感字段必须脱敏）"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    run_id = await recorder.start_run(flow_id="flow_test", plan={})
    await recorder.log_request(run_id, "login", "POST", "https://api.example.com/login", {}, {})
    await recorder.log_response(
        run_id=run_id,
        step_name="login",
        status_code=200,
        body_preview='{"token": "jwt_abc123", "sid": "session_xyz"}',
        duration_ms=150,
    )
    rows = await db.fetchall("SELECT * FROM http_logs WHERE run_id = :rid AND direction = 'response'", {"rid": run_id})
    assert len(rows) == 1
    assert rows[0]["status_code"] == 200
    assert "jwt_abc123" not in rows[0]["body_preview"]
    assert "session_xyz" not in rows[0]["body_preview"]


@pytest.mark.asyncio
async def test_recorder_end_run_with_error(db_path):
    """测试错误状态"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    run_id = await recorder.start_run(flow_id="flow_fail", plan={})
    await recorder.end_run(run_id, status="failed", error_message="Network timeout")
    rows = await db.fetchall("SELECT * FROM runs WHERE id = :id", {"id": run_id})
    assert rows[0]["status"] == "failed"
    assert rows[0]["error_message"] == "Network timeout"


@pytest.mark.asyncio
async def test_recorder_query_runs(db_path):
    """测试查询运行列表"""
    from workflow_test_desktop.core.storage.database import get_db
    db = await get_db(db_path)
    recorder = RunRecorder(db)
    await recorder.start_run(flow_id="flow_1", plan={})
    await recorder.start_run(flow_id="flow_2", plan={})
    await recorder.end_run(1, status="success")
    runs = await recorder.query_runs(limit=10)
    assert len(runs) == 2
    # 最新的在前面
    assert runs[0]["id"] == 2
    assert runs[1]["id"] == 1
