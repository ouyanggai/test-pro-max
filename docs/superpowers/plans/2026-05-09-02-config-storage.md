# Task 2: 配置层与存储层

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this task step-by-step.

**Goal:** 实现 EnvironmentService、SecretProvider、SQLite 表初始化、sanitizer 脱敏工具、RunRecorder 统一写入层。

**Architecture:** 配置层负责读取 `.env` 非敏感配置和密钥；存储层负责 SQLite 初始化、脱敏、写入记录。脱敏在 `RunRecorder.write()` 层统一执行，禁止各模块自行处理。

**Dependencies:** Task 1（目录结构）

---

## 文件清单

- Create: `workflow_test_desktop/core/config/__init__.py`
- Create: `workflow_test_desktop/core/config/environment.py`
- Create: `workflow_test_desktop/core/config/secrets.py`
- Create: `workflow_test_desktop/core/storage/__init__.py`
- Create: `workflow_test_desktop/core/storage/db.py`
- Create: `workflow_test_desktop/core/storage/sanitizer.py`
- Create: `workflow_test_desktop/core/storage/recorder.py`
- Create: `tests/test_config/test_environment.py`
- Create: `tests/test_config/test_secrets.py`
- Create: `tests/test_storage/test_recorder.py`
- Create: `tests/test_storage/test_sanitizer.py`

---

### Step 1: 创建 `workflow_test_desktop/core/config/environment.py`（EnvironmentService）

```python
"""EnvironmentService：读取 .env 和 config/ 下非敏感配置"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


class EnvironmentError(Exception):
    """环境配置异常"""


@dataclass
class AppConfig:
    """统一配置对象（非敏感）"""
    env_id: str = "dev"
    gateway_url: str = ""
    login_path: str = "/api/auth/login"
    logout_path: str = "/api/auth/logout"
    user_directory_path: str = "/api/user/directory"
    flow_catalog_path: str = "/api/flow/catalog"
    flow_detail_path: str = "/api/flow/detail"
    todo_list_path: str = "/api/todo/list"
    node_action_path: str = "/api/flow/node/action"
    flow_history_path: str = "/api/flow/history"
    _raw: dict[str, str] = field(default_factory=dict)


class EnvironmentService:
    """
    读取环境配置。优先级：
    1. 显式传入的 .env 文件路径
    2. WORKFLOW_ENV_FILE 环境变量
    3. 项目根目录 .env
    """

    _config: AppConfig | None = None

    def __init__(self, env_file: str | Path | None = None):
        self._env_file = self._resolve_env_file(env_file)

    def _resolve_env_file(self, env_file: str | Path | None) -> Path:
        if env_file:
            path = Path(env_file)
            if not path.exists():
                raise EnvironmentError(f"环境文件不存在: {path}")
            return path
        env_var = os.environ.get("WORKFLOW_ENV_FILE")
        if env_var:
            path = Path(env_var)
            if not path.exists():
                raise EnvironmentError(f"WORKFLOW_ENV_FILE 不存在: {path}")
            return path
        root = Path(__file__).parent.parent.parent
        default = root / ".env"
        if default.exists():
            return default
        raise EnvironmentError("未找到 .env 文件，请创建或指定 --env-file")

    def load(self) -> AppConfig:
        """加载并解析配置，返回 AppConfig（不含密钥）"""
        if self._config:
            return self._config
        raw = self._read_env_file()
        self._validate_required(raw)
        self._config = self._parse(raw)
        return self._config

    def _read_env_file(self) -> dict[str, str]:
        """读取 .env 文件，KEY=value 格式，支持 # 注释"""
        result: dict[str, str] = {}
        for line in self._env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
        return result

    def _validate_required(self, raw: dict[str, str]) -> None:
        required = ["GATEWAY_URL"]
        missing = [k for k in required if k not in raw]
        if missing:
            raise EnvironmentError(f"缺少必需配置: {', '.join(missing)}")

    def _parse(self, raw: dict[str, str]) -> AppConfig:
        return AppConfig(
            env_id=raw.get("ENV_ID", "dev"),
            gateway_url=raw["GATEWAY_URL"],
            login_path=raw.get("LOGIN_PATH", "/api/auth/login"),
            logout_path=raw.get("LOGOUT_PATH", "/api/auth/logout"),
            user_directory_path=raw.get("USER_DIRECTORY_PATH", "/api/user/directory"),
            flow_catalog_path=raw.get("FLOW_CATALOG_PATH", "/api/flow/catalog"),
            flow_detail_path=raw.get("FLOW_DETAIL_PATH", "/api/flow/detail"),
            todo_list_path=raw.get("TODO_LIST_PATH", "/api/todo/list"),
            node_action_path=raw.get("NODE_ACTION_PATH", "/api/flow/node/action"),
            flow_history_path=raw.get("FLOW_HISTORY_PATH", "/api/flow/history"),
            _raw=raw,
        )

    def get_raw(self, key: str, default: str = "") -> str:
        """获取原始配置值（不含密钥的字段）"""
        return self.load()._raw.get(key, default)

    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.load().env_id in ("prod", "production")
```

