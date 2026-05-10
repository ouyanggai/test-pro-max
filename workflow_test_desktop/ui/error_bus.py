"""错误通知总线（单例）"""
from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import Callable


@dataclass
class ErrorItem:
    """单条错误"""
    title: str       # 简短标题，如 "登录失败"
    message: str     # 详细消息
    detail: str = "" # 完整堆栈/响应体（可选）
    source: str = "" # 来源模块名
    timestamp: str = ""


class ErrorBus:
    """
    全局错误通知总线（单例）。
    步骤通过 emit() 发布错误，UI 层通过 on_error() 订阅显示。
    """
    _instance: ErrorBus | None = None

    def __new__(cls) -> ErrorBus:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: list[Callable[[ErrorItem], None]] = []
        return cls._instance

    def emit(self, title: str, message: str, detail: str = "", source: str = ""):
        """发布一条错误"""
        item = ErrorItem(
            title=title,
            message=message,
            detail=detail,
            source=source,
            timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
        )
        logger = logging.getLogger("workflow_test_desktop")
        logger.error("[%s] %s: %s | %s | source=%s",
                     item.timestamp, title, message, detail, source)
        for handler in self._handlers:
            handler(item)

    def on_error(self, handler: Callable[[ErrorItem], None]):
        """订阅错误通知"""
        self._handlers.append(handler)

    def off_error(self, handler: Callable[[ErrorItem], None]):
        """取消订阅"""
        self._handlers.remove(handler)

    def clear_handlers(self):
        """清空所有处理器（仅用于测试）"""
        self._handlers.clear()
