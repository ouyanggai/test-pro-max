"""Database layer: aiosqlite 异步封装"""
from __future__ import annotations

import aiosqlite
from pathlib import Path
from typing import Any


_db_instance: aiosqlite.Connection | None = None
_db_wrapper: "_DBWrapper | None" = None
_db_path: Path | None = None


class DBManager:
    """aiosqlite 异步上下文管理器"""

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> DBManager:
        self._conn = await aiosqlite.connect(str(self._db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn:
            await self._conn.close()

    async def _create_tables(self) -> None:
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT DEFAULT 'running',
                summary TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS http_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                step_name TEXT,
                direction TEXT NOT NULL,
                method TEXT,
                url TEXT,
                params TEXT,
                headers TEXT,
                status_code INTEGER,
                body_preview TEXT,
                duration_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)
        await self._conn.commit()

    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> aiosqlite.Cursor:
        return await self._conn.execute(sql, params or {})

    async def fetchall(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(sql, params or {})
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchone(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        cursor = await self._conn.execute(sql, params or {})
        row = await cursor.fetchone()
        return dict(row) if row else None


class _DBWrapper:
    """给 aiosqlite.Connection 包一层，提供 fetchall/fetchone"""
    __slots__ = ("_conn",)

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def execute(self, sql: str, params: dict[str, Any] | None = None):
        return await self._conn.execute(sql, params or {})

    async def fetchall(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(sql, params or {})
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchone(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        cursor = await self._conn.execute(sql, params or {})
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_db(db_path: str | Path) -> _DBWrapper:
    """单例 DB 连接（首次连接时建表），返回带 fetchall/fetchone 的包装器"""
    global _db_instance, _db_wrapper, _db_path
    path = Path(db_path)
    if _db_instance is None or _db_path != path:
        conn = await aiosqlite.connect(str(path))
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT DEFAULT 'running',
                summary TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS http_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                step_name TEXT,
                direction TEXT NOT NULL,
                method TEXT,
                url TEXT,
                params TEXT,
                headers TEXT,
                status_code INTEGER,
                body_preview TEXT,
                duration_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)
        _db_instance = conn
        _db_path = path
        _db_wrapper = _DBWrapper(_db_instance)
    return _db_wrapper
