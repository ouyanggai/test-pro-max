# 子计划 2：错误通知组件

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现错误通知条组件 + 错误收集总线，供所有步骤共享

**Architecture:**
- `ErrorNotifier` 独立 Widget，内嵌在主窗口内容区顶部
- `ErrorBus` 单例，步骤通过 `emit_error()` 发布错误，UI 订阅显示
- 支持多条错误叠加展示

**Tech Stack:** PySide6 QWidget + Signal/Slot

**Dependencies:** 子计划 0（日志）、子计划 1（主窗口）

---

### Task 2-1: ErrorBus（错误收集总线）

**Files:**
- Create: `workflow_test_desktop/ui/error_bus.py`
- Test: `tests/test_error_bus.py`

- [ ] **Step 1: 创建 ErrorBus**

```python
"""错误通知总线（单例）"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
import logging


@dataclass
class ErrorItem:
    """单条错误"""
    title: str           # 简短标题，如 "登录失败"
    message: str         # 详细消息
    detail: str = ""     # 完整堆栈/响应体（可选）
    source: str = ""     # 来源模块名
    timestamp: str = ""   # 时间戳


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
        import datetime
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
        self._handlers.clear()
```

- [ ] **Step 2: 写测试**

```python
# tests/test_error_bus.py
import pytest
from workflow_test_desktop.ui.error_bus import ErrorBus, ErrorItem


def test_error_bus_singleton():
    bus1 = ErrorBus()
    bus2 = ErrorBus()
    assert bus1 is bus2


def test_error_bus_emit_calls_handler():
    bus = ErrorBus()
    bus.clear_handlers()
    received = []

    def handler(item: ErrorItem):
        received.append(item)

    bus.on_error(handler)
    bus.emit("测试错误", "测试消息", detail="堆栈信息", source="test")
    bus.off_error(handler)

    assert len(received) == 1
    assert received[0].title == "测试错误"
    assert received[0].message == "测试消息"
    assert received[0].detail == "堆栈信息"
    assert received[0].source == "test"


def test_error_item_fields():
    item = ErrorItem(
        title="登录失败",
        message="用户名错误",
        detail="traceback...",
        source="AuthModule",
        timestamp="12:30:00",
    )
    assert item.title == "登录失败"
    assert item.message == "用户名错误"
```

- [ ] **Step 3: 运行测试**

Run: `cd /Users/ouyanggai/Documents/test-pro-max && python -m pytest tests/test_error_bus.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add workflow_test_desktop/ui/error_bus.py tests/test_error_bus.py
git commit -m "feat: add ErrorBus singleton for centralized error notification"
```

---

### Task 2-2: ErrorNotification（错误通知条）

**Files:**
- Create: `workflow_test_desktop/ui/error_notification.py`
- Modify: `workflow_test_desktop/ui/main_window.py`（将 ErrorNotifier 嵌入内容区顶部）
- Test: `tests/test_error_notification.py`

- [ ] **Step 1: 创建 ErrorNotification Widget**

