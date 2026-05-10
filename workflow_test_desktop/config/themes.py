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


# 圆角规范
RADIUS_BUTTON = "8px"
RADIUS_CARD = "12px"
RADIUS_MODAL = "16px"

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
