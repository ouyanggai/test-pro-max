import pytest
from PySide6.QtWidgets import QApplication
from workflow_test_desktop.ui.main_window import MainWindow
from workflow_test_desktop.core.config.secrets import SecretProvider


@pytest.fixture
def mock_secrets():
    """Mock secrets provider with a pre-populated cache."""
    provider = SecretProvider.__new__(SecretProvider)
    provider._cache = {"DEFAULT_USERNAME": "test_user"}
    provider._loaded = True
    return provider


@pytest.fixture
def app(mock_secrets):
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    yield qapp


def test_main_window_creates(app, mock_secrets):
    mw = MainWindow(config=None, secrets=mock_secrets, db=None, loop=None)
    assert mw.windowTitle() == "接口回归测试工作台"
    assert mw._current_step == 0
    assert mw._progress_bar.value() == 1
    assert mw._btn_next.text() == "下一步 →"
    assert not mw._btn_prev.isEnabled()


def test_main_window_step_navigation(app, mock_secrets):
    mw = MainWindow(config=None, secrets=mock_secrets, db=None, loop=None)
    # 点击下一步
    mw._on_next()
    assert mw._current_step == 1
    assert mw._progress_bar.value() == 2
    assert mw._btn_prev.isEnabled()

    # 点击上一步
    mw._on_prev()
    assert mw._current_step == 0
    assert mw._progress_bar.value() == 1


def test_main_window_prevents_forward_jump(app, mock_secrets):
    mw = MainWindow(config=None, secrets=mock_secrets, db=None, loop=None)
    # 尝试跳过步骤 0 直接到 2
    mw._on_nav_step_clicked(2)
    assert mw._current_step == 0

    # 正常前进到步骤 1
    mw._on_next()
    assert mw._current_step == 1
    # 尝试跳到步骤 0（可以回退）
    mw._on_nav_step_clicked(0)
    assert mw._current_step == 0


def test_main_window_progress_label(app, mock_secrets):
    mw = MainWindow(config=None, secrets=mock_secrets, db=None, loop=None)
    assert mw._progress_label.text() == "步骤 1 / 6"
    mw._on_next()
    assert mw._progress_label.text() == "步骤 2 / 6"
