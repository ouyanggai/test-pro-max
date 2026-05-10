# 子计划 1：主题升级 + 主窗口布局重构

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 升级 Qt CSS 主题 + Fusion 主题 + 重构主窗口布局（移入导航按钮到内容区）

**Architecture:**
- `themes.py` 扩展完整的组件样式表（按钮/输入框/卡片/进度条等），亮暗双主题
- `main_window.py` 移除底部导航栏，在内容区底部添加居中的上一步/下一步按钮 + 细条进度条
- `app.py` 设置 `Fusion` 风格

**Tech Stack:** PySide6, Qt CSS, Qt Fusion

**Dependencies:** 子计划 0（日志系统）

---

### Task 1-1: 升级 themes.py

**Files:**
- Modify: `workflow_test_desktop/config/themes.py`
- Test: `tests/test_themes.py`

- [ ] **Step 1: 读取现有 themes.py 确认当前内容**

Read: `workflow_test_desktop/config/themes.py`

- [ ] **Step 2: 替换 themes.py 为完整升级版本**

```python
"""双主题调色板（浅色 / 深色） + 完整组件样式"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ThemeColors:
    bg_primary: Final[str]
    bg_secondary: Final[str]
    bg_card: Final[str]
    border: Final[str]
    text_primary: Final[str]
    text_secondary: Final[str]
    accent: Final[str]
    accent_hover: Final[str]
    accent_light: Final[str]
    success: Final[str]
    warning: Final[str]
    error: Final[str]
    error_bg: Final[str]
    error_text: Final[str]
    sidebar_bg: Final[str]
    sidebar_active: Final[str]
    sidebar_done: Final[str]
    sidebar_text_active: Final[str]
    sidebar_text_done: Final[str]
    sidebar_text_future: Final[str]


LIGHT: ThemeColors = ThemeColors(
    bg_primary="#FFFFFF",
    bg_secondary="#F4F5F7",
    bg_card="#FFFFFF",
    border="#E2E4E9",
    text_primary="#1A1D26",
    text_secondary="#6B7280",
    accent="#0EA5E9",
    accent_hover="#0284C7",
    accent_light="#DBEAFE",
    success="#10B981",
    warning="#F59E0B",
    error="#EF4444",
    error_bg="#FEF2F2",
    error_text="#991B1B",
    sidebar_bg="#F8F9FA",
    sidebar_active="#0EA5E9",
    sidebar_done="#DBEAFE",
    sidebar_text_active="#FFFFFF",
    sidebar_text_done="#0EA5E9",
    sidebar_text_future="#9CA3AF",
)


DARK: ThemeColors = ThemeColors(
    bg_primary="#0F1117",
    bg_secondary="#161921",
    bg_card="#1C1F2A",
    border="#2A2D3A",
    text_primary="#E8EAF0",
    text_secondary="#8B90A0",
    accent="#38BDF8",
    accent_hover="#0EA5E9",
    accent_light="#1E3A5F",
    success="#34D399",
    warning="#FBBF24",
    error="#F87171",
    error_bg="#2D1B1B",
    error_text="#FCA5A5",
    sidebar_bg="#13151E",
    sidebar_active="#38BDF8",
    sidebar_done="#1E3A5F",
    sidebar_text_active="#0F1117",
    sidebar_text_done="#38BDF8",
    sidebar_text_future="#4B5563",
)


def build_theme_css(theme: ThemeColors) -> str:
    """生成完整的 Qt 样式表（Fusion 基础上覆盖）"""
    t = theme
    return f"""
QWidget {{
    background-color: {t.bg_primary};
    color: {t.text_primary};
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    font-size: 14px;
}}
QLabel {{
    background-color: transparent;
    border: none;
    color: {t.text_primary};
}}

/* ===== 按钮样式 ===== */
QPushButton {{
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-family: inherit;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    background-color: {t.bg_secondary};
    color: {t.text_primary};
}}
QPushButton:hover {{
    background-color: {t.border};
}}
QPushButton:pressed {{
    background-color: {t.border};
}}

/* 主按钮（蓝底白字） */
QPushButton[theme="primary"] {{
    background-color: {t.accent};
    color: white;
}}
QPushButton[theme="primary"]:hover {{
    background-color: {t.accent_hover};
}}

/* 次要按钮（边框） */
QPushButton[theme="secondary"] {{
    background-color: transparent;
    border: 1.5px solid {t.accent};
    color: {t.accent};
}}
QPushButton[theme="secondary"]:hover {{
    background-color: {t.accent_light};
}}

/* 危险按钮 */
QPushButton[theme="danger"] {{
    background-color: {t.error};
    color: white;
}}
QPushButton[theme="danger"]:hover {{
    background-color: #DC2626;
}}

/* 禁用状态 */
QPushButton:disabled {{
    background-color: {t.bg_secondary};
    color: {t.text_secondary};
    cursor: not-allowed;
}}

/* ===== 输入框样式 ===== */
QLineEdit, QTextEdit, QSpinBox {{
    background-color: {t.bg_secondary};
    color: {t.text_primary};
    border: 1.5px solid {t.border};
    border-radius: 8px;
    padding: 8px 12px;
    font-family: inherit;
    font-size: 14px;
    selection-background-color: {t.accent_light};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {t.accent};
    background-color: {t.bg_card};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {t.bg_primary};
    color: {t.text_secondary};
}}

/* ===== 下拉框 ===== */
QComboBox {{
    background-color: {t.bg_secondary};
    color: {t.text_primary};
    border: 1.5px solid {t.border};
    border-radius: 8px;
    padding: 8px 12px;
    font-family: inherit;
    font-size: 14px;
}}
QComboBox:hover {{
    border-color: {t.accent};
}}
QComboBox:focus {{
    border-color: {t.accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {t.text_secondary};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.bg_card};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: 8px;
    selection-background-color: {t.accent_light};
    padding: 4px;
}}

/* ===== 卡片 ===== */
QFrame[frameShape="4"] {{
    background-color: {t.bg_card};
    border: 1px solid {t.border};
    border-radius: 12px;
    padding: 16px;
}}

/* ===== 进度条 ===== */
QProgressBar {{
    background-color: {t.bg_secondary};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {t.accent};
    border-radius: 6px;
}}

/* ===== 列表 ===== */
QListWidget {{
    background-color: {t.bg_card};
    border: 1px solid {t.border};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px;
}}
QListWidget::item:selected {{
    background-color: {t.accent_light};
    color: {t.accent};
}}
QListWidget::item:hover:!selected {{
    background-color: {t.bg_secondary};
}}

/* ===== 表格 ===== */
QTableWidget, QTreeWidget {{
    background-color: {t.bg_card};
    border: 1px solid {t.border};
    border-radius: 8px;
    gridline-color: {t.border};
    font-family: inherit;
    font-size: 14px;
    outline: none;
}}
QHeaderView::section {{
    background-color: {t.bg_secondary};
    color: {t.text_secondary};
    border: none;
    border-bottom: 1px solid {t.border};
    padding: 10px 12px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}}

/* ===== 滚动条 ===== */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {t.border};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.text_secondary};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0 4px;
}}
QScrollBar::handle:horizontal {{
    background: {t.border};
    border-radius: 4px;
    min-width: 30px;
}}

/* ===== 工具提示 ===== */
QToolTip {{
    background-color: {t.bg_card};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}

/* ===== 分割线 ===== */
QFrame[frameShape="4"].horizontal {{
    border: none;
    border-top: 1px solid {t.border};
}}
"""


# 卡片快捷样式（QFrame 用 setObjectName("card") 后自动生效）
def build_card_style(theme: ThemeColors, padding: str = "16px") -> str:
    """生成卡片容器样式字符串（用于 setStyleSheet）"""
    t = theme
    return (
        f"QFrame#card {{"
        f"background-color: {t.bg_card};"
        f"border: 1px solid {t.border};"
        f"border-radius: 12px;"
        f"padding: {padding};"
        f"}}"
    )


# 字体规范
FONT_FAMILY = "system-ui, -apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, sans-serif"

# 间距规范（整数，Qt 布局用）
SPACE_XS_PX = 4
SPACE_SM_PX = 8
SPACE_MD_PX = 12
SPACE_LG_PX = 16
SPACE_XL_PX = 24
SPACE_2XL_PX = 32

# 主窗口尺寸
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 760
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 640
```

