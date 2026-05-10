import pytest
from PySide6.QtWidgets import QApplication
from workflow_test_desktop.ui.error_notification import ErrorNotificationBar
from workflow_test_desktop.ui.error_bus import ErrorBus, ErrorItem


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


@pytest.fixture
def fresh_error_bus():
    """Reset ErrorBus singleton before each test."""
    ErrorBus._instance = None
    yield
    ErrorBus._instance = None


def test_error_notification_creates(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    assert bar.height() == 0


def test_error_notification_shows_on_error(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("测试错误", "这是测试消息")
    assert bar.height() > 0
    assert bar.error_count() == 1


def test_error_notification_dismiss(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("错误1", "消息1")
    assert bar.height() > 0
    bar._dismiss_error(0)
    assert bar.height() == 0
    assert bar.error_count() == 0


def test_error_notification_multiple_errors(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("错误1", "消息1")
    ErrorBus().emit("错误2", "消息2")
    ErrorBus().emit("错误3", "消息3")
    ErrorBus().emit("错误4", "消息4")
    assert bar.error_count() == 4
    # 高度由 min(4,3)*60=180 决定
    assert bar.height() == 180


def test_error_notification_clear_all(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("错误1", "消息1")
    ErrorBus().emit("错误2", "消息2")
    assert bar.height() > 0
    bar.clear_all()
    assert bar.height() == 0
    assert bar.error_count() == 0


def test_error_notification_uses_timestamp(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("t", "m")
    assert bar.error_count() == 1
    assert len(bar._errors[0].timestamp) == 8
    assert bar._errors[0].timestamp.count(":") == 2


def test_error_notification_source(app, fresh_error_bus):
    bar = ErrorNotificationBar()
    ErrorBus().emit("t", "m", source="AuthModule")
    assert bar._errors[0].source == "AuthModule"
