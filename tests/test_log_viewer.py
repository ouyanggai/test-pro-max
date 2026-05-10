import pytest
from PySide6.QtWidgets import QApplication
from workflow_test_desktop.ui.log_viewer import LogViewerDialog
from workflow_test_desktop.core.logging_config import setup_logging
import logging


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_log_viewer_creates(app):
    dialog = LogViewerDialog()
    assert dialog.windowTitle() == "日志查看器"
    assert dialog.width() == 900
    assert dialog.height() == 500


def test_log_viewer_accepts_filter(app, tmp_path, monkeypatch):
    # Mock log file path
    from workflow_test_desktop.core import logging_config
    test_log = tmp_path / "app_2026-05-10.log"
    monkeypatch.setattr(logging_config, "get_log_file_path", lambda: test_log)

    dialog = LogViewerDialog()
    assert dialog._filter_level == "全部"
    dialog._level_combo.setCurrentText("ERROR")
    assert dialog._filter_level == "ERROR"
    dialog._level_combo.setCurrentText("全部")
    assert dialog._filter_level == "全部"