- [ ] **Step 3: 写测试**

```python
# tests/test_themes.py
import pytest
from workflow_test_desktop.config.themes import (
    LIGHT, DARK, build_theme_css, build_card_style,
    FONT_FAMILY, WINDOW_WIDTH, WINDOW_HEIGHT,
)


def test_light_theme_has_required_fields():
    assert LIGHT.bg_primary == "#FFFFFF"
    assert LIGHT.accent == "#0EA5E9"
    assert LIGHT.error == "#EF4444"


def test_dark_theme_has_required_fields():
    assert DARK.bg_primary == "#0F1117"
    assert DARK.accent == "#38BDF8"
    assert DARK.error == "#F87171"


def test_build_theme_css_returns_string():
    css = build_theme_css(LIGHT)
    assert isinstance(css, str)
    assert "QPushButton" in css
    assert "QWidget" in css
    assert "#0EA5E9" in css


def test_build_card_style():
    style = build_card_style(LIGHT)
    assert "QFrame#card" in style
    assert "#FFFFFF" in style
    assert "border-radius" in style


def test_dark_theme_css_contains_dark_colors():
    css = build_theme_css(DARK)
    assert "#0F1117" in css
    assert "#38BDF8" in css
```

- [ ] **Step 4: 运行测试**

Run: `cd /Users/ouyanggai/Documents/test-pro-max && python -m pytest tests/test_themes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add workflow_test_desktop/config/themes.py tests/test_themes.py
git commit -m "feat: upgrade themes with complete component styling for light/dark modes"
```