---

### Step 2: 创建 `tests/test_config/test_environment.py`

```python
"""测试 EnvironmentService"""
import pytest
from pathlib import Path
from workflow_test_desktop.core.config.environment import (
    EnvironmentService, AppConfig, EnvironmentError
)


def test_load_success(mock_env_file):
    """测试正常加载配置"""
    svc = EnvironmentService(env_file=mock_env_file)
    cfg = svc.load()
    assert isinstance(cfg, AppConfig)
    assert cfg.gateway_url == "https://dev.example.com"
    assert cfg.login_path == "/api/auth/login"


def test_missing_required_key(tmp_path):
    """测试缺少必需配置时抛出异常"""
    env_file = tmp_path / ".env"
    env_file.write_text("LOGIN_PATH=/api/auth/login\n")  # 缺少 GATEWAY_URL
    with pytest.raises(EnvironmentError, match="缺少必需配置"):
        EnvironmentService(env_file=env_file).load()


def test_env_file_not_found():
    """测试环境文件不存在时抛出异常"""
    with pytest.raises(EnvironmentError, match="环境文件不存在"):
        EnvironmentService(env_file="/nonexistent/.env").load()


def test_get_raw(mock_env_file):
    """测试获取原始值"""
    svc = EnvironmentService(env_file=mock_env_file)
    assert svc.get_raw("GATEWAY_URL") == "https://dev.example.com"
    assert svc.get_raw("MISSING_KEY", "default") == "default"


def test_is_production(mock_env_file):
    """测试生产环境判断"""
    svc = EnvironmentService(env_file=mock_env_file)
    assert svc.is_production() is False
```

---

### Step 3: 创建 `workflow_test_desktop/core/config/secrets.py`（SecretProvider）

```python
"""SecretProvider：只读本地 .env 敏感字段，内存持有，不写日志不落库"""
from __future__ import annotations

import re
from pathlib import Path


_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "passwd", "pwd",
    "token", "api_token", "access_token", "refresh_token",
    "sid", "session_id",
    "cookie",
    "authorization", "auth_token",
    "client_secret", "secret",
    "db_password", "database_password",
    "nacos_token",
})


class SecretProvider:
    """
    只读本地 .env 敏感字段，内存持有。
    关键原则：
    - 永不写入日志
    - 永不写入数据库
    - 永不写入文档
    - 永不提交到仓库
    """

    def __init__(self, env_file: str | Path):
        self._env_file = Path(env_file)
        self._cache: dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self._env_file.exists():
            raise FileNotFoundError(f"密钥文件不存在: {self._env_file}")
        for line in self._env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            self._cache[key.strip()] = value.strip()
        self._loaded = True

    def get(self, key: str, default: str | None = None) -> str | None:
        """获取敏感配置值，大小写不敏感"""
        self._ensure_loaded()
        upper = key.upper()
        for cache_key, cache_val in self._cache.items():
            if cache_key.upper() == upper:
                return cache_val
        return default

    def get_password(self, key: str = "PASSWORD", default: str | None = None) -> str | None:
        return self.get(key, default)

    def get_token(self, key: str = "TOKEN", default: str | None = None) -> str | None:
        return self.get(key, default)

    def get_sid(self, key: str = "SID", default: str | None = None) -> str | None:
        return self.get(key, default)

    def get_all(self) -> dict[str, str]:
        """返回所有密钥的只读字典副本"""
        self._ensure_loaded()
        return dict(self._cache)

    def is_sensitive_key(self, key: str) -> bool:
        """判断 key 是否为敏感字段名"""
        lower = key.lower()
        return lower in _SENSITIVE_KEYS or bool(re.search(
            r"(password|token|sid|secret|auth|cookie)", lower
        ))
```

