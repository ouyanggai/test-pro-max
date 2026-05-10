"""SessionLease 数据类"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SessionLease:
    """
    会话租约。
    节点执行器拿到的是此对象，不是直接管理 SID。
    """
    env_id: str
    login_type: str
    username: str
    sid: str
    generation: int
    expires_at: float | None  # Unix 时间戳

    @property
    def cache_key(self) -> str:
        """缓存键：env_id + login_type + username"""
        return f"{self.env_id}+{self.login_type}+{self.username}"

    def is_expired(self) -> bool:
        """判断是否已过期"""
        import time
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at
