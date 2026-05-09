from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from workflow_test_desktop.workbench import WorkbenchSnapshot


def create_workbench_window(snapshot: WorkbenchSnapshot) -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("接口编排自动化测试工具")
    window.resize(1200, 760)

    toolbar = QToolBar("全局操作")
    toolbar.setObjectName("global_toolbar")
    toolbar.setFixedHeight(snapshot.layout.toolbar_height_px)
    toolbar.addAction("运行")
    toolbar.addAction("暂停")
    toolbar.addAction("停止")
    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(_panel("navigation_panel", "项目 / 流程 / 报告"))
    splitter.addWidget(_panel("main_panel", "流程回归工作区"))
    splitter.addWidget(_panel("details_panel", "上下文详情"))
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 3)
    splitter.setStretchFactor(2, 2)
    window.setCentralWidget(splitter)

    status_bar = QStatusBar()
    status_bar.setObjectName("status_bar")
    status_bar.setFixedHeight(snapshot.layout.status_bar_height_px)
    status_bar.showMessage(
        f"{snapshot.environment.env_name} | "
        f"{snapshot.environment.api_gateway or '未配置 API 网关'} | "
        f"{snapshot.connection.message}"
    )
    window.setStatusBar(status_bar)

    return window


def _panel(object_name: str, text: str) -> QWidget:
    panel = QWidget()
    panel.setObjectName(object_name)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.addWidget(QLabel(text))
    return panel
