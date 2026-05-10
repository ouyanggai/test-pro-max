"""步骤1：账号选择"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QFrame, QComboBox,
)
from PySide6.QtCore import Signal
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


class StepAccount(QWidget):
    """账号选择步骤"""
    account_selected = Signal(str, str)  # username, display_name

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        title = QLabel("选择发起账号")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)

        # 会话状态卡片
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ border-radius: {RADIUS_CARD}; "
            "background: var(--bg-card); padding: 16px; }}"
        )
        cl = QHBoxLayout(card)
        indicator = QLabel("●")
        indicator.setStyleSheet("color: #10B981; font-size: 20px;")
        cl.addWidget(indicator)
        self._username_label = QLabel("当前会话：欧阳改（默认）")
        self._username_label.setFont(FONT_FAMILY)
        cl.addWidget(self._username_label)
        cl.addStretch()
        btn_switch = QPushButton("切换账号")
        btn_switch.setFont(FONT_FAMILY)
        btn_switch.clicked.connect(self._on_switch)
        cl.addWidget(btn_switch)
        layout.addWidget(card)

        # 切换账号面板
        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ border-radius: {RADIUS_CARD}; "
            "background: var(--bg-card); padding: 16px; }}"
        )
        pl = QVBoxLayout(panel)
        sl = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索账号...")
        self._search_input.setFont(FONT_FAMILY)
        self._search_input.textChanged.connect(self._on_search)
        sl.addWidget(self._search_input)
        self._dept_combo = QComboBox()
        self._dept_combo.setPlaceholderText("部门筛选")
        self._dept_combo.setFont(FONT_FAMILY)
        sl.addWidget(self._dept_combo)
        btn_reset = QPushButton("重置")
        btn_reset.setFont(FONT_FAMILY)
        btn_reset.clicked.connect(self._on_reset)
        sl.addWidget(btn_reset)
        pl.addLayout(sl)
        self._user_list = QListWidget()
        self._user_list.setFont(FONT_FAMILY)
        self._user_list.itemDoubleClicked.connect(self._on_user_double_clicked)
        pl.addWidget(self._user_list)
        layout.addWidget(panel, 1)

        # 加载默认账号
        self._load_default_account()

    def _load_default_account(self):
        default_username = self._secrets.get("DEFAULT_USERNAME", "欧阳改")
        self._shared_data["starter_username"] = default_username
        self._shared_data["starter_display_name"] = default_username
        self._username_label.setText(f"当前会话：{default_username}（默认）")

    def _on_switch(self):
        pass  # TODO: 实现账号搜索和切换

    def _on_search(self, text: str):
        pass  # TODO: 实现账号过滤

    def _on_reset(self):
        self._search_input.clear()
        self._dept_combo.setCurrentIndex(-1)

    def _on_user_double_clicked(self, item):
        username = item.text()
        self._shared_data["starter_username"] = username
        self._shared_data["starter_display_name"] = username
        self._username_label.setText(f"当前会话：{username}")
        self.account_selected.emit(username, username)
