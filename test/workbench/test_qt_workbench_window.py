import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget, QFrame

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

    assert window.findChild(QWidget, "navigation_panel") is not None
    assert window.findChild(QWidget, "main_panel") is not None
    assert window.findChild(QWidget, "details_panel") is not None
    assert window.findChild(QWidget, "global_toolbar") is not None
    assert window.findChild(QWidget, "status_bar") is not None
    assert window.findChild(QFrame, "starter_account_section") is not None
    assert window.findChild(QFrame, "flow_selection_section") is not None
    assert window.findChild(QFrame, "review_node_section") is not None
    assert window.findChild(QFrame, "environment_status_section") is not None
    assert "本地演示环境" in window.statusBar().currentMessage()
    assert "dry-run" not in window.statusBar().currentMessage()
    assert "环境连接正常" in window.statusBar().currentMessage()