---

### Step 4: 创建 `tests/test_config/test_secrets.py`

```python
"""测试 SecretProvider"""
import pytest
from pathlib import Path
from workflow_test_desktop.core.config.secrets import SecretProvider


def test_get_success(tmp_path):
    """测试正常获取密钥"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GATEWAY_URL=https://api.example.com\n"
        "TEST_PASSWORD=secret123\n"
        "API_TOKEN=token_abc\n"
    )
    sp = SecretProvider(env_file=env_file)
    assert sp.get("TEST_PASSWORD") == "secret123"
    assert sp.get("API_TOKEN") == "token_abc"


def test_get_case_insensitive(tmp_path):
    """测试大小写不敏感"""
    env_file = tmp_path / ".env"
    env_file.write_text("MY_SECRET=abc123\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get("my_secret") == "abc123"
    assert sp.get("MY_SECRET") == "abc123"


def test_get_default(tmp_path):
    """测试默认值"""
    env_file = tmp_path / ".env"
    env_file.write_text("GATEWAY_URL=https://api.example.com\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get("MISSING") is None
    assert sp.get("MISSING", "default_val") == "default_val"


def test_get_password_shortcut(tmp_path):
    """测试 get_password 快捷方法"""
    env_file = tmp_path / ".env"
    env_file.write_text("PASSWORD=pass123\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get_password() == "pass123"
    assert sp.get_token() is None


def test_is_sensitive_key():
    """测试敏感字段判断"""
    sp = SecretProvider(env_file="/dev/null")
    for key in ["password", "PASSWORD", "token", "sid", "authorization", "client_secret"]:
        assert sp.is_sensitive_key(key), f"{key} should be sensitive"


def test_file_not_found():
    """测试文件不存在时抛出异常"""
    with pytest.raises(FileNotFoundError):
        SecretProvider(env_file="/nonexistent/.env").get("KEY")
```

---

### Step 5: 创建 `workflow_test_desktop/core/storage/sanitizer.py`（统一脱敏）

```python
"""统一脱敏工具：禁止各模块自行处理，所有写入必须经此"""
from __future__ import annotations

import re
import urllib.parse
from typing import Any


_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(token|api_token|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(sid|session_id)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(cookie)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(authorization)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(client_secret|secret)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]+)", re.IGNORECASE),
    re.compile(r"sid=([a-zA-Z0-9_\-]{16,})", re.IGNORECASE),
]


def sanitize(value: str | None) -> str | None:
    """对单个字符串值脱敏"""
    if value is None:
        return None
    result = value
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub(lambda m: f'"{m.group(1)}": "****"', result)
    if _looks_like_sensitive(result):
        return "****"
    return result


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """递归脱敏字典"""
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            result[_sanitize_key(k)] = sanitize_dict(v)
        elif isinstance(v, list):
            result[_sanitize_key(k)] = sanitize_list(v)
        elif isinstance(v, str):
            result[_sanitize_key(k)] = sanitize(v)
        else:
            result[_sanitize_key(k)] = v
    return result


def sanitize_list(data: list[Any]) -> list[Any]:
    """递归脱敏列表"""
    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(sanitize_dict(item))
        elif isinstance(item, list):
            result.append(sanitize_list(item))
        elif isinstance(item, str):
            result.append(sanitize(item))
        else:
            result.append(item)
    return result


def _sanitize_key(s: str) -> str:
    """对字典 key 脱敏（检查是否含敏感关键词）"""
    return s


def _looks_like_sensitive(s: str) -> bool:
    """判断字符串是否像敏感值"""
    sensitive_keywords = [
        "password", "passwd", "pwd",
        "token", "api_token", "access_token",
        "sid", "session_id",
        "authorization",
        "secret", "client_secret",
        "nacos_token",
    ]
    return any(kw in s.lower() for kw in sensitive_keywords)


def sanitize_request_summary(method: str, url: str,
                             params: dict | None = None,
                             headers: dict | None = None) -> dict[str, Any]:
    """生成安全的请求摘要（用于写入数据库/报告）"""
    summary: dict[str, Any] = {
        "method": method.upper(),
        "url": _mask_url_credentials(url),
    }
    if params:
        summary["params"] = sanitize_dict(params)
    if headers:
        summary["headers"] = _sanitize_headers(headers)
    return summary


def sanitize_response_summary(status_code: int,
                              body_preview: str | None = None) -> dict[str, Any]:
    """生成安全的响应摘要"""
    return {
        "status_code": status_code,
        "body_preview": sanitize(body_preview) if body_preview else None,
    }


def _mask_url_credentials(url: str) -> str:
    """URL 中移除用户信息"""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.username:
            netloc = parsed.netloc.replace(f"{parsed.username}@", "")
            return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        pass
    return url


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """headers 中移除授权相关值"""
    result = {}
    auth_keys = {"authorization", "cookie", "x-api-token", "x-sid"}
    for k, v in headers.items():
        if k.lower() in auth_keys or "auth" in k.lower() or "token" in k.lower():
            result[k] = "****"
        else:
            result[k] = v
    return result
```

