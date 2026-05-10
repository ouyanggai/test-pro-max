"""步骤2：流程选择"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QGridLayout, QFrame, QScrollArea,
)
from PySide6.QtCore import Signal
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


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
        self._flows = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        title = QLabel("选择流程")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索流程...")
        self._search_input.setFont(FONT_FAMILY)
        self._search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_input)
        self._category_combo = QComboBox()
        self._category_combo.setPlaceholderText("分类筛选")
        self._category_combo.setFont(FONT_FAMILY)
        toolbar.addWidget(self._category_combo)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.setFont(FONT_FAMILY)
        btn_refresh.clicked.connect(self._on_refresh)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._flow_container = QWidget()
        self._flow_grid = QGridLayout(self._flow_container)
        self._flow_grid.setSpacing(SPACE_MD)
        scroll.setWidget(self._flow_container)
        layout.addWidget(scroll, 1)

        self._hint = QLabel("")
        self._hint.setFont(FONT_FAMILY)
        layout.addWidget(self._hint)

    def _on_search(self, text: str):
        self._filter_flows(text)

    def _on_refresh(self):
        pass  # TODO: 调用 FlowCatalogService.list_startable_flows

    def _filter_flows(self, keyword: str):
        # 清除现有卡片
        while self._flow_grid.count():
            item = self._flow_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = self._flows
        if keyword:
            filtered = [f for f in self._flows if keyword.lower() in f.get("flow_name", "").lower()]

        for i, flow in enumerate(filtered):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ border-radius: {RADIUS_CARD}; "
                "background: var(--bg-card); padding: 12px; "
                "border: 1px solid var(--border); }}"
            )
            cl = QVBoxLayout(card)
            lbl_name = QLabel(flow.get("flow_name", ""))
            lbl_name.setFont(FONT_FAMILY)
            lbl_name.setStyleSheet("font-weight: bold;")
            cl.addWidget(lbl_name)
            lbl_cat = QLabel(flow.get("category_name", ""))
            lbl_cat.setFont(FONT_FAMILY)
            lbl_cat.setStyleSheet("color: var(--text-secondary); font-size: 12px;")
            cl.addWidget(lbl_cat)
            row, col = divmod(i, 2)
            self._flow_grid.addWidget(card, row, col)

    def set_flows(self, flows):
        self._flows = flows
        self._filter_flows("")
