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


def test_error_bus_multiple_handlers():
    bus = ErrorBus()
    bus.clear_handlers()
    called = []

    bus.on_error(lambda item: called.append("a"))
    bus.on_error(lambda item: called.append("b"))
    bus.emit("x", "y")
    bus.clear_handlers()

    assert called == ["a", "b"]


def test_error_bus_off_handler():
    bus = ErrorBus()
    bus.clear_handlers()
    called = []

    def handler(item: ErrorItem):
        called.append(item.title)

    bus.on_error(handler)
    bus.emit("first", "msg")
    bus.off_error(handler)
    bus.emit("second", "msg")

    assert called == ["first"]


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
    assert item.detail == "traceback..."
    assert item.source == "AuthModule"
    assert item.timestamp == "12:30:00"


def test_error_item_defaults():
    item = ErrorItem(title="t", message="m")
    assert item.detail == ""
    assert item.source == ""
    assert item.timestamp == ""


def test_error_bus_emits_timestamp():
    bus = ErrorBus()
    bus.clear_handlers()
    received = []

    bus.on_error(lambda item: received.append(item))
    bus.emit("t", "m")
    bus.clear_handlers()

    assert len(received) == 1
    assert len(received[0].timestamp) == 8  # "HH:MM:SS"
    assert received[0].timestamp.count(":") == 2