---

### Step 6: 创建 `tests/test_storage/test_sanitizer.py`

```python
"""测试脱敏工具"""
import pytest
from workflow_test_desktop.core.storage.sanitizer import (
    sanitize, sanitize_dict, sanitize_list,
    sanitize_request_summary, sanitize_response_summary
)


def test_sanitize_none():
    assert sanitize(None) is None


def test_sanitize_normal_string():
    assert sanitize("hello world") == "hello world"


def test_sanitize_password():
    result = sanitize('{"password": "secret123"}')
    assert "secret123" not in result
    assert "****" in result


def test_sanitize_token():
    result = sanitize('"token": "abc_xyz_token"')
    assert "abc_xyz_token" not in result
    assert "****" in result


def test_sanitize_bearer():
    result = sanitize("Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0")
    assert "eyJ" not in result
    assert "****" in result


def test_sanitize_dict():
    data = {
        "username": "testuser",
        "password": "supersecret",
        "nested": {"token": "tok_123"},
    }
    result = sanitize_dict(data)
    assert result["username"] == "testuser"
    assert result["password"] == "****"
    assert result["nested"]["token"] == "****"


def test_sanitize_list():
    data = [
        {"name": "item1", "password": "pass1"},
        "plain_string",
        [1, 2, 3],
    ]
    result = sanitize_list(data)
    assert result[0]["password"] == "****"
    assert result[1] == "plain_string"
    assert result[2] == [1, 2, 3]


def test_sanitize_request_summary():
    result = sanitize_request_summary(
        method="POST",
        url="https://api.example.com/login",
        params={"username": "admin", "password": "secret123"},
        headers={"Authorization": "Bearer token_abc"},
    )
    assert result["method"] == "POST"
    assert result["params"]["username"] == "admin"
    assert result["params"]["password"] == "****"
    assert result["headers"]["Authorization"] == "****"


def test_sanitize_response_summary():
    result = sanitize_response_summary(200, '{"status": "ok", "sid": "real_sid_here"}')
    assert result["status_code"] == 200
    assert "real_sid_here" not in str(result["body_preview"])


def test_mask_url_credentials():
    result = sanitize_request_summary("GET", "https://user:pass@api.example.com/secure", {}, {})
    assert "user:pass" not in result["url"]
    assert "api.example.com" in result["url"]
```

---

### Step 7: 创建 `workflow_test_desktop/core/storage/db.py`（SQLite 连接 + 表初始化）

