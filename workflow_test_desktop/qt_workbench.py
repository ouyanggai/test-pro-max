from __future__ import annotations

from PySide6.QtCore import Qt
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


def create_workbench_window(snapshot: WorkbenchSnapshot) -> QMainWindow:
    window = QMainWindow()
    window.setObjectName("workbench_window")
    window.setWindowTitle("接口编排自动化测试工具")
    window.resize(1280, 760)
    _apply_styles(window)

    toolbar = QToolBar("全局操作")
    toolbar.setObjectName("global_toolbar")
    toolbar.setFixedHeight(snapshot.layout.toolbar_height_px)
    toolbar.addAction("查询可发起流程")
    toolbar.addAction("生成节点配置")
    toolbar.addAction("开始回归")
    toolbar.addAction("暂停")
    toolbar.addAction("停止")
    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
    toolbar.hide()

    shell = QWidget()
    shell.setObjectName("workbench_shell")
    shell_layout = QHBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(0)
    shell_layout.addWidget(_navigation_panel(snapshot))
    shell_layout.addWidget(_main_scroll_area())
    shell_layout.addWidget(_details_panel(snapshot))
    window.setCentralWidget(shell)

    status_bar = QStatusBar()
    status_bar.setObjectName("status_bar")
    status_bar.setFixedHeight(snapshot.layout.status_bar_height_px)
    status_bar.showMessage(snapshot.status_text)
    window.setStatusBar(status_bar)

    return window


def _navigation_panel(snapshot: WorkbenchSnapshot) -> QWidget:
    panel = QWidget()
    panel.setObjectName("navigation_panel")
    panel.setFixedWidth(236)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(18, 22, 18, 18)
    layout.setSpacing(14)

    brand = QFrame()
    brand.setObjectName("brand_panel")
    brand_layout = QHBoxLayout(brand)
    brand_layout.setContentsMargins(0, 0, 0, 0)
    brand_layout.setSpacing(10)
    mark = QLabel("测")
    mark.setObjectName("brand_mark")
    title = QLabel("接口编排回归")
    title.setProperty("role", "nav_title")
    brand_layout.addWidget(mark)
    brand_layout.addWidget(title, 1)
    layout.addWidget(brand)

    env_badge = QLabel(f"{snapshot.environment.display_name} · {snapshot.connection.message}")
    env_badge.setObjectName("environment_badge")
    env_badge.setWordWrap(True)
    layout.addWidget(env_badge)

    layout.addSpacing(8)
    layout.addWidget(_nav_button("流程回归", selected=True))
    layout.addWidget(_nav_button("账号会话"))
    layout.addWidget(_nav_button("节点配置"))
    layout.addWidget(_nav_button("运行记录"))
    layout.addWidget(_nav_button("报告中心"))
    layout.addStretch()

    footer = QLabel("本地开发验证工作台")
    footer.setObjectName("nav_footer")
    layout.addWidget(footer)
    return panel


def _main_scroll_area() -> QScrollArea:
    scroll_area = QScrollArea()
    scroll_area.setObjectName("main_panel")
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)
    scroll_area.setMinimumWidth(700)

    content = QWidget()
    content.setObjectName("main_content")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(28, 24, 28, 24)
    layout.setSpacing(18)

    layout.addWidget(_page_header())
    layout.addWidget(_metric_grid())
    layout.addWidget(_starter_account_section())
    layout.addWidget(_flow_selection_section())
    layout.addWidget(_review_node_section())
    layout.addStretch()

    scroll_area.setWidget(content)
    return scroll_area


def _page_header() -> QWidget:
    header = QWidget()
    layout = QHBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)

    copy = QWidget()
    copy_layout = QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(6)
    title = QLabel("流程回归工作台")
    title.setProperty("role", "page_title")
    subtitle = QLabel("从发起账号开始，选择流程、配置审核节点，然后按真实分支并发执行。")
    subtitle.setProperty("role", "page_subtitle")
    subtitle.setWordWrap(True)
    copy_layout.addWidget(title)
    copy_layout.addWidget(subtitle)

    primary = QPushButton("查询流程")
    primary.setObjectName("primary_button")
    secondary = QPushButton("导入配置")
    secondary.setObjectName("secondary_button")
    layout.addWidget(copy, 1)
    layout.addWidget(secondary)
    layout.addWidget(primary)
    return header


