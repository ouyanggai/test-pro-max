"""主窗口：侧边步骤条 + 内容区 + 导航按钮"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from workflow_test_desktop.config.themes import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    FONT_FAMILY, SPACE_XL, SPACE_LG, SPACE_SM, LIGHT, DARK, build_theme_css,
)
from workflow_test_desktop.ui.wizard_navigator import WizardNavigator
from workflow_test_desktop.ui.steps import (
    StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport,
)


class MainWindow(QWidget):
    """主窗口：左侧导航 + 右侧步骤内容 + 底部导航"""

    step_changed = Signal(int)

    def __init__(self, config, secrets, db, loop):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._current_step = 0
        self._theme = LIGHT

        # 跨步骤共享数据
        self._shared_data: dict = {}

        self._setup_ui()
        self._apply_theme()
        self._show_step(0)

    def _setup_ui(self):
        self.setWindowTitle("接口回归测试工作台")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧：步骤导航（固定 200px）
        self._nav = WizardNavigator(steps=[
            "① 账号", "② 流程", "③ 表单", "④ 节点", "⑤ 运行", "⑥ 报告",
        ])
        self._nav.step_clicked.connect(self._on_nav_step_clicked)
        self._nav.setFixedWidth(200)
        main_layout.addWidget(self._nav)

        # 右侧
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 内容区
        self._content_stack = QWidget()
        self._content_layout = QVBoxLayout(self._content_stack)
        self._content_layout.setContentsMargins(SPACE_XL, SPACE_XL, SPACE_XL, SPACE_LG)
        right_layout.addWidget(self._content_stack, 1)

        # 底部导航栏
        nav_bar = self._build_nav_bar()
        right_layout.addWidget(nav_bar)

        main_layout.addWidget(right_widget, 1)

    def _build_nav_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(60)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(SPACE_XL, SPACE_SM, SPACE_XL, SPACE_SM)

        self._btn_prev = QPushButton("← 上一步")
        self._btn_prev.setFont(FONT_FAMILY)
        self._btn_prev.clicked.connect(self._on_prev)

        self._btn_next = QPushButton("下一步 →")
        self._btn_next.setFont(FONT_FAMILY)
        self._btn_next.clicked.connect(self._on_next)

        layout.addStretch()
        layout.addWidget(self._btn_prev)
        layout.addWidget(self._btn_next)

        return bar

    def _show_step(self, index: int):
        steps = [StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport]
        if index < 0 or index >= len(steps):
            return

        # 清理旧内容
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 创建新步骤（注入共享依赖）
        step_widget = steps[index](
            config=self._config,
            secrets=self._secrets,
            db=self._db,
            loop=self._loop,
            shared_data=self._shared_data,
        )
        self._content_layout.addWidget(step_widget)
        self._current_step = index
        self._nav.set_current_step(index)
        self._update_nav_buttons()
        self.step_changed.emit(index)

    def _update_nav_buttons(self):
        self._btn_prev.setEnabled(self._current_step > 0)
        if self._current_step == 4:
            self._btn_next.setText("▶ 运行")
        elif self._current_step == 5:
            self._btn_next.setText("查看报告")
        else:
            self._btn_next.setText("下一步 →")
        self._btn_next.setEnabled(True)

    def _on_prev(self):
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    def _on_next(self):
        if self._current_step < 5:
            self._show_step(self._current_step + 1)
        elif self._current_step == 4:
            self._show_step(5)

    def _on_nav_step_clicked(self, index: int):
        # 只能回退，不能跳到未完成的步骤
        if index <= self._current_step:
            self._show_step(index)

    def _apply_theme(self):
        css = build_theme_css(self._theme)
        self.setStyleSheet(css)

    def toggle_theme(self):
        self._theme = DARK if self._theme == LIGHT else LIGHT
        self._apply_theme()

    def get_shared_data(self) -> dict:
        return self._shared_data