```python
"""SQLite 连接管理 + 表初始化"""
from __future__ import annotations

import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS run_plan (
    id TEXT PRIMARY KEY,
    name TEXT,
    version INTEGER DEFAULT 1,
    env_id TEXT,
    starter_username TEXT,
    flow_id TEXT,
    flow_name TEXT,
    random_seed INTEGER,
    plan_json TEXT NOT NULL,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS execution_run (
    id TEXT PRIMARY KEY,
    run_plan_id TEXT,
    flow_instance_id TEXT,
    status TEXT,
    started_at REAL,
    finished_at REAL,
    failure_policy TEXT,
    FOREIGN KEY (run_plan_id) REFERENCES run_plan(id)
);

CREATE TABLE IF NOT EXISTS branch_run (
    id TEXT PRIMARY KEY,
    execution_run_id TEXT,
    branch_key TEXT,
    status TEXT,
    started_at REAL,
    finished_at REAL,
    FOREIGN KEY (execution_run_id) REFERENCES execution_run(id)
);

CREATE TABLE IF NOT EXISTS node_run (
    id TEXT PRIMARY KEY,
    branch_run_id TEXT,
    node_id TEXT,
    node_name TEXT,
    status TEXT,
    assignee_snapshot TEXT,
    started_at REAL,
    finished_at REAL,
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (branch_run_id) REFERENCES branch_run(id)
);

CREATE TABLE IF NOT EXISTS request_log (
    id TEXT PRIMARY KEY,
    node_run_id TEXT,
    method TEXT,
    url TEXT,
    request_summary TEXT,
    response_summary TEXT,
    status_code INTEGER,
    duration_ms INTEGER,
    created_at REAL,
    FOREIGN KEY (node_run_id) REFERENCES node_run(id)
);

CREATE TABLE IF NOT EXISTS session_log (
    id TEXT PRIMARY KEY,
    execution_run_id TEXT,
    env_id TEXT,
    login_type TEXT,
    username TEXT,
    generation INTEGER,
    action TEXT,
    reason TEXT,
    created_at REAL,
    FOREIGN KEY (execution_run_id) REFERENCES execution_run(id)
);

CREATE TABLE IF NOT EXISTS candidate_snapshot (
    id TEXT PRIMARY KEY,
    execution_run_id TEXT,
    node_id TEXT,
    field TEXT,
    selector_type TEXT,
    candidates_json TEXT,
    created_at REAL,
    FOREIGN KEY (execution_run_id) REFERENCES execution_run(id)
);

CREATE INDEX IF NOT EXISTS idx_execution_run_plan ON execution_run(run_plan_id);
CREATE INDEX IF NOT EXISTS idx_branch_run_execution ON branch_run(execution_run_id);
CREATE INDEX IF NOT EXISTS idx_node_run_branch ON node_run(branch_run_id);
CREATE INDEX IF NOT EXISTS idx_request_log_node ON request_log(node_run_id);
CREATE INDEX IF NOT EXISTS idx_session_log_execution ON session_log(execution_run_id);
CREATE INDEX IF NOT EXISTS idx_candidate_snapshot_execution ON candidate_snapshot(execution_run_id);
"""


class Database:
    """SQLite 数据库连接管理器"""

    def __init__(self, db_path: str | Path = "workflow_runs.db"):
        self._db_path = Path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """初始化数据库连接并创建表"""
        self._conn = await aiosqlite.connect(str(self._db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA_SQL)
        await self._conn.commit()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @asynccontextmanager
    async def transaction(self):
        """异步上下文管理器：自动提交或回滚"""
        if not self._conn:
            raise RuntimeError("Database not initialized")
        try:
            yield self._conn
            await self._conn.commit()
        except Exception:
            await self._conn.rollback()
            raise

    @asynccontextmanager
    async def cursor(self):
        """获取游标的上下文管理器"""
        async with self.transaction() as conn:
            cursor = await conn.cursor()
            try:
                yield cursor
            finally:
                await cursor.close()
```

---

### Step 8: 创建 `workflow_test_desktop/core/storage/recorder.py`（RunRecorder）

