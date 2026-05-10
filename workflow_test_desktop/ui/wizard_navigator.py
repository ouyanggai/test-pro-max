"""竖向步骤导航条（美化版）"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_SM_PX, SPACE_MD_PX, SPACE_LG_PX, LIGHT


class WizardNavigator(QWidget):
    """竖向步骤导航条"""

    step_clicked = Signal(int)

    def __init__(self, steps: list[str], parent=None):
        super().__init__(parent)
        self._steps = steps
        self._current = 0
        self._done = []
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(200)
        self._circles = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_SM_PX, SPACE_LG_PX, SPACE_SM_PX, SPACE_LG_PX)
        layout.setSpacing(4)

        # 标题
        title = QLabel("接口回归测试")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1A1D26; padding: 4px 8px;")
        layout.addWidget(title)
        layout.addSpacing(SPACE_LG_PX)

        self._step_buttons = []
        for i, name in enumerate(self._steps):
            step_item = self._build_step_item(i, name)
            layout.addWidget(step_item)
            self._step_buttons.append(step_item)

        layout.addStretch()
        self._update_buttons()

    def _build_step_item(self, index: int, name: str) -> QWidget:
        """构建单个步骤项（含序号圆圈 + 名称 + 连接线）"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # 序号圆圈
        circle = QLabel(str(index + 1))
        circle.setFixedSize(28, 28)
        circle.setAlignment(Qt.AlignCenter)
        circle.setFont(FONT_FAMILY)
        circle.setObjectName("step_circle")
        self._circles.append(circle)

        # 步骤名称
        label = QLabel(name)
        label.setFont(FONT_FAMILY)
        label.setObjectName("step_label")
        layout.addWidget(label, 1)
        layout.addWidget(circle)

        # 点击区域
        container.setCursor(Qt.PointingHandCursor)
        container.mousePressEvent = lambda e, idx=index: self.step_clicked.emit(idx)
        container.setObjectName("step_item")

        return container

    def set_current_step(self, index: int):
        self._current = index
        self._update_buttons()

    def mark_done(self, index: int):
        if index not in self._done:
            self._done.append(index)
        self._update_buttons()

    def _update_buttons(self):
        for i, item in enumerate(self._step_buttons):
            circle = self._circles[i]
            label = item.findChild(QLabel, "step_label")

            if i < self._current:
                state = "done"
            elif i == self._current:
                state = "active"
            else:
                state = "future"

            # 圆圈样式
            if state == "active":
                circle.setStyleSheet(
                    "background-color: #0EA5E9; color: white; border-radius: 14px; "
                    "font-weight: 700; font-size: 13px;"
                )
            elif state == "done":
                circle.setStyleSheet(
                    "background-color: #DBEAFE; color: #0EA5E9; border-radius: 14px; "
                    "font-weight: 700; font-size: 13px;"
                )
                circle.setText("✓")
            else:
                circle.setStyleSheet(
                    "background-color: transparent; color: #9CA3AF; border-radius: 14px; "
                    "border: 1.5px solid #D1D5DB; font-size: 13px;"
                )

            # 标签样式
            if state == "active":
                label.setStyleSheet("font-weight: 700; color: #1A1D26; font-size: 14px;")
            elif state == "done":
                label.setStyleSheet("color: #0EA5E9; font-size: 14px;")
            else:
                label.setStyleSheet("color: #9CA3AF; font-size: 14px;")

            item.setEnabled(i <= self._current)
