import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from workflow_test_desktop.workbench import EnvironmentConfig, build_workbench_snapshot
from workflow_test_desktop.qt_workbench import create_workbench_window


def test_qt_workbench_window_exposes_required_regions():
    app = QApplication.instance() or QApplication([])
    snapshot = build_workbench_snapshot(
        EnvironmentConfig(
            env_name="local-dry-run",
            api_gateway="http://127.0.0.1:38081/api",
            connection_checker=lambda gateway: True,
        )
    )

    window = create_workbench_window(snapshot)
    window.show()
    app.processEvents()

    assert window.findChild(object, "navigation_panel") is not None
    assert window.findChild(object, "main_panel") is not None
    assert window.findChild(object, "details_panel") is not None
    assert window.findChild(object, "global_toolbar") is not None
    assert window.findChild(object, "status_bar") is not None
    assert "local-dry-run" in window.statusBar().currentMessage()
    assert "环境连接正常" in window.statusBar().currentMessage()
