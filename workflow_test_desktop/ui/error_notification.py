"""错误通知条组件"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QFrame,
)
from PySide6.QtCore import Qt

from workflow_test_desktop.ui.error_bus import ErrorBus, ErrorItem
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_XL_PX


class ErrorNotificationBar(QWidget):
    """
    错误通知条，显示在内容区顶部。
    支持多条错误叠加、自动展开、手动关闭、详情展开。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._errors: list[ErrorItem] = []
        self._expanded_indices: set[int] = set()
        self._setup_ui()
        ErrorBus().on_error(self._on_new_error)

    # ─── UI 初始化 ─────────────────────────────────────────────

    def _setup_ui(self):
        self.setFixedHeight(0)   # 初始隐藏
        self.setMaximumHeight(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._container = QWidget()
        container_style = (
            "QWidget { background-color: #FEE2E2; border-bottom: 1px solid #FECACA; }"
        )
        self._container.setStyleSheet(container_style)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(SPACE_XL_PX, 8, SPACE_XL_PX, 8)
        self._container_layout.setSpacing(4)
        layout.addWidget(self._container)

    # ─── 错误处理 ───────────────────────────────────────────────

    def _on_new_error(self, item: ErrorItem):
        self._errors.append(item)
        self._render_errors()

    def _render_errors(self):
        """渲染所有错误条"""
        # 清除现有子控件
        while self._container_layout.count():
            child = self._container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 重新构建
        for i, err in enumerate(self._errors):
            bar = self._build_error_bar(err, i)
            self._container_layout.addWidget(bar)

        # 更新高度：最多显示 3 条，每条 60px
        visible_count = min(len(self._errors), 3)
        total_height = visible_count * 60 if visible_count > 0 else 0
        self.setFixedHeight(total_height)
        self.update()

    def _build_error_bar(self, err: ErrorItem, index: int) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(
            "QFrame { background-color: #FEF2F2; border-radius: 8px; padding: 0; }"
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.setSpacing(8)

        # 图标
        icon = QLabel("⚠")   # ⚠
        icon.setStyleSheet("font-size: 18px; background: transparent; border: none; color: #991B1B;")
        icon.setFixedWidth(24)
        icon.setAlignment(Qt.AlignCenter)
        bar_layout.addWidget(icon)

        # 内容
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        # 时间戳 + 来源
        meta = QLabel(f"{err.timestamp}  {err.source}")
        meta.setFont(FONT_FAMILY)
        meta.setStyleSheet("color: #B91C1C; font-size: 11px; background: transparent; border: none;")
        content_layout.addWidget(meta)

        title_label = QLabel(err.title)
        title_label.setFont(FONT_FAMILY)
        title_label.setStyleSheet(
            "font-weight: 600; color: #991B1B; font-size: 14px; background: transparent; border: none;"
        )
        content_layout.addWidget(title_label)

        msg_label = QLabel(err.message)
        msg_label.setFont(FONT_FAMILY)
        msg_label.setStyleSheet("color: #B91C1C; font-size: 13px; background: transparent; border: none;")
        msg_label.setWordWrap(True)
        content_layout.addWidget(msg_label)

        # 详情
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 4, 0, 0)
        detail_layout.setSpacing(2)

        detail_label = QLabel(err.detail)
        detail_label.setFont(FONT_FAMILY)
        detail_label.setStyleSheet(
            "color: #7F1D1D; font-size: 12px; font-family: monospace; background: #FECACA; "
            "border-radius: 4px; padding: 6px 8px;"
        )
        detail_label.setWordWrap(True)
        detail_label.setVisible(index in self._expanded_indices)
        detail_label.setObjectName("detail")
        detail_layout.addWidget(detail_label)

        content_layout.addWidget(detail_widget)

        bar_layout.addWidget(content, 1)

        # 按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        if err.detail:
            btn_detail = QPushButton("▼")
            btn_detail.setFont(FONT_FAMILY)
            btn_detail.setFixedSize(28, 22)
            btn_detail.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid #FECACA; "
                "border-radius: 4px; color: #991B1B; padding: 0; font-size: 12px; }"
                "QPushButton:hover { background: #FECACA; }"
            )
            # pyright: ignore [reportGeneralTypeIssues]
            btn_detail.clicked.connect(lambda _, idx=index: self._toggle_detail(idx))
            btn_layout.addWidget(btn_detail)

        btn_close = QPushButton("✕")   # ✕
        btn_close.setFont(FONT_FAMILY)
        btn_close.setFixedSize(28, 22)
        btn_close.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #FECACA; "
            "border-radius: 4px; color: #991B1B; padding: 0; font-size: 12px; }"
            "QPushButton:hover { background: #FECACA; }"
        )
        # pyright: ignore [reportGeneralTypeIssues]
        btn_close.clicked.connect(lambda _, idx=index: self._dismiss_error(idx))
        btn_layout.addWidget(btn_close)

        bar_layout.addLayout(btn_layout)
        return bar

    def _toggle_detail(self, index: int):
        if index in self._expanded_indices:
            self._expanded_indices.discard(index)
        else:
            self._expanded_indices.add(index)

        # 找到对应 detail label 并切换可见性
        container = self._container_layout.itemAt(index)
        if container and container.widget():
            detail_lbl = container.widget().findChild(QLabel, "detail")
            if detail_lbl:
                detail_lbl.setVisible(index in self._expanded_indices)

    def _dismiss_error(self, index: int):
        """关闭指定索引的错误"""
        if 0 <= index < len(self._errors):
            self._errors.pop(index)
            self._expanded_indices.discard(index)
            # 重新索引
            new_expanded = set()
            for old_idx in self._expanded_indices:
                if old_idx > index:
                    new_expanded.add(old_idx - 1)
                elif old_idx < index:
                    new_expanded.add(old_idx)
            self._expanded_indices = new_expanded
            self._render_errors()
            if not self._errors:
                self.setFixedHeight(0)

    def clear_all(self):
        """清空所有错误"""
        self._errors.clear()
        self._expanded_indices.clear()
        self._render_errors()
        self.setFixedHeight(0)

    def error_count(self) -> int:
        return len(self._errors)
