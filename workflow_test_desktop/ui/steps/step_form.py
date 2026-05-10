"""步骤3：表单填写 - 动态字段渲染 + 必填验证"""
from __future__ import annotations

import asyncio
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QComboBox,
    QFormLayout, QFrame, QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

from workflow_test_desktop.config.themes import FONT_FAMILY, SPACE_LG_PX
from workflow_test_desktop.api.client import ApiClient
from workflow_test_desktop.ui.error_bus import ErrorBus

logger = logging.getLogger(__name__)


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
        self._field_widgets: dict[str, QWidget] = {}
        self._field_labels: dict[str, QLabel] = {}
        self._setup_ui()
        self._load_form_from_flow()

    # ─── UI 构建 ───────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE_LG_PX)

        # 标题
        title = QLabel("填写表单")
        title.setFont(FONT_FAMILY)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1A1D26;")
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        for label_text, action in [
            ("从历史采样", self._on_sample),
            ("清空", self._on_clear),
            ("保存模板", self._on_save_template),
        ]:
            btn = QPushButton(label_text)
            btn.setFont(FONT_FAMILY)
            btn.setProperty("theme", "secondary")
            btn.clicked.connect(action)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 表单区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._form_container = QWidget()
        self._form_container.setObjectName("card")
        self._form_container.setStyleSheet(
            "QWidget#card { background-color: #FFFFFF; border: 1px solid #E2E4E9; "
            "border-radius: 12px; padding: 24px; }"
        )
        self._form_layout = QFormLayout(self._form_container)
        self._form_layout.setSpacing(SPACE_LG_PX)
        self._form_layout.setLabelAlignment(Qt.AlignLeft)
        self._form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(self._form_container)
        layout.addWidget(scroll, 1)

        # 空状态提示
        self._empty_hint = QLabel("选择流程后自动加载表单字段")
        self._empty_hint.setFont(FONT_FAMILY)
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setStyleSheet("color: #9CA3AF; padding: 60px; font-size: 14px;")
        layout.addWidget(self._empty_hint)

        # 验证错误提示
        self._error_label = QLabel("")
        self._error_label.setFont(FONT_FAMILY)
        self._error_label.setStyleSheet("color: #EF4444; font-size: 13px; padding: 8px 12px;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

    # ─── 加载表单 ───────────────────────────────────────────────

    def _load_form_from_flow(self):
        """从 shared_data 读取 flow_id，加载表单配置"""
        flow_id = self._shared_data.get("flow_id")
        if not flow_id:
            self._empty_hint.setVisible(True)
            return
        self._empty_hint.setVisible(False)

        async def _fetch():
            gateway = self._config.gateway_url
            if not gateway:
                ErrorBus().emit(
                    "配置错误",
                    "GATEWAY_URL 未配置",
                    source="StepForm",
                )
                return
            try:
                async with ApiClient(gateway) as client:
                    resp = await client.post(
                        "/web/flowTemplateApi/detail",
                        json={"id": flow_id},
                    )
                    data = resp.json()
                    if data.get("code") == 0:
                        form_config = data.get("data", {}).get("formConfig", [])
                        if not form_config:
                            form_config = data.get("data", {}).get("formConfigList", [])
                        # 同时缓存节点信息供 StepNodes 使用
                        self._shared_data["_flow_detail"] = data.get("data", {})
                        self._build_form(form_config)
                    else:
                        ErrorBus().emit(
                            "加载表单失败",
                            data.get("message", "未知错误"),
                            source="StepForm",
                        )
            except Exception as e:
                ErrorBus().emit(
                    "加载表单失败",
                    str(e),
                    source="StepForm",
                )

        def _run():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            asyncio.ensure_future(_fetch(), loop=loop)

        QTimer.singleShot(50, _run)

    def _build_form(self, fields: list):
        """根据字段配置构建表单"""
        # 清除现有
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._field_widgets.clear()
        self._field_labels.clear()

        if not fields:
            self._empty_hint.setVisible(True)
            return
        self._empty_hint.setVisible(False)

        for field in fields:
            field_id = field.get("fieldId", "") or field.get("field_name", "")
            if not field_id:
                continue
            label_text = field.get("fieldLabel", "") or field.get("label", "") or field_id
            required = field.get("required", False) or field.get("requiredField", False)

            widget = self._make_widget_for_field(field)
            self._field_widgets[field_id] = widget

            # 标签
            label = QLabel(label_text + (" *" if required else ""))
            label.setFont(FONT_FAMILY)
            label.setStyleSheet("font-weight: 500; color: #374151; font-size: 14px;")
            label.setObjectName(f"label_{field_id}")
            self._field_labels[field_id] = label

            # 设置默认
            default = field.get("defaultValue") or field.get("default")
            if default is not None and default != "":
                self._set_widget_value(widget, default)

            self._form_layout.addRow(label, widget)

    def _make_widget_for_field(self, field: dict) -> QWidget:
        field_type = field.get("fieldType", "") or field.get("type", "")
        options = field.get("options", []) or field.get("optionList", [])

        if field_type in ("textarea", "multiline"):
            w = QTextEdit()
            w.setFont(FONT_FAMILY)
            w.setMinimumHeight(80)
            w.setMaximumHeight(200)
        elif field_type in ("number", "int", "decimal"):
            w = QSpinBox()
            w.setFont(FONT_FAMILY)
            if field.get("min") is not None:
                w.setMinimum(int(field["min"]))
            if field.get("max") is not None:
                w.setMaximum(int(field["max"]))
            if field.get("defaultValue") is not None:
                w.setValue(int(field["defaultValue"]))
        elif field_type == "select" and options:
            w = QComboBox()
            w.setFont(FONT_FAMILY)
            for opt in options:
                if isinstance(opt, dict):
                    w.addItem(opt.get("label", ""), opt.get("value", ""))
                else:
                    w.addItem(str(opt), opt)
        else:
            w = QLineEdit()
            w.setFont(FONT_FAMILY)
            if field.get("placeholder"):
                w.setPlaceholderText(field["placeholder"])

        if field.get("readonly") or field.get("disabled"):
            w.setEnabled(False)

        return w

    def _set_widget_value(self, widget: QWidget, value):
        if isinstance(widget, QTextEdit):
            widget.setPlainText(str(value))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QComboBox):
            idx = widget.findData(value)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            else:
                idx_text = widget.findText(str(value))
                if idx_text >= 0:
                    widget.setCurrentIndex(idx_text)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))

    # ─── 获取数据 ───────────────────────────────────────────────

    def get_form_data(self) -> dict:
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

    # ─── 验证 ───────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """验证必填字段"""
        self._error_label.setVisible(False)
        for fid, w in self._field_widgets.items():
            if isinstance(w, QTextEdit):
                value = w.toPlainText().strip()
            elif isinstance(w, QSpinBox):
                value = str(w.value())
            else:
                value = w.text().strip()

            # 检查是否必填（通过标签是否含 *）
            label = self._field_labels.get(fid)
            if label and " *" in label.text() and not value:
                field_name = label.text().replace(" *", "")
                # 高亮 + 抖动
                self._highlight_error(w, label)
                self._error_label.setText(f"⚠ 请填写「{field_name}」")
                self._error_label.setVisible(True)
                self._scroll_to_widget(w)
                return False, f"请填写「{field_name}」"
        return True, ""

    def _highlight_error(self, widget: QWidget, label: QLabel):
        """错误高亮 + 抖动"""
        label.setStyleSheet("font-weight: 500; color: #EF4444; font-size: 14px;")
        self._shake_widget(widget)

    def _shake_widget(self, widget: QWidget):
        """抖动动画"""
        anim = QPropertyAnimation(widget, b"pos")
        orig_pos = widget.pos()
        anim.setDuration(300)
        anim.setKeyValueAt(0, orig_pos)
        anim.setKeyValueAt(0.25, orig_pos + QPoint(8, 0))
        anim.setKeyValueAt(0.5, orig_pos + QPoint(-8, 0))
        anim.setKeyValueAt(0.75, orig_pos + QPoint(8, 0))
        anim.setKeyValueAt(1, orig_pos)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start()

    def _scroll_to_widget(self, widget: QWidget):
        """滚动到控件位置"""
        scroll = self.parent()
        while scroll and not isinstance(scroll, QScrollArea):
            scroll = scroll.parent()
        if scroll:
            scroll.ensureWidgetVisible(widget)

    # ─── 操作 ───────────────────────────────────────────────

    def _on_sample(self):
        logger.info("从历史采样（TODO）")

    def _on_clear(self):
        for fid, w in self._field_widgets.items():
            if isinstance(w, QTextEdit):
                w.clear()
            elif isinstance(w, QSpinBox):
                w.setValue(0)
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
            elif isinstance(w, QLineEdit):
                w.clear()
        # 重置标签颜色
        for label in self._field_labels.values():
            label.setStyleSheet("font-weight: 500; color: #374151; font-size: 14px;")
        self._error_label.setVisible(False)

    def _on_save_template(self):
        logger.info("保存模板（TODO）")
