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
