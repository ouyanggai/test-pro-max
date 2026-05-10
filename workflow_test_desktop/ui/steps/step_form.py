"""步骤3：表单填写"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QComboBox,
    QFormLayout, QFrame, QScrollArea, QPushButton,
)
from PySide6.QtCore import Signal, Qt
from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG, SPACE_MD, RADIUS_CARD


class StepForm(QWidget):
    """表单填写步骤"""
    form_submitted = Signal(dict)

    def __init__(self, config, secrets, db, loop, shared_data):
        super().__init__()
        self._config = config
        self._secrets = secrets
        self._db = db
        self._loop = loop
        self._shared_data = shared_data
        self._field_widgets: dict = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG)

        title = QLabel("填写表单")
        title.setFont(FONT_FAMILY)
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        for label_text, action in [
            ("从历史采样", self._on_sample),
            ("清空", self._on_clear),
            ("保存为模板", self._on_save_template),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._form_container = QWidget()
        self._form_layout = QFormLayout(self._form_container)
        self._form_layout.setSpacing(SPACE_MD)
        scroll.setWidget(self._form_container)
        layout.addWidget(scroll, 1)

        self._empty_hint = QLabel("流程选择后自动加载表单字段")
        self._empty_hint.setFont(FONT_FAMILY)
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setStyleSheet("color: var(--text-secondary); padding: 40px;")
        layout.addWidget(self._empty_hint)

    def set_form_fields(self, fields: list):
        """从 StepFlow 选择流程后调用，填充表单字段"""
        # 清除现有内容
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._field_widgets.clear()
        self._empty_hint.setVisible(False)

        for field in fields:
            label = QLabel(field.get("field_name", field.get("label", "")))
            label.setFont(FONT_FAMILY)
            required = field.get("required", False)
            if required:
                label.setText(label.text() + " *")

            widget = self._make_widget_for_field(field)
            self._field_widgets[field.get("field_id", "")] = widget
            self._form_layout.addRow(label, widget)

    def _make_widget_for_field(self, field: dict) -> QWidget:
        field_type = field.get("type", "text")
        if field_type == "textarea" or field_type == "text":
            w = QTextEdit()
            w.setFont(FONT_FAMILY)
            if field.get("default"):
                w.setPlainText(str(field["default"]))
        elif field_type == "number":
            w = QSpinBox()
            w.setFont(FONT_FAMILY)
            if field.get("default"):
                w.setValue(int(field["default"]))
        elif field_type == "select" and field.get("options"):
            w = QComboBox()
            w.setFont(FONT_FAMILY)
            for opt in field["options"]:
                w.addItem(opt, opt)
        else:
            w = QLineEdit()
            w.setFont(FONT_FAMILY)
            if field.get("default"):
                w.setText(str(field["default"]))

        if field.get("readonly", False):
            w.setEnabled(False)

        return w

    def get_form_data(self) -> dict:
        """返回表单数据"""
        data = {}
        for fid, w in self._field_widgets.items():
            if isinstance(w, QTextEdit):
                data[fid] = w.toPlainText()
            elif isinstance(w, QSpinBox):
                data[fid] = w.value()
            elif isinstance(w, QComboBox):
                data[fid] = w.currentData() or w.currentText()
            else:
                data[fid] = w.text()
        return data

    def _on_sample(self):
        pass  # TODO: 从历史运行中采样表单数据

    def _on_clear(self):
        for fid, w in self._field_widgets.items():
            if isinstance(w, QTextEdit):
                w.clear()
            elif isinstance(w, QSpinBox):
                w.setValue(0)
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
            else:
                w.clear()

    def _on_save_template(self):
        pass  # TODO: 保存为模板