---

### Task 1-2: 重构主窗口（移入导航按钮）

**Files:**
- Modify: `workflow_test_desktop/ui/main_window.py`
- Modify: `workflow_test_desktop/app.py` (设置 Fusion 风格)
- Test: `tests/test_main_window.py`

- [ ] **Step 1: 读取现有 main_window.py**

Read: `workflow_test_desktop/ui/main_window.py`

- [ ] **Step 2: 修改 app.py 设置 Fusion 主题（在 QApplication 创建后）**

Read: `workflow_test_desktop/app.py`

找到 `app = QApplication(sys.argv)` 这一行，在其后添加：

```python
    app.setStyle("Fusion")
```

- [ ] **Step 3: 重写 main_window.py**

```python
"""主窗口：左侧导航 + 内容区（内嵌导航按钮）"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from workflow_test_desktop.config.themes import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    FONT_FAMILY, SPACE_LG_PX, SPACE_SM_PX, SPACE_XL_PX, LIGHT, DARK, build_theme_css,
)
from workflow_test_desktop.ui.wizard_navigator import WizardNavigator
from workflow_test_desktop.ui.steps import (
    StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport,
)
from workflow_test_desktop.ui.log_viewer import LogViewerDialog

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
        content_layout.addWidget(self._content_stack, 1)

        # 底部导航区（内嵌到内容区底部）
        nav_area = self._build_nav_area()
        content_layout.addWidget(nav_area)

        right_layout.addWidget(content_area)
        main_layout.addWidget(right_widget, 1)

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

        # 清理旧内容
        old_widget = self._content_stack.layout().itemAt(0)
        if old_widget and old_widget.widget():
            old_widget.widget().deleteLater()
        else:
            # 第一次：需要设置布局
            while self._content_stack.layout().count():
                self._content_stack.layout().takeAt(0)

        # 创建新步骤
        step_widget = steps[index](
            config=self._config,
            secrets=self._secrets,
            db=self._db,
            loop=self._loop,
            shared_data=self._shared_data,
        )
        step_widget.set_validation_callback(self._on_step_validation_result)
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

    def _on_step_validation_result(self, step_index: int, valid: bool, message: str):
        """步骤验证结果回调"""
        if valid:
            # 可以在这里做成功后的处理
            pass
        else:
            logger.warning("步骤 %d 验证失败: %s", step_index, message)

    # ─── 导航事件 ───────────────────────────────────────────────

    def _on_prev(self):
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    def _on_next(self):
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
```

- [ ] **Step 4: 写测试**

```python
# tests/test_main_window.py
import pytest
from PySide6.QtWidgets import QApplication
from workflow_test_desktop.ui.main_window import MainWindow


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_creates(app):
    mw = MainWindow(config=None, secrets=None, db=None, loop=None)
    assert mw.windowTitle() == "接口回归测试工作台"
    assert mw._current_step == 0
    assert mw._progress_bar.value() == 1
    assert mw._btn_next.text() == "下一步 →"
    assert not mw._btn_prev.isEnabled()


def test_main_window_step_navigation(app):
    mw = MainWindow(config=None, secrets=None, db=None, loop=None)
    # 点击下一步
    mw._on_next()
    assert mw._current_step == 1
    assert mw._progress_bar.value() == 2
    assert mw._btn_prev.isEnabled()

    # 点击上一步
    mw._on_prev()
    assert mw._current_step == 0
    assert mw._progress_bar.value() == 1


def test_main_window_prevents_forward_jump(app):
    mw = MainWindow(config=None, secrets=None, db=None, loop=None)
    # 尝试跳过步骤 0 直接到 2
    mw._on_nav_step_clicked(2)
    assert mw._current_step == 0

    # 正常前进到步骤 1
    mw._on_next()
    assert mw._current_step == 1
    # 尝试跳到步骤 0（可以回退）
    mw._on_nav_step_clicked(0)
    assert mw._current_step == 0


def test_main_window_progress_label(app):
    mw = MainWindow(config=None, secrets=None, db=None, loop=None)
    assert mw._progress_label.text() == "步骤 1 / 6"
    mw._on_next()
    assert mw._progress_label.text() == "步骤 2 / 6"
```

