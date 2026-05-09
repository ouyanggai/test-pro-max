from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPaintEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from workflow_test_desktop.workbench import WorkbenchSnapshot

# Brand color — kept in sync with stylesheet accent #3b4fbd
_BRAND_COLOR = QColor(59, 79, 189)


# ---------------------------------------------------------------------------
# Brand Icon — minimal geometric mark drawn with QPainter
# ---------------------------------------------------------------------------


class BrandIcon(QWidget):
    """Indigo square with two white horizontal bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(32, 32)

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_BRAND_COLOR)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        painter.drawPath(path)
        painter.setPen(
            QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(8, 11, 24, 11)
        painter.drawLine(8, 21, 24, 21)


# ---------------------------------------------------------------------------
# Connection Status Dot
# ---------------------------------------------------------------------------


class StatusDot(QLabel):
    """Small 8x8 colored dot that reflects connection status."""

    _COLORS: dict[str, str] = {
        "connected": "22c55e",
        "failed": "ef4444",
        "unconfigured": "fbbf24",
        "missing_secrets": "fbbf24",
        "unchecked": "9ca3af",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self.set_status("unchecked")

    def set_status(self, status: str) -> None:
        key = status.split(":")[0].strip()
        hex_color = self._COLORS.get(key, "9ca3af")
        self.setStyleSheet(f"background: #{hex_color}; border-radius: 4px;")


# ---------------------------------------------------------------------------
# Top-level Window Builder
# ---------------------------------------------------------------------------

def create_workbench_window(snapshot: WorkbenchSnapshot) -> QMainWindow:
    window = QMainWindow()
    window.setObjectName("workbench_window")
    window.setWindowTitle("接口编排自动化测试工具")
    window.resize(1360, 820)
    _apply_base_styles(window)

    toolbar = _build_toolbar()
    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
    toolbar.hide()  # P0 阶段不显示，等功能接入

    shell = QWidget()
    shell.setObjectName("workbench_shell")
    shell_layout = QHBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(0)
    shell_layout.addWidget(_build_navigation_panel(snapshot))
    shell_layout.addWidget(_build_main_scroll_area(snapshot))
    shell_layout.addWidget(_build_details_panel(snapshot))
    window.setCentralWidget(shell)

    status_bar = QStatusBar()
    status_bar.setObjectName("status_bar")
    status_bar.setFixedHeight(snapshot.layout.status_bar_height_px)
    status_bar.showMessage(snapshot.status_text)
    window.setStatusBar(status_bar)

    return window


# ---------------------------------------------------------------------------
# Toolbar
# ---------------------------------------------------------------------------

def _build_toolbar() -> QToolBar:
    toolbar = QToolBar("全局操作")
    toolbar.setObjectName("global_toolbar")
    toolbar.setFixedHeight(40)
    return toolbar


# ---------------------------------------------------------------------------
# Navigation Panel
# ---------------------------------------------------------------------------

def _build_navigation_panel(snapshot: WorkbenchSnapshot) -> QWidget:
    panel = QWidget()
    panel.setObjectName("navigation_panel")
    panel.setFixedWidth(240)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(16, 20, 16, 20)
    layout.setSpacing(0)

    # Brand row
    brand = QWidget()
    brand.setObjectName("brand_row")
    brand_layout = QHBoxLayout(brand)
    brand_layout.setContentsMargins(0, 0, 0, 0)
    brand_layout.setSpacing(10)
    brand_layout.addWidget(BrandIcon())
    title = QLabel("流程回归")
    title.setObjectName("brand_title")
    title.setStyleSheet("font-size: 15px; font-weight: 600; color: #0f172a; background: transparent;")
    brand_layout.addWidget(title)
    brand_layout.addStretch()
    layout.addWidget(brand)

    layout.addSpacing(28)

    # Env badge — vertical so both name and message are visible
    env_badge = QWidget()
    env_badge.setObjectName("env_badge")
    env_layout = QVBoxLayout(env_badge)
    env_layout.setContentsMargins(10, 8, 10, 8)
    env_layout.setSpacing(4)
    dot = StatusDot()
    dot.set_status(snapshot.connection.status)
    name_row = QWidget()
    name_row.setStyleSheet("background: transparent; border: none;")
    name_layout = QHBoxLayout(name_row)
    name_layout.setContentsMargins(0, 0, 0, 0)
    name_layout.setSpacing(6)
    name_layout.addWidget(dot)
    env_name = QLabel(snapshot.environment.display_name)
    env_name.setObjectName("env_name")
    name_layout.addWidget(env_name)
    name_layout.addStretch()
    env_msg = QLabel(snapshot.connection.message)
    env_msg.setObjectName("env_msg")
    env_layout.addWidget(name_row)
    env_layout.addWidget(env_msg)
    layout.addWidget(env_badge)

    layout.addSpacing(24)

    # Nav section label
    nav_label = QLabel("导航")
    nav_label.setObjectName("nav_section_label")
    layout.addWidget(nav_label)

    layout.addSpacing(8)

    # Nav items
    nav_items = [
        ("工作台", True),
        ("发起账号", False),
        ("流程库", False),
        ("节点配置", False),
        ("运行报告", False),
    ]
    for text, selected in nav_items:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(selected)
        btn.setObjectName(f"nav_{text}")
        layout.addWidget(btn)

    layout.addStretch()

    # Footer
    footer = QLabel("本地开发验证工作台 v0.1")
    footer.setObjectName("nav_footer")
    layout.addWidget(footer)
    return panel


# ---------------------------------------------------------------------------
# Main Scroll Area
# ---------------------------------------------------------------------------

def _build_main_scroll_area(snapshot: WorkbenchSnapshot) -> QScrollArea:
    scroll_area = QScrollArea()
    scroll_area.setObjectName("main_panel")
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)
    scroll_area.setMinimumWidth(680)

    content = QWidget()
    content.setObjectName("main_content")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(32, 28, 32, 32)
    layout.setSpacing(24)

    layout.addWidget(_build_page_header())
    layout.addWidget(_build_hero_panel(snapshot))
    layout.addWidget(_build_metric_grid())
    layout.addWidget(_build_starter_account_section())
    layout.addWidget(_build_flow_selection_section())
    layout.addWidget(_build_review_node_section())
    layout.addStretch()

    scroll_area.setWidget(content)
    return scroll_area


def _build_page_header() -> QWidget:
    header = QWidget()
    header.setObjectName("page_header")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    layout.addStretch()

    btn_import = QPushButton("导入配置")
    btn_import.setObjectName("btn_import")
    btn_query = QPushButton("查询流程")
    btn_query.setObjectName("btn_query")
    layout.addWidget(btn_import)
    layout.addWidget(btn_query)
    return header


def _build_hero_panel(snapshot: WorkbenchSnapshot) -> QFrame:
    hero = QFrame()
    hero.setObjectName("hero_panel")
    layout = QHBoxLayout(hero)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(24)

    # Left: copy
    copy = QWidget()
    copy.setObjectName("hero_copy")
    copy_layout = QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(8)

    eyebrow = QLabel("推荐回归起点")
    eyebrow.setObjectName("hero_eyebrow")
    title = QLabel("从欧阳改开始，快速拉起全流程回归")
    title.setObjectName("hero_title")
    title.setWordWrap(True)
    desc = QLabel("先查询账号可发起流程，再按真实节点配置审核人员、部门、岗位和候选范围。")
    desc.setObjectName("hero_desc")
    desc.setWordWrap(True)

    copy_layout.addWidget(eyebrow)
    copy_layout.addWidget(title)
    copy_layout.addWidget(desc)
    copy_layout.addWidget(_build_chip_row(["默认超级账号", "会话统一管理", snapshot.environment.display_name]))
    copy_layout.addSpacing(4)
    copy_layout.addWidget(_build_action_row(["开始查询", "选择其他账号"]))

    # Right: stage tracker
    stage = QFrame()
    stage.setObjectName("hero_stage")
    stage_layout = QVBoxLayout(stage)
    stage_layout.setContentsMargins(16, 14, 16, 14)
    stage_layout.setSpacing(0)
    stage_layout.addWidget(_build_stage_line("发起账号", "欧阳改", active=True, done=True))
    stage_layout.addWidget(_build_stage_divider())
    stage_layout.addWidget(_build_stage_line("流程解析", "等待选择流程", active=False, done=False))
    stage_layout.addWidget(_build_stage_divider())
    stage_layout.addWidget(_build_stage_line("分支执行", "按节点配置并发", active=False, done=False))
    stage_layout.addStretch()

    layout.addWidget(copy, 3)
    layout.addWidget(stage, 2)
    return hero


def _build_metric_grid() -> QWidget:
    grid = QWidget()
    grid.setObjectName("metric_grid")
    layout = QGridLayout(grid)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(12)
    layout.setVerticalSpacing(12)
    metrics = [
        ("发起账号", "欧阳改", "默认超级账号，可切换"),
        ("可发起流程", "待查询", "按账号权限返回"),
        ("并发分支", "0", "选择流程后生成"),
        ("会话缓存", "待建立", "统一会话池管理"),
    ]
    for col, (label, value, hint) in enumerate(metrics):
        layout.addWidget(_build_metric_card(label, value, hint), 0, col)
    return grid


def _build_starter_account_section() -> QFrame:
    body = QWidget()
    body.setObjectName("section_body")
    body_layout = QGridLayout(body)
    body_layout.setContentsMargins(0, 4, 0, 0)
    body_layout.setHorizontalSpacing(12)
    body_layout.setVerticalSpacing(10)

    account_label = QLabel("发起账号")
    account_label.setObjectName("field_label")
    account_combo = QComboBox()
    account_combo.setObjectName("starter_account_selector")
    account_combo.addItems(["欧阳改（默认）", "按姓名或工号搜索", "从组织架构选择"])
    body_layout.addWidget(account_label, 0, 0)
    body_layout.addWidget(account_combo, 0, 1)

    mode_label = QLabel("查询方式")
    mode_label.setObjectName("field_label")
    mode_combo = QComboBox()
    mode_combo.addItems(["查询该账号可发起流程", "查询全部可发起流程"])
    body_layout.addWidget(mode_label, 1, 0)
    body_layout.addWidget(mode_combo, 1, 1)

    body_layout.addWidget(_build_action_row(["查询账号", "刷新流程"]), 2, 0, 1, 2)

    return _build_section(
        "starter_account_section",
        "1. 选择发起账号",
        "默认使用欧阳改，也可以切换为其他账号作为流程回归起点。",
        body,
    )


def _build_flow_selection_section() -> QFrame:
    body = QWidget()
    body.setObjectName("section_body")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(0, 4, 0, 0)
    body_layout.setSpacing(10)
    flow = QComboBox()
    flow.setObjectName("flow_selector")
    flow.addItems(["请先查询可发起流程", "采购审批流程", "合同会签流程", "付款申请流程"])
    body_layout.addWidget(flow)
    body_layout.addWidget(_build_chip_row(["表单字段待解析", "节点待解析", "条件分支待解析", "并行分支待解析"]))
    return _build_section(
        "flow_selection_section",
        "2. 选择流程",
        "选定流程后，系统会解析表单、节点、条件分支和并行分支。",
        body,
    )


def _build_review_node_section() -> QFrame:
    body = QWidget()
    body.setObjectName("section_body")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(0, 4, 0, 0)
    body_layout.setSpacing(8)
    body_layout.addWidget(_build_node_rule("部门负责人审批", "按真实节点配置，可手动指定或按部门随机"))
    body_layout.addWidget(_build_node_rule("岗位审批", "支持职位随机、范围随机和固定人员"))
    body_layout.addWidget(_build_node_rule("审批人自选", "运行前确认候选人员，缺失会自动登录并缓存会话"))
    body_layout.addWidget(_build_action_row(["一键指定", "一键随机", "手动配置"]))
    return _build_section(
        "review_node_section",
        "3. 配置审核节点",
        "人员、部门、岗位、角色、发起人和表单人员等配置都按实际节点规则处理。",
        body,
    )


# ---------------------------------------------------------------------------
# Details Panel
# ---------------------------------------------------------------------------

def _build_details_panel(snapshot: WorkbenchSnapshot) -> QWidget:
    panel = QWidget()
    panel.setObjectName("details_panel")
    panel.setFixedWidth(300)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(16, 20, 16, 20)
    layout.setSpacing(16)

    title = QLabel("环境与会话")
    title.setObjectName("panel_title")
    layout.addWidget(title)

    layout.addWidget(_build_section(
        "environment_status_section",
        "环境状态",
        "",
        _build_detail_rows([
            ("当前环境", snapshot.environment.display_name),
            ("API 网关", snapshot.environment.api_gateway or "未配置"),
            ("连接状态", snapshot.connection.message),
        ]),
        compact=True,
    ))

    layout.addWidget(_build_section(
        "session_pool_section",
        "会话池策略",
        "分支不自行登录。需要审核人身份时，通过会话管理自动登录、缓存 sid，并在失效后重新登录。",
        _build_chip_row(["统一获取会话", "sid 缓存", "失效重登"]),
        compact=True,
    ))

    layout.addWidget(_build_section(
        "next_step_section",
        "下一步",
        "先查询发起账号可用流程，再进入节点人员和部门配置。",
        None,
        compact=True,
    ))

    layout.addStretch()
    return panel


# ---------------------------------------------------------------------------
# Reusable Component Builders
# ---------------------------------------------------------------------------

def _build_section(
    object_name: str,
    title: str,
    description: str,
    content: QWidget | None = None,
    *,
    compact: bool = False,
) -> QFrame:
    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("role", "section_card")
    frame.setStyleSheet("background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
    layout = QVBoxLayout(frame)
    margin = 14 if compact else 18
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(10)

    t = QLabel(title)
    t.setObjectName("section_title")
    layout.addWidget(t)
    if description:
        d = QLabel(description)
        d.setObjectName("section_body")
        d.setWordWrap(True)
        layout.addWidget(d)
    if content is not None:
        layout.addWidget(content)
    return frame


def _build_metric_card(label: str, value: str, hint: str) -> QFrame:
    card = QFrame()
    card.setObjectName(f"metric_{label}")
    card.setStyleSheet(
        "background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;"
    )
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(3)

    lbl = QLabel(label)
    lbl.setObjectName("metric_label")
    val = QLabel(value)
    val.setObjectName("metric_value")
    hnt = QLabel(hint)
    hnt.setObjectName("metric_hint")
    hnt.setWordWrap(True)

    layout.addWidget(lbl)
    layout.addWidget(val)
    layout.addWidget(hnt)
    return card


def _build_chip_row(texts: tuple[str, ...] | list[str]) -> QWidget:
    row = QWidget()
    row.setObjectName("chip_row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    for i, text in enumerate(texts):
        chip = QLabel(text)
        chip.setObjectName(f"chip_{i}")
        layout.addWidget(chip)
    layout.addStretch()
    return row


def _build_action_row(texts: list[str]) -> QWidget:
    row = QWidget()
    row.setObjectName("action_row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for i, text in enumerate(texts):
        btn = QPushButton(text)
        btn.setObjectName(f"action_btn_{i}")
        layout.addWidget(btn)
    layout.addStretch()
    return row


def _build_node_rule(title: str, description: str) -> QFrame:
    row = QFrame()
    row.setObjectName("node_rule")
    row.setStyleSheet(
        "background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;"
    )
    layout = QHBoxLayout(row)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(10)

    dot = QLabel()
    dot.setFixedSize(8, 8)
    dot.setStyleSheet("background: #3b82f6; border-radius: 4px;")

    copy = QWidget()
    copy_layout = QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(2)

    t = QLabel(title)
    t.setObjectName("node_title")
    d = QLabel(description)
    d.setObjectName("node_desc")
    d.setWordWrap(True)

    copy_layout.addWidget(t)
    copy_layout.addWidget(d)
    layout.addWidget(dot)
    layout.addWidget(copy, 1)
    return row


def _build_stage_line(label: str, value: str, *, active: bool, done: bool) -> QWidget:
    row = QFrame()
    row.setObjectName("stage_line")
    row.setStyleSheet("background: transparent; border: none;")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 6, 0, 6)
    layout.setSpacing(10)

    marker = QLabel("✓" if done else ("●" if active else "○"))
    marker.setObjectName("stage_marker")

    copy = QWidget()
    copy_layout = QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(1)
    lbl = QLabel(label)
    lbl.setObjectName("stage_label")
    val = QLabel(value)
    val.setObjectName("stage_value")
    copy_layout.addWidget(lbl)
    copy_layout.addWidget(val)

    layout.addWidget(marker)
    layout.addWidget(copy, 1)
    return row


def _build_stage_divider() -> QWidget:
    div = QFrame()
    div.setObjectName("stage_divider")
    div.setFixedSize(1, 16)
    div.setStyleSheet("background: #cbd5e1; border: none;")
    return div


def _build_detail_rows(rows: list[tuple[str, str]]) -> QWidget:
    panel = QWidget()
    panel.setObjectName("detail_rows")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for key, val in rows:
        row = QWidget()
        row.setObjectName("detail_row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        k = QLabel(key)
        k.setObjectName("detail_key")
        v = QLabel(val)
        v.setObjectName("detail_value")
        v.setWordWrap(True)
        row_layout.addWidget(k)
        row_layout.addWidget(v, 1)
        layout.addWidget(row)
    return panel


# ---------------------------------------------------------------------------
# Global Stylesheet
# ---------------------------------------------------------------------------

def _apply_base_styles(window: QMainWindow) -> None:
    window.setStyleSheet("""
        /* ── Reset ─────────────────────────────────────────────── */
        * {
            font-family: "PingFang SC", "Helvetica Neue", sans-serif;
        }

        /* ── Window ─────────────────────────────────────────────── */
        QMainWindow#workbench_window {
            background: #f1f5f9;
        }

        /* ── Toolbar ───────────────────────────────────────────── */
        QToolBar#global_toolbar {
            background: #ffffff;
            border: none;
            border-bottom: 1px solid #e2e8f0;
            padding: 0 12px;
        }

        /* ── Nav Panel ─────────────────────────────────────────── */
        QWidget#navigation_panel {
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        QWidget#brand_row {
            background: transparent;
        }
        QLabel#env_badge {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
        }
        QLabel#env_name {
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            background: transparent;
        }
        QLabel#env_msg {
            font-size: 11px;
            color: #64748b;
            background: transparent;
        }
        QLabel#nav_section_label {
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            background: transparent;
        }

        /* ── Nav Buttons ───────────────────────────────────────── */
        QPushButton[objectName^="nav_"] {
            text-align: left;
            padding: 8px 10px;
            font-size: 13px;
            font-weight: 400;
            color: #475569;
            background: transparent;
            border: none;
            border-radius: 6px;
        }
        QPushButton[objectName^="nav_"]:checked {
            color: #1e40af;
            background: #eff6ff;
            font-weight: 500;
        }

        /* ── Nav Footer ───────────────────────────────────────── */
        QLabel#nav_footer {
            font-size: 11px;
            color: #94a3b8;
            background: transparent;
        }

        /* ── Main Panel ───────────────────────────────────────── */
        QScrollArea#main_panel,
        QWidget#main_content {
            background: #f1f5f9;
            border: none;
        }

        /* ── Hero Panel ───────────────────────────────────────── */
        QFrame#hero_panel {
            background: #1e40af;
            border: none;
            border-radius: 10px;
        }
        QWidget#hero_copy,
        QWidget#hero_stage {
            background: transparent;
            border: none;
        }
        QFrame#hero_stage {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
        }

        /* ── Hero Typography ───────────────────────────────────── */
        QLabel[objectName="hero_eyebrow"] {
            font-size: 11px;
            font-weight: 600;
            color: rgba(255,255,255,0.55);
            background: transparent;
        }
        QLabel[objectName="hero_title"] {
            font-size: 22px;
            font-weight: 600;
            color: #ffffff;
            background: transparent;
        }
        QLabel[objectName="hero_desc"] {
            font-size: 13px;
            color: rgba(255,255,255,0.7);
            background: transparent;
        }

        /* ── Chips ────────────────────────────────────────────── */
        QLabel[objectName^="chip_"] {
            font-size: 11px;
            font-weight: 500;
            color: #3b82f6;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 4px;
            padding: 3px 8px;
        }

        /* ── Action Buttons ────────────────────────────────────── */
        QPushButton#btn_query {
            background: #1e40af;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton#btn_query:hover {
            background: #1e3a8a;
        }
        QPushButton#btn_query:pressed {
            background: #1d3a9a;
        }
        QPushButton#btn_import {
            background: #ffffff;
            color: #475569;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton#btn_import:hover {
            background: #f8fafc;
            border-color: #94a3b8;
        }
        QWidget#action_row > QPushButton {
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            padding: 7px 14px;
        }
        QPushButton#action_btn_0 {
            background: #1e40af;
            color: #ffffff;
            border: none;
        }
        QPushButton#action_btn_0:hover {
            background: #1e3a8a;
        }
        QPushButton#action_btn_1,
        QPushButton#action_btn_2,
        QPushButton#action_btn_3 {
            background: #ffffff;
            color: #475569;
            border: 1px solid #cbd5e1;
        }
        QPushButton#action_btn_1:hover,
        QPushButton#action_btn_2:hover,
        QPushButton#action_btn_3:hover {
            background: #f8fafc;
            border-color: #94a3b8;
        }

        /* ── Metric Cards ─────────────────────────────────────── */
        QLabel[objectName="metric_label"] {
            font-size: 11px;
            color: #64748b;
            background: transparent;
        }
        QLabel[objectName="metric_value"] {
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
            background: transparent;
        }
        QLabel[objectName="metric_hint"] {
            font-size: 11px;
            color: #94a3b8;
            background: transparent;
        }

        /* ── Section Cards ─────────────────────────────────────── */
        QLabel[objectName="section_title"] {
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            background: transparent;
        }
        QLabel[objectName="section_body"] {
            font-size: 12px;
            color: #64748b;
            background: transparent;
        }

        /* ── Field Labels ──────────────────────────────────────── */
        QLabel[objectName="field_label"] {
            font-size: 12px;
            font-weight: 500;
            color: #475569;
            background: transparent;
        }

        /* ── Combo Boxes ───────────────────────────────────────── */
        QComboBox {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 13px;
            color: #0f172a;
        }
        QComboBox:hover {
            border-color: #94a3b8;
        }
        QComboBox:focus {
            border-color: #3b82f6;
        }

        /* ── Node Rules ───────────────────────────────────────── */
        QLabel[objectName="node_title"] {
            font-size: 13px;
            font-weight: 500;
            color: #1e293b;
            background: transparent;
        }
        QLabel[objectName="node_desc"] {
            font-size: 12px;
            color: #64748b;
            background: transparent;
        }

        /* ── Stage Tracker ─────────────────────────────────────── */
        QLabel[objectName="stage_marker"] {
            font-size: 14px;
            background: transparent;
        }
        QLabel[objectName="stage_label"] {
            font-size: 11px;
            color: rgba(255,255,255,0.5);
            background: transparent;
        }
        QLabel[objectName="stage_value"] {
            font-size: 13px;
            font-weight: 600;
            color: #ffffff;
            background: transparent;
        }

        /* ── Details Panel ────────────────────────────────────── */
        QWidget#details_panel {
            background: #f8fafc;
            border-left: 1px solid #e2e8f0;
        }
        QLabel[objectName="panel_title"] {
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            background: transparent;
        }
        QLabel[objectName="detail_key"] {
            font-size: 11px;
            color: #64748b;
            background: transparent;
        }
        QLabel[objectName="detail_value"] {
            font-size: 12px;
            font-weight: 500;
            color: #1e293b;
            background: transparent;
        }

        /* ── Status Bar ───────────────────────────────────────── */
        QStatusBar#status_bar {
            background: #ffffff;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
        }
    """)
