"""步骤1：账号选择 - 搜索下拉 + 默认预填"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QCompleter,
)
from PySide6.QtCore import Qt, Signal, QTimer

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX
from workflow_test_desktop.api.client import ApiClient
from workflow_test_desktop.ui.error_bus import ErrorBus

logger = logging.getLogger(__name__)


class StepAccount(QWidget):
    """
    账号选择步骤：
    - 输入框带下拉候选列表，实时模糊匹配
    - 默认预填 DEFAULT_USERNAME
    - 用户修改后更新 shared_data
    """

    # signal: (username, display_name)
    account_selected = Signal(str, str)

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._all_users: list[dict] = []
        self._updating_combo = False  # 防止 _on_selection_changed 循环触发
        self._setup_ui()
        self._load_default_account()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("发起账号")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 搜索框卡片
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "QFrame#card { background-color: #FFFFFF; border: 1px solid #E2E4E9; "
            "border-radius: 12px; padding: 24px; }"
        )
        cl = QVBoxLayout(card)
        cl.setSpacing(12)

        hint = QLabel("搜索或直接选择账号（所有账号密码均为 1）")
        hint.setFont(FONT_FAMILY)
        hint.setStyleSheet("color: #6B7280; font-size: 13px;")
        cl.addWidget(hint)

        # 可编辑下拉搜索框
        self._combo = QComboBox()
        self._combo.setFont(FONT_FAMILY)
        self._combo.setEditable(True)
        self._combo.setMinimumContentsLength(0)
        self._combo.setInsertPolicy(QComboBox.NoInsert)
        self._combo.lineEdit().setFont(FONT_FAMILY)
        self._combo.lineEdit().setPlaceholderText("输入账号名称搜索...")
        self._combo.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._combo.currentTextChanged.connect(self._on_selection_changed)
        cl.addWidget(self._combo)

        # 状态指示
        status_layout = QHBoxLayout()
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color: #9CA3AF; font-size: 14px;")
        self._status_label = QLabel("未选择账号")
        self._status_label.setFont(FONT_FAMILY)
        self._status_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        status_layout.addWidget(self._status_dot)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        cl.addLayout(status_layout)

        layout.addWidget(card, 1)

    # ─── 默认账号 ───────────────────────────────────────────────

    def _load_default_account(self):
        default_username = self._secrets.get("DEFAULT_USERNAME", "欧阳改")
        self._shared_data["starter_username"] = default_username
        self._shared_data["starter_display_name"] = default_username
        self._combo.lineEdit().setText(default_username)
        self._update_status(True, f"已选择：{default_username}")
        self._load_users_from_api()

    # ─── 加载账号列表 ───────────────────────────────────────────

    def _load_users_from_api(self):
        """从 API 加载用户列表用于模糊匹配"""
        async def _fetch():
            gateway = self._config.get("GATEWAY_URL", "")
            if not gateway:
                logger.warning("[StepAccount] GATEWAY_URL 未配置，跳过加载用户列表")
                return
            try:
                async with ApiClient(gateway) as client:
                    resp = await client.post(
                        "/web/user/api/user/list",
                        json={"page": 1, "size": 200, "keyword": ""},
                    )
                    data = resp.json()
                    if data.get("code") == 0:
                        records = data.get("data", {}).get("records", [])
                        self._all_users = records
                        logger.info(f"[StepAccount] 加载到 {len(records)} 个用户")
                        self._populate_combo("")
                    else:
                        ErrorBus().emit(
                            "加载账号失败",
                            data.get("message", "未知错误"),
                            source="StepAccount",
                        )
            except Exception as e:
                logger.exception("[StepAccount] 加载用户列表异常")
                ErrorBus().emit(
                    "加载账号失败",
                    str(e),
                    source="StepAccount",
                )

        def _run():
            try:
                loop = asyncio.get_event_loop()
            except (RuntimeError, DeprecationWarning):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            asyncio.ensure_future(_fetch(), loop=loop)

        QTimer.singleShot(100, _run)

    def _populate_combo(self, keyword: str):
        """根据关键字过滤并填充下拉列表"""
        self._updating_combo = True
        try:
            kw = keyword.lower().strip()
            filtered = self._all_users
            if kw:
                filtered = [
                    u for u in self._all_users
                    if kw in (u.get("username") or "").lower()
                    or kw in (u.get("displayName") or "").lower()
                    or kw in (u.get("userName") or "").lower()
                ]
            filtered = filtered[:20]  # 最多显示20条

            self._combo.blockSignals(True)
            self._combo.clear()
            for u in filtered:
                name = u.get("displayName") or u.get("username") or u.get("userName", "")
                user_id = u.get("userId", "")
                self._combo.addItem(name, userData={"username": name, "userId": user_id})
            self._combo.blockSignals(False)

            # 恢复用户输入
            if keyword:
                self._combo.lineEdit().setText(keyword)
                self._combo.lineEdit().selectAll()
        finally:
            self._updating_combo = False

    # ─── 选择变化 ───────────────────────────────────────────────

    def _on_selection_changed(self, text: str):
        """用户输入或选择变化时过滤列表"""
        if self._updating_combo:
            return
        self._populate_combo(text)
        self._combo.showPopup()

        # 检查是否精确匹配到用户
        matched = next(
            (
                u
                for u in self._all_users
                if (u.get("displayName") or u.get("username") or u.get("userName", "")) == text
            ),
            None,
        )
        if matched:
            self._shared_data["starter_username"] = text
            self._shared_data["starter_display_name"] = text
            self._update_status(True, f"已选择：{text}")
            self.account_selected.emit(text, text)
        else:
            self._update_status(False, "输入中（按 Enter 选择）")

    def _update_status(self, ok: bool, text: str):
        self._status_label.setText(text)
        if ok:
            self._status_dot.setStyleSheet("color: #10B981; font-size: 14px;")
            self._status_label.setStyleSheet("color: #10B981; font-size: 13px;")
        else:
            self._status_dot.setStyleSheet("color: #F59E0B; font-size: 14px;")
            self._status_label.setStyleSheet("color: #F59E0B; font-size: 13px;")

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """验证：必须有选中的账号"""
        username = self._shared_data.get("starter_username", "").strip()
        if not username:
            return False, "请选择或输入发起账号"
        return True, ""
