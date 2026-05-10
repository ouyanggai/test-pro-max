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
