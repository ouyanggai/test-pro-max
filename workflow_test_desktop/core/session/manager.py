"""SessionManager：全局单例，缓存键 env_id+login_type+username，防顶号"""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Callable

from workflow_test_desktop.core.session.lease import SessionLease
from workflow_test_desktop.core.config.secrets import SecretProvider

logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """会话管理异常"""


class SessionManager:
    """
    全局会话管理器单例。

    职责：
    - 按 env_id + login_type + username 缓存 SID
    - 同一缓存键同时只允许一个登录动作（per-key asyncio.Lock）
    - SID 有效时直接复用
    - SID 失效时自动重登
    - 记录 session_log（不含密钥）

    节点执行器永远通过 get_session() 获取会话，不自行登录。
    """

    _instance: SessionManager | None = None

    def __init__(
        self,
        secret_provider: SecretProvider,
        login_func: Callable,
    ):
        self._secrets = secret_provider
        self._login_func = login_func
        self._cache: dict[str, SessionLease] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._log_callback: Callable | None = None
        # 标记哪些 key 被 mark_invalid 了，需要强制重登
        self._invalidated_keys: set[str] = set()
        # 记录各 key 的最新 generation（即使 cache 被删除也保留）
        self._last_generation: dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> SessionManager:
        if cls._instance is None:
            raise SessionManagerError("SessionManager 未初始化，请先调用 set_instance()")
        return cls._instance

    @classmethod
    def set_instance(cls, instance: SessionManager) -> None:
        cls._instance = instance

    @classmethod
    def reset(cls) -> None:
        """仅测试用：重置单例"""
        cls._instance = None

    def set_log_callback(
        self,
        callback: Callable[[int, str, str, str, int, str, str], None]
    ) -> None:
        """设置会话日志回调：(execution_id, env_id, login_type, username, generation, action, reason)"""
        self._log_callback = callback

    def _get_lock(self, cache_key: str) -> asyncio.Lock:
        if cache_key not in self._locks:
            self._locks[cache_key] = asyncio.Lock()
        return self._locks[cache_key]

    def _cache_key(self, env_id: str, login_type: str, username: str) -> str:
        return f"{env_id}+{login_type}+{username}"

    async def get_session(
        self,
        env_id: str,
        login_type: str,
        username: str,
    ) -> SessionLease:
        """获取处理人会话"""
        key = self._cache_key(env_id, login_type, username)

        # 快速路径：缓存命中且未过期，且未被 mark_invalid
        if key in self._cache:
            lease = self._cache[key]
            if not lease.is_expired() and key not in self._invalidated_keys:
                logger.debug(f"SID 命中缓存: {key}")
                return lease

        # 慢路径：加锁登录
        async with self._get_lock(key):
            # 双检：其他协程可能已登录（且未被 mark_invalid）
            if key in self._cache and key not in self._invalidated_keys:
                lease = self._cache[key]
                if not lease.is_expired():
                    return lease

            # 清除 invalidate 标记
            self._invalidated_keys.discard(key)

            # 基于 _last_generation 递增（即使 cache 被 mark_invalid 删除了也保留）
            current_gen = self._last_generation.get(key, 0)
            new_lease = await self._do_login(env_id, login_type, username, generation_hint=current_gen + 1)
            self._cache[key] = new_lease
            self._last_generation[key] = new_lease.generation
            self._log(0, env_id, login_type, username, new_lease.generation, "login", "首次登录")
            return new_lease

    async def refresh_if_needed(
        self,
        lease: SessionLease,
        execution_id: int,
        reason: str,
    ) -> SessionLease:
        """检查 lease 是否仍有效，若失效则重登"""
        key = self._cache_key(lease.env_id, lease.login_type, lease.username)

        if not lease.is_expired() and key in self._cache:
            current = self._cache[key]
            if current.generation > lease.generation:
                self._log(execution_id, lease.env_id, lease.login_type,
                          lease.username, current.generation, "reused", "generation 更新，复用新 SID")
                return current

        async with self._get_lock(key):
            if key in self._cache:
                current = self._cache[key]
                if not current.is_expired():
                    return current

            current_gen = self._last_generation.get(key, 0)
            new_lease = await self._do_login(
                lease.env_id, lease.login_type, lease.username,
                generation_hint=current_gen + 1,
            )
            self._cache[key] = new_lease
            self._last_generation[key] = new_lease.generation
            self._log(execution_id, lease.env_id, lease.login_type,
                      lease.username, new_lease.generation, "relogin", reason)
            return new_lease

    async def mark_invalid(
        self,
        lease: SessionLease,
        execution_id: int,
        reason: str,
    ) -> None:
        """标记某个 lease 失效，下次 get_session 时强制重登"""
        key = self._cache_key(lease.env_id, lease.login_type, lease.username)
        async with self._get_lock(key):
            if key in self._cache and self._cache[key].generation == lease.generation:
                del self._cache[key]
            # 标记需要重登
            self._invalidated_keys.add(key)
            self._log(execution_id, lease.env_id, lease.login_type,
                      lease.username, lease.generation, "invalidated", reason)

    def _log(
        self,
        execution_id: int,
        env_id: str,
        login_type: str,
        username: str,
        generation: int,
        action: str,
        reason: str,
    ) -> None:
        if self._log_callback:
            self._log_callback(execution_id, env_id, login_type, username, generation, action, reason)

    async def _do_login(
        self,
        env_id: str,
        login_type: str,
        username: str,
        generation_hint: int,
    ) -> SessionLease:
        password_key = f"{login_type.upper()}_PASSWORD"
        password = self._secrets.get(password_key)
        if not password:
            password = self._secrets.get("PASSWORD")

        login_result = await self._login_func(env_id, login_type, username, password)
        # SID 嵌套在 data 字段中
        data = login_result.get("data", {})
        sid = data.get("sid") or data.get("token") if isinstance(data, dict) else None
        if not sid:
            raise SessionManagerError(f"登录失败，未获取到 SID: {login_result}")

        expires_at = None
        if "expires_at" in login_result:
            expires_at = float(login_result["expires_at"])
        elif "expires_in" in login_result:
            expires_at = time.time() + float(login_result["expires_in"])

        return SessionLease(
            env_id=env_id,
            login_type=login_type,
            username=username,
            sid=sid,
            generation=generation_hint,
            expires_at=expires_at,
        )
