"""竖向步骤导航条"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_SM, SPACE_MD, SPACE_LG


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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_MD, SPACE_LG, SPACE_MD, SPACE_LG)
        layout.setSpacing(SPACE_SM)

        title = QLabel("接口回归测试")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)
        layout.addSpacing(SPACE_LG)

        self._step_buttons = []
        for i, name in enumerate(self._steps):
            btn = QPushButton(f"  {name}")
            btn.setFont(FONT_FAMILY)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self.step_clicked.emit(idx))
            layout.addWidget(btn)
            self._step_buttons.append(btn)

        layout.addStretch()
        self._update_buttons()

    def set_current_step(self, index: int):
        self._current = index
        self._update_buttons()

    def mark_done(self, index: int):
        if index not in self._done:
            self._done.append(index)
        self._update_buttons()

    def _update_buttons(self):
        for i, btn in enumerate(self._step_buttons):
            if i < self._current:
                state = "done"
            elif i == self._current:
                state = "active"
            else:
                state = "future"
            btn.setProperty("step_state", state)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