def _metric_grid() -> QWidget:
    grid_panel = QWidget()
    layout = QGridLayout(grid_panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(12)
    layout.setVerticalSpacing(12)
    metrics = (
        ("发起账号", "欧阳改", "默认超级账号，可切换"),
        ("可发起流程", "待查询", "按账号权限返回"),
        ("并发分支", "0", "选择流程后生成"),
        ("会话缓存", "待建立", "统一会话池管理"),
    )
    for index, metric in enumerate(metrics):
        layout.addWidget(_metric_card(*metric), 0, index)
    return grid_panel


def _starter_account_section() -> QFrame:
    body = QWidget()
    body.setProperty("role", "section_content")
    layout = QGridLayout(body)
    layout.setContentsMargins(0, 4, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(10)
    layout.addWidget(_field_label("发起账号"), 0, 0)
    account = QComboBox()
    account.setObjectName("starter_account_selector")
    account.addItems(["欧阳改（默认）", "按姓名或工号搜索", "从组织架构选择"])
    layout.addWidget(account, 0, 1)
    layout.addWidget(_field_label("查询方式"), 1, 0)
    mode = QComboBox()
    mode.addItems(["查询该账号可发起流程", "查询全部可发起流程"])
    layout.addWidget(mode, 1, 1)
    layout.addWidget(_action_row("查询账号", "刷新流程"), 2, 0, 1, 2)
    return _section(
        "starter_account_section",
        "1. 选择发起账号",
        "默认使用欧阳改，也可以切换为其他账号作为流程回归起点。",
        body,
    )


def _flow_selection_section() -> QFrame:
    body = QWidget()
    body.setProperty("role", "section_content")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 4, 0, 0)
    layout.setSpacing(10)
    flow = QComboBox()
    flow.setObjectName("flow_selector")
    flow.addItems(["请先查询可发起流程", "采购审批流程", "合同会签流程", "付款申请流程"])
    layout.addWidget(flow)
    layout.addWidget(_chip_row(("表单字段待解析", "节点待解析", "条件分支待解析", "并行分支待解析")))
    return _section(
        "flow_selection_section",
        "2. 选择流程",
        "选定流程后，系统会解析表单、节点、条件分支和并行分支。",
        body,
    )


def _review_node_section() -> QFrame:
    body = QWidget()
    body.setProperty("role", "section_content")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 4, 0, 0)
    layout.setSpacing(10)
    layout.addWidget(_node_rule("部门负责人审批", "按真实节点配置，可手动指定或按部门随机"))
    layout.addWidget(_node_rule("岗位审批", "支持职位随机、范围随机和固定人员"))
    layout.addWidget(_node_rule("审批人自选", "运行前确认候选人员，缺失会自动登录并缓存会话"))
    layout.addWidget(_action_row("一键指定", "一键随机", "手动配置"))
    return _section(
        "review_node_section",
        "3. 配置审核节点",
        "人员、部门、岗位、角色、发起人和表单人员等配置都按实际节点规则处理。",
        body,
    )


def _details_panel(snapshot: WorkbenchSnapshot) -> QWidget:
    panel = QWidget()
    panel.setObjectName("details_panel")
    panel.setFixedWidth(340)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(20, 24, 20, 20)
    layout.setSpacing(16)

    title = QLabel("环境与会话")
    title.setProperty("role", "panel_title")
    layout.addWidget(title)
    layout.addWidget(
        _section(
            "environment_status_section",
            "环境状态",
            "",
            _detail_lines(
                (
                    ("当前环境", snapshot.environment.display_name),
                    ("API 网关", snapshot.environment.api_gateway or "未配置"),
                    ("连接状态", snapshot.connection.message),
                )
            ),
            compact=True,
        )
    )
    layout.addWidget(
        _section(
            "session_pool_section",
            "会话池策略",
            "分支不自行登录。需要审核人身份时，通过会话管理自动登录、缓存 sid，并在失效后重新登录。",
            _chip_row(("统一获取会话", "sid 缓存", "失效重登")),
            compact=True,
        )
    )
    layout.addWidget(
        _section(
            "next_step_section",
            "下一步",
            "先查询发起账号可用流程，再进入节点人员和部门配置。",
            None,
            compact=True,
        )
    )
    layout.addStretch()
    return panel


