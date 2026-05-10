"""双主题调色板（浅色 / 深色）"""
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
    accent: Final[str]       # 主强调色（天蓝）
    success: Final[str]
    warning: Final[str]
    error: Final[str]
    sidebar_bg: Final[str]


LIGHT: ThemeColors = ThemeColors(
    bg_primary="#FFFFFF",
    bg_secondary="#F4F5F7",
    bg_card="#FFFFFF",
    border="#E2E4E9",
    text_primary="#1A1D26",
    text_secondary="#6B7280",
    accent="#0EA5E9",
    success="#10B981",
    warning="#F59E0B",
    error="#EF4444",
    sidebar_bg="#F1F3F5",
)

DARK: ThemeColors = ThemeColors(
    bg_primary="#0F1117",
    bg_secondary="#161921",
    bg_card="#1C1F2A",
    border="#2A2D3A",
    text_primary="#E8EAF0",
    text_secondary="#8B90A0",
    accent="#38BDF8",
    success="#34D399",
    warning="#FBBF24",
    error="#F87171",
    sidebar_bg="#13151E",
)


# CSS 变量映射
THEME_CSS_VAR_MAP = {
    "bg-primary": "bg_primary",
    "bg-secondary": "bg_secondary",
    "bg-card": "bg_card",
    "border-color": "border",
    "text-primary": "text_primary",
    "text-secondary": "text_secondary",
    "accent-color": "accent",
    "success-color": "success",
    "warning-color": "warning",
    "error-color": "error",
    "sidebar-bg": "sidebar_bg",
}


def build_theme_css(theme: ThemeColors) -> str:
    """生成 CSS 变量块，300ms 全局过渡用于主题切换"""
    lines = [":root {"]
    for css_var, attr in THEME_CSS_VAR_MAP.items():
        lines.append(f"  --{css_var}: {getattr(theme, attr)};")
    lines.append("  --transition-theme: 300ms ease;")
    lines.append("}")
    lines.append(
        "*{transition: background-color var(--transition-theme), "
        "border-color var(--transition-theme), color var(--transition-theme);}"
    )
    return "\n".join(lines)


# 字体规范（系统字体栈，不打包字体）
FONT_FAMILY = "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif"

# 圆角规范
RADIUS_BUTTON = "8px"
RADIUS_CARD = "12px"
RADIUS_MODAL = "16px"

# 间距规范（基准 4px）
SPACE_XS = "4px"
SPACE_SM = "8px"
SPACE_MD = "12px"
SPACE_LG = "16px"
SPACE_XL = "24px"
SPACE_2XL = "32px"

# 主窗口尺寸
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 760
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 640
