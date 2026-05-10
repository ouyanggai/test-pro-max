"""主窗口：左侧导航 + 内容区（内嵌导航按钮）"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QProgressBar, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from workflow_test_desktop.config.themes import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    FONT_FAMILY, SPACE_LG_PX, SPACE_SM_PX, SPACE_XL_PX, LIGHT, DARK, build_theme_css,
)
from workflow_test_desktop.ui.wizard_navigator import WizardNavigator
from workflow_test_desktop.ui.error_notification import ErrorNotificationBar
from workflow_test_desktop.ui.steps import (
    StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport,
)
logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """主窗口：左侧导航 + 右侧内容区（内嵌上一步/下一步按钮）"""

    step_changed = Signal(int)

    def __init__(self, config, secrets, db, loop):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._current_step = 0
        self._theme = LIGHT
        self._shared_data: dict = {}

        self._setup_ui()
        self._apply_theme()
        self._show_step(0)

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        self.setWindowTitle("接口回归测试工作台")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # 主布局：左侧导航 + 右侧内容
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航（固定 200px）
        self._nav = WizardNavigator(steps=[
            "① 账号", "② 流程", "③ 表单", "④ 节点", "⑤ 运行", "⑥ 报告",
        ])
        self._nav.step_clicked.connect(self._on_nav_step_clicked)
        self._nav.setFixedWidth(200)
        main_layout.addWidget(self._nav)

        # 右侧：内容区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 内容区（步骤内容 + 底部导航按钮）
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(SPACE_XL_PX, SPACE_XL_PX, SPACE_XL_PX, 0)
        content_layout.setSpacing(SPACE_LG_PX)

        # 步骤内容区
        self._content_stack = QWidget()
        self._ensure_content_layout()
        content_layout.addWidget(self._content_stack, 1)

        # 错误通知条（插入到内容区最顶部）
        self._error_bar = ErrorNotificationBar()
        content_layout.insertWidget(0, self._error_bar)

        # 底部导航区（内嵌到内容区底部）
        nav_area = self._build_nav_area()
        content_layout.addWidget(nav_area)

        right_layout.addWidget(content_area)
        main_layout.addWidget(right_widget, 1)

    def _ensure_content_layout(self):
        """确保 _content_stack 拥有布局管理器（首次调用或切换步骤前使用）"""
        if self._content_stack.layout() is None:
            layout = QVBoxLayout(self._content_stack)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

    def _build_nav_area(self) -> QWidget:
        """底部导航区：进度条 + 上一步/下一步按钮"""
        container = QWidget()
        container.setFixedHeight(120)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, SPACE_SM_PX, 0, SPACE_LG_PX)
        layout.setSpacing(SPACE_SM_PX)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setFont(FONT_FAMILY)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setRange(0, 5)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # 进度文字
        self._progress_label = QLabel("步骤 1 / 6")
        self._progress_label.setFont(FONT_FAMILY)
        self._progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._progress_label)

        # 导航按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_prev = QPushButton("← 上一步")
        self._btn_prev.setFont(FONT_FAMILY)
        self._btn_prev.setProperty("theme", "secondary")
        self._btn_prev.setFixedWidth(140)
        self._btn_prev.clicked.connect(self._on_prev)
        btn_layout.addWidget(self._btn_prev)

        self._btn_next = QPushButton("下一步 →")
        self._btn_next.setFont(FONT_FAMILY)
        self._btn_next.setProperty("theme", "primary")
        self._btn_next.setFixedWidth(180)
        self._btn_next.clicked.connect(self._on_next)
        btn_layout.addWidget(self._btn_next)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return container

    # ─── 步骤切换 ───────────────────────────────────────────────

    def _show_step(self, index: int):
        steps = [StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport]
        if index < 0 or index >= len(steps):
            return

        # 确保布局已设置
        self._ensure_content_layout()

        # 清理旧内容
        while self._content_stack.layout().count():
            item = self._content_stack.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 创建新步骤
        step_widget = steps[index](
            config=self._config,
            secrets=self._secrets,
            db=self._db,
            loop=self._loop,
            shared_data=self._shared_data,
        )
        self._content_stack.layout().addWidget(step_widget)

        self._current_step = index
        self._nav.set_current_step(index)
        self._update_nav_buttons()
        self.step_changed.emit(index)

        logger.info("切换到步骤 %d: %s", index, steps[index].__name__)

    def _update_nav_buttons(self):
        """更新导航按钮状态"""
        self._btn_prev.setEnabled(self._current_step > 0)

        # 进度条
        self._progress_bar.setValue(self._current_step + 1)
        self._progress_label.setText(f"步骤 {self._current_step + 1} / 6")

        # 下一步文字
        if self._current_step == 4:
            self._btn_next.setText("▶ 运行")
        elif self._current_step == 5:
            self._btn_next.setText("查看报告")
        else:
            self._btn_next.setText("下一步 →")

    # ─── 导航事件 ───────────────────────────────────────────────

    def _on_prev(self):
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    def _on_next(self):
        # 验证当前步骤
        step_widget = self._content_stack.layout().itemAt(0).widget()
        if step_widget and hasattr(step_widget, 'validate'):
            valid, msg = step_widget.validate()
            if not valid:
                logger.warning("步骤 %d 验证失败: %s", self._current_step + 1, msg)
                return  # 不前进

        if self._current_step < 5:
            self._show_step(self._current_step + 1)
        elif self._current_step == 4:
            self._show_step(5)

    def _on_nav_step_clicked(self, index: int):
        if index <= self._current_step:
            self._show_step(index)

    # ─── 主题 ───────────────────────────────────────────────

    def _apply_theme(self):
        css = build_theme_css(self._theme)
        self.setStyleSheet(css)

    def toggle_theme(self):
        self._theme = DARK if self._theme == LIGHT else LIGHT
        self._apply_theme()
        logger.info("切换主题: %s", "dark" if self._theme == DARK else "light")

    def get_shared_data(self) -> dict:
        return self._shared_data