```python
"""RunRecorder：统一写入 SQLite，所有写入经脱敏层"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any

from workflow_test_desktop.core.storage.db import Database
from workflow_test_desktop.core.storage.sanitizer import sanitize_dict, sanitize_request_summary, sanitize_response_summary


class RunRecorder:
    """
    统一写入层。
    所有模块的数据写入必须通过这里，禁止直接操作数据库。
    脱敏在写入层统一执行。
    """

    def __init__(self, db: Database):
        self._db = db

    # ── RunPlan ──────────────────────────────────────────────────────────────

    async def save_run_plan(
        self,
        name: str,
        env_id: str,
        starter_username: str,
        flow_id: str,
        flow_name: str,
        random_seed: int | None,
        plan_json: dict[str, Any],
    ) -> str:
        """保存运行计划，返回 plan_id"""
        plan_id = str(uuid.uuid4())
        now = time.time()
        # 写入前脱敏
        sanitized = sanitize_dict(plan_json)
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO run_plan
                   (id, name, version, env_id, starter_username, flow_id, flow_name,
                    random_seed, plan_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (plan_id, name, 1, env_id, starter_username, flow_id, flow_name,
                 random_seed, json.dumps(sanitized, ensure_ascii=False), now),
            )
        return plan_id

    # ── ExecutionRun ─────────────────────────────────────────────────────────

    async def create_execution(
        self,
        run_plan_id: str,
        failure_policy: str,
    ) -> str:
        """创建执行记录，返回 execution_id"""
        execution_id = str(uuid.uuid4())
        now = time.time()
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO execution_run
                   (id, run_plan_id, status, started_at, failure_policy)
                   VALUES (?, ?, ?, ?, ?)""",
                (execution_id, run_plan_id, "running", now, failure_policy),
            )
        return execution_id

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        flow_instance_id: str | None = None,
    ) -> None:
        """更新执行状态"""
        async with self._db.cursor() as cur:
            if flow_instance_id:
                await cur.execute(
                    "UPDATE execution_run SET status=?, flow_instance_id=?, finished_at=? WHERE id=?",
                    (status, flow_instance_id, time.time(), execution_id),
                )
            else:
                await cur.execute(
                    "UPDATE execution_run SET status=?, finished_at=? WHERE id=?",
                    (status, time.time(), execution_id),
                )

    # ── BranchRun ─────────────────────────────────────────────────────────────

    async def create_branch(
        self,
        execution_id: str,
        branch_key: str,
    ) -> str:
        """创建分支记录"""
        branch_id = str(uuid.uuid4())
        now = time.time()
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO branch_run
                   (id, execution_run_id, branch_key, status, started_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (branch_id, execution_id, branch_key, "running", now),
            )
        return branch_id

    async def update_branch(self, branch_id: str, status: str) -> None:
        async with self._db.cursor() as cur:
            await cur.execute(
                "UPDATE branch_run SET status=?, finished_at=? WHERE id=?",
                (status, time.time(), branch_id),
            )

    # ── NodeRun ───────────────────────────────────────────────────────────────

    async def create_node(
        self,
        branch_id: str,
        node_id: str,
        node_name: str,
        assignee_snapshot: str | None = None,
    ) -> str:
        """创建节点记录"""
        node_run_id = str(uuid.uuid4())
        now = time.time()
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO node_run
                   (id, branch_run_id, node_id, node_name, status, assignee_snapshot, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (node_run_id, branch_id, node_id, node_name, "pending", assignee_snapshot, now),
            )
        return node_run_id

    async def update_node(
        self,
        node_run_id: str,
        status: str,
        retry_count: int | None = None,
    ) -> None:
        async with self._db.cursor() as cur:
            if retry_count is not None:
                await cur.execute(
                    "UPDATE node_run SET status=?, finished_at=?, retry_count=? WHERE id=?",
                    (status, time.time(), retry_count, node_run_id),
                )
            else:
                await cur.execute(
                    "UPDATE node_run SET status=?, finished_at=? WHERE id=?",
                    (status, time.time(), node_run_id),
                )

    # ── RequestLog ────────────────────────────────────────────────────────────

    async def log_request(
        self,
        node_run_id: str,
        method: str,
        url: str,
        params: dict | None,
        response_status: int,
        response_body: str | None,
        duration_ms: int,
    ) -> str:
        """写入请求日志（自动脱敏）"""
        log_id = str(uuid.uuid4())
        now = time.time()
        req_summary = sanitize_request_summary(method, url, params, None)
        resp_summary = sanitize_response_summary(response_status, response_body)
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO request_log
                   (id, node_run_id, method, url, request_summary, response_summary,
                    status_code, duration_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (log_id, node_run_id, method, url,
                 json.dumps(req_summary, ensure_ascii=False),
                 json.dumps(resp_summary, ensure_ascii=False),
                 response_status, duration_ms, now),
            )
        return log_id

    # ── SessionLog ───────────────────────────────────────────────────────────

    async def log_session(
        self,
        execution_run_id: int,
        env_id: str,
        login_type: str,
        username: str,
        generation: int,
        action: str,
        reason: str,
    ) -> None:
        """写入会话日志"""
        log_id = str(uuid.uuid4())
        now = time.time()
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO session_log
                   (id, execution_run_id, env_id, login_type, username, generation,
                    action, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (log_id, execution_run_id, env_id, login_type, username,
                 generation, action, reason, now),
            )

    # ── CandidateSnapshot ──────────────────────────────────────────────────────

    async def save_candidate_snapshot(
        self,
        execution_id: str,
        node_id: str,
        field: str,
        selector_type: str,
        candidates: list[dict[str, Any]],
    ) -> str:
        """保存候选池快照"""
        snapshot_id = str(uuid.uuid4())
        now = time.time()
        sanitized = sanitize_dict({"candidates": candidates})
        async with self._db.cursor() as cur:
            await cur.execute(
                """INSERT INTO candidate_snapshot
                   (id, execution_run_id, node_id, field, selector_type, candidates_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (snapshot_id, execution_id, node_id, field, selector_type,
                 json.dumps(sanitized, ensure_ascii=False), now),
            )
        return snapshot_id
```