- [ ] **Step 5: 运行测试**

Run: `cd /Users/ouyanggai/Documents/test-pro-max && python -m pytest tests/test_main_window.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add workflow_test_desktop/ui/main_window.py workflow_test_desktop/app.py tests/test_main_window.py
git commit -m "refactor: move nav buttons into content area, add progress bar"
```

---

### Task 1-3: 美化导航条（WizardNavigator）

**Files:**
- Modify: `workflow_test_desktop/ui/wizard_navigator.py`

- [ ] **Step 1: 重写 wizard_navigator.py**

```python
"""竖向步骤导航条（美化版）"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_SM_PX, SPACE_MD_PX, SPACE_LG_PX, LIGHT


class WizardNavigator(QWidget):
    """竖向步骤导航条"""

    step_clicked = Signal(int)

    def __init__(self, steps: list[str], parent=None):
        super().__init__(parent)
        self._steps = steps
        self._current = 0
        self._done = []
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(200)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_SM_PX, SPACE_LG_PX, SPACE_SM_PX, SPACE_LG_PX)
        layout.setSpacing(4)

        # 标题
        title = QLabel("接口回归测试")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1A1D26; padding: 4px 8px;")
        layout.addWidget(title)
        layout.addSpacing(SPACE_LG_PX)

        self._step_buttons = []
        for i, name in enumerate(self._steps):
            step_item = self._build_step_item(i, name)
            layout.addWidget(step_item)
            self._step_buttons.append(step_item)

        layout.addStretch()
        self._update_buttons()

    def _build_step_item(self, index: int, name: str) -> QWidget:
        """构建单个步骤项（含序号圆圈 + 名称 + 连接线）"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # 序号圆圈
        self._circles = getattr(self, '_circles', [])
        circle = QLabel(str(index + 1))
        circle.setFixedSize(28, 28)
        circle.setAlignment(Qt.AlignCenter)
        circle.setFont(FONT_FAMILY)
        circle.setObjectName("step_circle")
        self._circles.append(circle)

        # 步骤名称
        label = QLabel(name)
        label.setFont(FONT_FAMILY)
        label.setObjectName("step_label")
        layout.addWidget(label, 1)
        layout.addWidget(circle)

        # 点击区域
        container.setCursor(Qt.PointingHandCursor)
        container.mousePressEvent = lambda e, idx=index: self.step_clicked.emit(idx)
        container.setObjectName("step_item")

        return container

    def set_current_step(self, index: int):
        self._current = index
        self._update_buttons()

    def mark_done(self, index: int):
        if index not in self._done:
            self._done.append(index)
        self._update_buttons()

    def _update_buttons(self):
        for i, item in enumerate(self._step_buttons):
            circle = self._circles[i]
            label = item.findChild(QLabel, "step_label")

            if i < self._current:
                state = "done"
            elif i == self._current:
                state = "active"
            else:
                state = "future"

            # 圆圈样式
            if state == "active":
                circle.setStyleSheet(
                    "background-color: #0EA5E9; color: white; border-radius: 14px; "
                    "font-weight: 700; font-size: 13px;"
                )
            elif state == "done":
                circle.setStyleSheet(
                    "background-color: #DBEAFE; color: #0EA5E9; border-radius: 14px; "
                    "font-weight: 700; font-size: 13px;"
                )
                circle.setText("✓")
            else:
                circle.setStyleSheet(
                    "background-color: transparent; color: #9CA3AF; border-radius: 14px; "
                    "border: 1.5px solid #D1D5DB; font-size: 13px;"
                )

            # 标签样式
            if state == "active":
                label.setStyleSheet("font-weight: 700; color: #1A1D26; font-size: 14px;")
            elif state == "done":
                label.setStyleSheet("color: #0EA5E9; font-size: 14px;")
            else:
                label.setStyleSheet("color: #9CA3AF; font-size: 14px;")

            item.setEnabled(i <= self._current)
```

- [ ] **Step 2: 运行测试（无新增测试，验证构建不报错）**

Run: `cd /Users/ouyanggai/Documents/test-pro-max && python -c "from workflow_test_desktop.ui.wizard_navigator import WizardNavigator; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add workflow_test_desktop/ui/wizard_navigator.py
git commit -m "style: improve wizard navigator with circle indicators and state styling"
```