```python
"""错误通知条组件"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
    QFrame, QTextEdit,
)
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont

from workflow_test_desktop.ui.error_bus import ErrorBus, ErrorItem
from workflow_test_desktop.config.themes import FONT_FAMILY


class ErrorNotificationBar(QWidget):
    """
    错误通知条，显示在内容区顶部。
    支持多条错误叠加、自动收起、手动展开详情。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._errors: list[ErrorItem] = []
        self._expanded_id: int | None = None
        self._setup_ui()
        self._subscribe()

    def _setup_ui(self):
        self.setFixedHeight(0)  # 初始隐藏
        self.setMaximumHeight(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(SPACE_XL_PX, 8, SPACE_XL_PX, 8)
        self._container_layout.setSpacing(4)
        layout.addWidget(self._container)

    def _subscribe(self):
        ErrorBus().on_error(self._on_new_error)

    def _on_new_error(self, item: ErrorItem):
        self._errors.append(item)
        self._render_errors()
        self._auto_hide_timer()

    def _render_errors(self):
        """渲染所有错误条"""
        # 清除现有
        while self._container_layout.count():
            self._container_layout.takeAt(0).widget().deleteLater()

        for i, err in enumerate(self._errors):
            bar = self._build_error_bar(err, i)
            self._container_layout.addWidget(bar)

        # 更新高度
        total = min(len(self._errors), 3) * 56 + min(len(self._errors), 3) * 4
        self.setFixedHeight(total)
        self.update()

    def _build_error_bar(self, err: ErrorItem, index: int) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(
            "QFrame { background-color: #FEF2F2; border-radius: 8px; padding: 10px 12px; }"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)

        # 图标
        icon = QLabel("⚠")
        icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        icon.setFixedWidth(24)
        layout.addWidget(icon)

        # 内容
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        title_label = QLabel(err.title)
        title_label.setFont(FONT_FAMILY)
        title_label.setStyleSheet("font-weight: 600; color: #991B1B; font-size: 14px;")
        content_layout.addWidget(title_label)

        msg_label = QLabel(err.message)
        msg_label.setFont(FONT_FAMILY)
        msg_label.setStyleSheet("color: #B91C1C; font-size: 13px;")
        msg_label.setWordWrap(True)
        content_layout.addWidget(msg_label)

        # 详情展开
        if err.detail:
            detail_label = QLabel(err.detail)
            detail_label.setFont(FONT_FAMILY)
            detail_label.setStyleSheet("color: #7F1D1D; font-size: 12px; font-family: monospace;")
            detail_label.setWordWrap(True)
            detail_label.setVisible(False)
            detail_label.setObjectName("detail")
            content_layout.addWidget(detail_label)

        layout.addWidget(content, 1)

        # 按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        if err.detail:
            btn_detail = QPushButton("详情")
            btn_detail.setFont(FONT_FAMILY)
            btn_detail.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid #FECACA; "
                "border-radius: 4px; color: #991B1B; padding: 2px 8px; font-size: 12px; }"
            )
            idx = index
            detail_lbl = content.findChild(QLabel, "detail")
            btn_detail.clicked.connect(lambda _, d=detail_lbl: d.setVisible(not d.isVisible()))
            btn_layout.addWidget(btn_detail)

        btn_close = QPushButton("✕")
        btn_close.setFont(FONT_FAMILY)
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #991B1B; "
            "font-size: 14px; padding: 0; }"
        )
        btn_close.clicked.connect(lambda _, i=index: self._dismiss_error(i))
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        return bar

    def _dismiss_error(self, index: int):
        if 0 <= index < len(self._errors):
            self._errors.pop(index)
            self._render_errors()
            if not self._errors:
                self.setFixedHeight(0)

    def _auto_hide_timer(self):
        """3秒后提示可收起（不自动消失，保持可见直到用户关闭）"""
        pass  # 改为手动关闭，不自动消失

    def clear_all(self):
        """清空所有错误"""
        self._errors.clear()
        self._render_errors()
        self.setFixedHeight(0)
```

- [ ] **Step 2: 将 ErrorNotificationBar 嵌入 main_window.py 内容区顶部**

Read: `workflow_test_desktop/ui/main_window.py`

在 `_setup_ui` 的内容区布局中，`self._content_stack` 之前添加：

```python
        # 错误通知条（内容区顶部）
        self._error_bar = ErrorNotificationBar()
        content_layout.addWidget(self._error_bar)

        # 步骤内容区
        self._content_stack = QWidget()
        content_layout.addWidget(self._content_stack, 1)
```

在 `import` 区域添加：

```python
from workflow_test_desktop.ui.error_notification import ErrorNotificationBar
```

- [ ] **Step 3: 写测试**

```python
# tests/test_error_notification.py
import pytest
from PySide6.QtWidgets import QApplication
from workflow_test_desktop.ui.error_notification import ErrorNotificationBar
from workflow_test_desktop.ui.error_bus import ErrorBus, ErrorItem


@pytest.fixture
def app():
    app = QApplication.instance() or QApplication([])


def test_error_notification_creates(app):
    bar = ErrorNotificationBar()
    assert bar.height() == 0  # 初始隐藏


def test_error_notification_shows_on_error(app):
    bar = ErrorNotificationBar()
    ErrorBus().clear_handlers()
    ErrorBus().emit("测试错误", "这是测试消息")
    assert bar.height() > 0


def test_error_notification_dismiss(app):
    bar = ErrorNotificationBar()
    ErrorBus().clear_handlers()
    ErrorBus().emit("错误1", "消息1")
    assert bar.height() > 0
    bar._dismiss_error(0)
    assert bar.height() == 0
```

- [ ] **Step 4: 运行测试**

Run: `cd /Users/ouyanggai/Documents/test-pro-max && python -m pytest tests/test_error_notification.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add workflow_test_desktop/ui/error_notification.py workflow_test_desktop/ui/main_window.py tests/test_error_notification.py
git commit -m "feat: add ErrorNotificationBar with ErrorBus for centralized error display"
```