def _section(
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
    layout = QVBoxLayout(frame)
    margin = 14 if compact else 18
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(10)

    title_label = QLabel(title)
    title_label.setProperty("role", "section_title")
    layout.addWidget(title_label)
    if description:
        body_label = QLabel(description)
        body_label.setProperty("role", "section_body")
        body_label.setWordWrap(True)
        layout.addWidget(body_label)
    if content is not None:
        layout.addWidget(content)
    return frame


def _metric_card(label: str, value: str, hint: str) -> QFrame:
    card = QFrame()
    card.setProperty("role", "metric_card")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)
    label_widget = QLabel(label)
    label_widget.setProperty("role", "metric_label")
    value_widget = QLabel(value)
    value_widget.setProperty("role", "metric_value")
    hint_widget = QLabel(hint)
    hint_widget.setProperty("role", "metric_hint")
    hint_widget.setWordWrap(True)
    layout.addWidget(label_widget)
    layout.addWidget(value_widget)
    layout.addWidget(hint_widget)
    return card


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "field_label")
    return label


def _action_row(*texts: str) -> QWidget:
    row = QWidget()
    row.setProperty("role", "action_row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for index, text in enumerate(texts):
        button = QPushButton(text)
        button.setProperty("role", "action_button")
        if index == 0:
            button.setObjectName("primary_inline_button")
        layout.addWidget(button)
    layout.addStretch()
    return row


def _chip_row(texts: tuple[str, ...]) -> QWidget:
    row = QWidget()
    row.setProperty("role", "chip_row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    for text in texts:
        chip = QLabel(text)
        chip.setProperty("role", "chip")
        layout.addWidget(chip)
    layout.addStretch()
    return row


def _node_rule(title: str, description: str) -> QFrame:
    row = QFrame()
    row.setProperty("role", "node_rule")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(12)
    dot = QLabel("")
    dot.setProperty("role", "status_dot")
    copy = QWidget()
    copy_layout = QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(3)
    title_label = QLabel(title)
    title_label.setProperty("role", "node_title")
    desc_label = QLabel(description)
    desc_label.setProperty("role", "node_desc")
    desc_label.setWordWrap(True)
    copy_layout.addWidget(title_label)
    copy_layout.addWidget(desc_label)
    layout.addWidget(dot)
    layout.addWidget(copy, 1)
    return row


def _detail_lines(lines: tuple[tuple[str, str], ...]) -> QWidget:
    panel = QWidget()
    panel.setObjectName("detail_lines")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for label, value in lines:
        row = QWidget()
        row.setProperty("role", "detail_row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        key = QLabel(label)
        key.setProperty("role", "detail_key")
        val = QLabel(value)
        val.setProperty("role", "detail_value")
        val.setWordWrap(True)
        row_layout.addWidget(key)
        row_layout.addWidget(val, 1)
        layout.addWidget(row)
    return panel


def _nav_button(text: str, *, selected: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setCheckable(True)
    button.setChecked(selected)
    button.setProperty("role", "nav_button")
    return button


def _apply_styles(window: QMainWindow) -> None:
    window.setStyleSheet(
        """
        QMainWindow#workbench_window {
            background: #edf1f5;
            font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
        }
        QToolBar#global_toolbar {
            background: #ffffff;
            border: 0;
            border-bottom: 1px solid #dbe2ea;
            padding-left: 10px;
            spacing: 10px;
        }
        QToolButton {
            color: #233147;
            background: #f4f7fb;
            border: 1px solid #dce5ef;
            border-radius: 7px;
            padding: 5px 12px;
        }
        QToolButton:hover {
            background: #eaf2fb;
            border-color: #b9cee6;
        }
        QWidget#navigation_panel {
            background: #182235;
            border-right: 1px solid #101827;
        }
        QFrame#brand_panel {
            border: 0;
            background: transparent;
        }
        QLabel#brand_mark {
            min-width: 36px;
            min-height: 36px;
            max-width: 36px;
            max-height: 36px;
            border-radius: 10px;
            background: #2dd4bf;
            color: #082f3d;
            font-size: 19px;
            font-weight: 800;
            qproperty-alignment: AlignCenter;
        }
        QLabel[role="nav_title"] {
            color: #f8fafc;
            font-size: 17px;
            font-weight: 800;
            background: transparent;
        }
        QLabel#environment_badge {
            color: #b8c7d9;
            background: #22304a;
            border: 1px solid #304260;
            border-radius: 8px;
            padding: 9px 10px;
            line-height: 18px;
        }
        QPushButton[role="nav_button"] {
            text-align: left;
            color: #c8d3e2;
            background: transparent;
            border: 0;
            border-radius: 8px;
            padding: 11px 12px;
            font-weight: 600;
        }
        QPushButton[role="nav_button"]:checked {
            color: #ffffff;
            background: #2563eb;
        }
        QPushButton[role="nav_button"]:hover {
            background: #253653;
        }
        QLabel#nav_footer {
            color: #7d8ca3;
            background: transparent;
        }
        QScrollArea#main_panel,
        QWidget#main_content {
            background: #edf1f5;
        }
        QFrame[role="section_card"] QWidget,
        QWidget[role="section_content"],
        QWidget[role="action_row"],
        QWidget[role="chip_row"],
        QWidget#detail_lines,
        QWidget[role="detail_row"] {
            background-color: transparent;
        }
        QWidget#details_panel {
            background: #f8fafc;
            border-left: 1px solid #d9e1eb;
        }
        QLabel[role="page_title"] {
            color: #111827;
            font-size: 24px;
            font-weight: 900;
            background: transparent;
        }
        QLabel[role="page_subtitle"] {
            color: #5d6b7c;
            font-size: 13px;
            background: transparent;
        }
        QLabel[role="panel_title"] {
            color: #111827;
            font-size: 17px;
            font-weight: 900;
            background: transparent;
        }
        QPushButton#primary_button {
            color: #ffffff;
            background: #0f766e;
            border: 0;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 800;
        }
        QPushButton#secondary_button,
        QPushButton[role="action_button"] {
            color: #25344a;
            background: #ffffff;
            border: 1px solid #d6e0eb;
            border-radius: 8px;
            padding: 9px 14px;
            font-weight: 700;
        }
        QPushButton#primary_inline_button {
            color: #ffffff;
            background: #2563eb;
            border-color: #2563eb;
        }
        QFrame[role="section_card"],
        QFrame[role="metric_card"] {
            background: #ffffff;
            border: 1px solid #dce5ef;
            border-radius: 10px;
        }
        QFrame[role="section_card"] {
            border-top: 3px solid #0f766e;
        }
        QLabel[role="section_title"] {
            color: #111827;
            font-size: 15px;
            font-weight: 900;
            border: 0;
            background: transparent;
        }
        QLabel[role="section_body"] {
            color: #5b6778;
            border: 0;
            background: transparent;
            line-height: 19px;
        }
        QLabel[role="metric_label"],
        QLabel[role="metric_hint"],
        QLabel[role="detail_key"] {
            color: #728197;
            background: transparent;
        }
        QLabel[role="metric_value"] {
            color: #111827;
            font-size: 21px;
            font-weight: 900;
            background: transparent;
        }
        QLabel[role="detail_value"] {
            color: #1f2937;
            font-weight: 700;
            background: transparent;
        }
        QLabel[role="field_label"] {
            color: #4b5870;
            font-weight: 800;
            background: transparent;
        }
        QComboBox {
            color: #182235;
            background: #f8fafc;
            border: 1px solid #d4deea;
            border-radius: 8px;
            padding: 8px 10px;
            min-height: 22px;
        }
        QLabel[role="chip"] {
            color: #0f3f3d;
            background: #dff7f2;
            border: 1px solid #b7e8dc;
            border-radius: 10px;
            padding: 5px 9px;
            font-weight: 700;
        }
        QFrame[role="node_rule"] {
            background: #f8fafc;
            border: 1px solid #e1e8f0;
            border-radius: 9px;
        }
        QLabel[role="status_dot"] {
            min-width: 10px;
            min-height: 10px;
            max-width: 10px;
            max-height: 10px;
            border-radius: 5px;
            background: #f59e0b;
        }
        QLabel[role="node_title"] {
            color: #172033;
            font-weight: 900;
            background: transparent;
        }
        QLabel[role="node_desc"] {
            color: #5d6b7c;
            background: transparent;
        }
        QStatusBar#status_bar {
            background: #ffffff;
            color: #374151;
            border-top: 1px solid #d9e1eb;
        }
        """
    )