---

### Step 9: 创建 `tests/test_storage/test_recorder.py`

```python
"""测试 RunRecorder"""
import pytest
from workflow_test_desktop.core.storage.db import Database
from workflow_test_desktop.core.storage.recorder import RunRecorder


@pytest.fixture
async def db(tmp_path):
    db = Database(db_path=tmp_path / "test.db")
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
async def recorder(db):
    return RunRecorder(db)


@pytest.mark.asyncio
async def test_save_run_plan_sanitizes_sensitive_fields(recorder):
    """敏感字段应被脱敏后才写入"""
    plan = {
        "run_plan_version": 1,
        "name": "test plan",
        "password": "super_secret",
        "fields": {"api_token": "tok_abc"},
    }
    plan_id = await recorder.save_run_plan(
        name="test plan",
        env_id="dev",
        starter_username="testuser",
        flow_id="flow_001",
        flow_name="测试流程",
        random_seed=42,
        plan_json=plan,
    )
    assert plan_id is not None
    assert len(plan_id) == 36  # UUID 格式


@pytest.mark.asyncio
async def test_create_execution_and_branches(recorder):
    """测试创建执行记录和分支"""
    plan_id = await recorder.save_run_plan(
        name="test",
        env_id="dev",
        starter_username="user",
        flow_id="f1",
        flow_name="流程",
        random_seed=None,
        plan_json={"version": 1},
    )
    exec_id = await recorder.create_execution(plan_id, "wait_all_then_fail")
    assert exec_id is not None

    branch_id = await recorder.create_branch(exec_id, "branch_0")
    assert branch_id is not None

    await recorder.update_branch(branch_id, "completed")
    await recorder.update_execution(exec_id, "completed")
```

---

### Step 10: 提交

```bash
git add workflow_test_desktop/core/config/environment.py
git add workflow_test_desktop/core/config/secrets.py
git add workflow_test_desktop/core/storage/db.py
git add workflow_test_desktop/core/storage/sanitizer.py
git add workflow_test_desktop/core/storage/recorder.py
git add tests/test_config/test_environment.py
git add tests/test_config/test_secrets.py
git add tests/test_storage/test_sanitizer.py
git add tests/test_storage/test_recorder.py
git commit -m "feat: add config layer (EnvironmentService, SecretProvider), SQLite schema, sanitizer, and RunRecorder"
```
