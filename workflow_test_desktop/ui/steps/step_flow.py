"""步骤2：流程选择 - 卡片网格 + API加载"""
from __future__ import annotations

import asyncio
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGridLayout, QFrame,
    QScrollArea, QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX
from workflow_test_desktop.api.client import ApiClient
from workflow_test_desktop.ui.error_bus import ErrorBus

logger = logging.getLogger(__name__)


class FlowCard(QFrame):
    """流程卡片（选中高亮）"""

    clicked = Signal(dict)

    def __init__(self, flow: dict, parent=None):
        super().__init__(parent)
        self._flow = flow
        self._selected = False
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self._name_label = QLabel(self._flow.get("flowTemplateName", ""))
        self._name_label.setFont(FONT_FAMILY)
        self._name_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #1A1D26;")
        layout.addWidget(self._name_label)

        self._cat_label = QLabel(self._flow.get("flowGroupName", ""))
        self._cat_label.setFont(FONT_FAMILY)
        self._cat_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self._cat_label)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(
                "QFrame { background-color: #EFF6FF; border: 2px solid #0EA5E9; "
                "border-radius: 10px; }"
            )
        else:
            self.setStyleSheet(
                "QFrame { background-color: #FFFFFF; border: 1px solid #E2E4E9; "
                "border-radius: 10px; }"
                "QFrame:hover { border-color: #93C5FD; background-color: #F8FAFF; }"
            )

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    def get_flow(self) -> dict:
        return self._flow

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._flow)
        super().mousePressEvent(event)


class StepFlow(QWidget):
    """流程选择步骤"""

    flow_selected = Signal(str, str)  # flow_id, flow_name

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._flows: list[dict] = []
        self._selected_flow: dict | None = None
        self._card_widgets: list[FlowCard] = []
        self._setup_ui()
        self._load_flows()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("选择流程")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 搜索工具栏
        toolbar = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setFont(FONT_FAMILY)
        self._search_input.setPlaceholderText("搜索流程名称...")
        self._search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_input, 1)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setFont(FONT_FAMILY)
        self._refresh_btn.setProperty("theme", "secondary")
        self._refresh_btn.setFixedWidth(80)
        self._refresh_btn.clicked.connect(self._load_flows)
        toolbar.addWidget(self._refresh_btn)
        layout.addLayout(toolbar)

        # 加载状态
        self._loading_label = QLabel("加载中...")
        self._loading_label.setFont(FONT_FAMILY)
        self._loading_label.setStyleSheet("color: #6B7280; padding: 20px;")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setVisible(False)
        layout.addWidget(self._loading_label)

        # 流程卡片区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._card_container = QWidget()
        self._card_grid = QGridLayout(self._card_container)
        self._card_grid.setSpacing(12)
        self._card_grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._card_container)
        layout.addWidget(scroll, 1)

        # 提示
        self._hint = QLabel("请点击选择流程")
        self._hint.setFont(FONT_FAMILY)
        self._hint.setStyleSheet("color: #F59E0B; font-size: 13px;")
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setVisible(False)
        layout.addWidget(self._hint)

        # 验证错误提示
        self._error_label = QLabel("")
        self._error_label.setFont(FONT_FAMILY)
        self._error_label.setStyleSheet("color: #EF4444; font-size: 13px; padding: 8px 12px;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

    # ─── 加载流程 ───────────────────────────────────────────────

    def _load_flows(self):
        """从 API 加载流程列表"""
        self._loading_label.setVisible(True)
        self._hint.setVisible(False)
        self._error_label.setVisible(False)
        self._refresh_btn.setEnabled(False)

        async def _fetch():
            from workflow_test_desktop.api.client import ApiError
            gateway = self._config.gateway_url
            if not gateway:
                ErrorBus().emit("配置错误", "GATEWAY_URL 未配置", source="StepFlow")
                self._set_loaded([])
                return
            try:
                async with ApiClient(gateway) as client:
                    resp = await client.post(
                        "/web/flowTemplateApi/list",
                        json={"page": 1, "size": 100, "status": "enable"},
                    )
                    data = resp.json()
                    if data.get("isSuccess") is False:
                        ErrorBus().emit(
                            "加载流程失败",
                            data.get("message", "接口返回错误"),
                            source="StepFlow",
                        )
                        self._set_loaded([])
                    elif data.get("code") == 0:
                        records = data.get("data", {}).get("records", [])
                        self._set_loaded(records)
            except ApiError as e:
                ErrorBus().emit("加载流程失败", e.message, detail=e.detail, source="StepFlow")
                self._set_loaded([])
            except Exception as e:
                ErrorBus().emit("加载流程失败", str(e), source="StepFlow")
                self._set_loaded([])

        def _run():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            asyncio.ensure_future(_fetch(), loop=loop)

        QTimer.singleShot(50, _run)

    def _set_loaded(self, flows: list[dict]):
        """在主线程设置加载结果"""
        self._flows = flows
        self._loading_label.setVisible(False)
        self._refresh_btn.setEnabled(True)
        self._render_cards("")

    # ─── 渲染卡片 ───────────────────────────────────────────────

    def _render_cards(self, keyword: str):
        """渲染流程卡片网格"""
        # 清除旧卡片
        for w in self._card_widgets:
            w.deleteLater()
        self._card_widgets.clear()

        kw = keyword.lower().strip()
        filtered = self._flows
        if kw:
            filtered = [f for f in self._flows if kw in f.get("flowTemplateName", "").lower()]

        for i, flow in enumerate(filtered):
            card = FlowCard(flow)
            card.clicked.connect(self._on_card_clicked)
            row, col = divmod(i, 2)
            self._card_grid.addWidget(card, row, col)
            self._card_widgets.append(card)

        if not filtered:
            empty = QLabel("没有找到匹配的流程" if keyword else "暂无可用流程")
            empty.setFont(FONT_FAMILY)
            empty.setStyleSheet("color: #9CA3AF; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self._card_grid.addWidget(empty, 0, 0, 1, 2)

    def _on_search(self, text: str):
        self._render_cards(text)

    # ─── 卡片点击 ───────────────────────────────────────────────

    def _on_card_clicked(self, flow: dict):
        self._selected_flow = flow

        # 更新卡片选中状态
        for card in self._card_widgets:
            card.set_selected(card.get_flow() == flow)

        flow_id = flow.get("flowTemplateId", "")
        flow_name = flow.get("flowTemplateName", "")
        self._shared_data["flow_id"] = flow_id
        self._shared_data["flow_name"] = flow_name
        self._hint.setVisible(False)
        self._error_label.setVisible(False)
        logger.info("选择流程: %s (%s)", flow_name, flow_id)
        self.flow_selected.emit(flow_id, flow_name)

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        if not self._selected_flow:
            self._error_label.setText("⚠ 请先选择一个流程")
            self._error_label.setVisible(True)
            self._shake_widget(self._error_label)
            return False, "请先选择一个流程"
        return True, ""

    def _shake_widget(self, widget):
        """抖动动画（3次左右晃动）"""
        anim = QPropertyAnimation(widget, b"pos")
        orig_pos = widget.pos()
        anim.setDuration(400)
        anim.setKeyValueAt(0, orig_pos)
        anim.setKeyValueAt(0.25, orig_pos + QPoint(10, 0))
        anim.setKeyValueAt(0.5, orig_pos + QPoint(-10, 0))
        anim.setKeyValueAt(0.75, orig_pos + QPoint(10, 0))
        anim.setKeyValueAt(1, orig_pos)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start()
