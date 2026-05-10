"""测试 Database 层"""
import pytest
import pytest_asyncio
from pathlib import Path
from workflow_test_desktop.core.storage.database import DBManager, get_db


@pytest_asyncio.fixture
async def db_path(tmp_path):
    path = tmp_path / "test.db"
    yield path
    # cleanup
    if path.exists():
        path.unlink()


@pytest.mark.asyncio
async def test_db_manager_init_creates_tables(db_path):
    """测试 DBManager 初始化时创建表"""
    async with DBManager(db_path) as db:
        # 表已创建，查询应该成功（无报错即通过）
        rows = await db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [r["name"] for r in rows]
        assert "runs" in table_names
        assert "http_logs" in table_names


@pytest.mark.asyncio
async def test_db_manager_insert_run(db_path):
    """测试插入 run 记录"""
    async with DBManager(db_path) as db:
        await db.execute(
            """INSERT INTO runs (flow_id, started_at, finished_at, status, summary)
               VALUES (:flow_id, :started_at, :finished_at, :status, :summary)""",
            {
                "flow_id": "flow_001",
                "started_at": "2025-01-01T10:00:00",
                "finished_at": "2025-01-01T10:01:00",
                "status": "success",
                "summary": '{"steps": 3}',
            },
        )
        rows = await db.fetchall("SELECT * FROM runs WHERE flow_id = :id", {"id": "flow_001"})
        assert len(rows) == 1
        assert rows[0]["flow_id"] == "flow_001"
        assert rows[0]["status"] == "success"


@pytest.mark.asyncio
async def test_db_manager_insert_http_log(db_path):
    """测试插入 HTTP 日志（先插入 run 满足 FK）"""
    async with DBManager(db_path) as db:
        # 先插入 run 记录
        await db.execute(
            "INSERT INTO runs (flow_id, started_at) VALUES (:flow_id, :started_at)",
            {"flow_id": "flow_test", "started_at": "2025-01-01T10:00:00"},
        )
        await db.execute(
            """INSERT INTO http_logs (run_id, step_name, direction, method, url, params, headers, status_code, body_preview, duration_ms)
               VALUES (:run_id, :step_name, :direction, :method, :url, :params, :headers, :status_code, :body_preview, :duration_ms)""",
            {
                "run_id": 1,
                "step_name": "login",
                "direction": "request",
                "method": "POST",
                "url": "https://api.example.com/login",
                "params": '{"password": "supersecret"}',
                "headers": '{"Authorization": "Bearer xxx"}',
                "status_code": None,
                "body_preview": None,
                "duration_ms": None,
            },
        )
        rows = await db.fetchall("SELECT * FROM http_logs WHERE step_name = :name", {"name": "login"})
        assert len(rows) == 1
        assert rows[0]["run_id"] == 1
        assert rows[0]["direction"] == "request"


@pytest.mark.asyncio
async def test_get_db_singleton(db_path):
    """测试 get_db 返回同一实例"""
    db1 = await get_db(db_path)
    db2 = await get_db(db_path)
    assert db1 is db2
