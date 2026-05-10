"""测试 StepForm（步骤3：表单填写）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_form import StepForm


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    yield qapp


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get = MagicMock(side_effect=lambda k, d=None: {
        "GATEWAY_URL": "https://dev.example.com",
    }.get(k, d))
    return config


@pytest.fixture
def shared_data():
    return {"flow_id": "test-flow-001"}


@pytest.fixture
def step_form(app, mock_config, shared_data):
    """构建 StepForm widget（patch QTimer，避免异步触发）"""
    with patch("workflow_test_desktop.ui.steps.step_form.QTimer.singleShot"):
        widget = StepForm(
            config=mock_config,
            secrets=MagicMock(),
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared_data,
        )
    yield widget
    widget.deleteLater()


@pytest.fixture
def step_form_no_flow(app, mock_config):
    """构建 StepForm widget（无 flow_id）"""
    shared = {}
    with patch("workflow_test_desktop.ui.steps.step_form.QTimer.singleShot"):
        widget = StepForm(
            config=mock_config,
            secrets=MagicMock(),
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared,
        )
    yield widget
    widget.deleteLater()


class TestStepFormInit:
    """测试初始化"""

    def test_widget_created(self, step_form):
        assert step_form is not None

    def test_has_form_layout(self, step_form):
        assert step_form._form_layout is not None

    def test_toolbar_buttons_exist(self, step_form):
        """三个工具栏按钮存在"""
        # 从工具栏获取按钮
        toolbar_layout = step_form.layout().itemAt(1).layout()
        btn_count = sum(1 for i in range(toolbar_layout.count()) if hasattr(toolbar_layout.itemAt(i).widget(), "clicked"))
        assert btn_count >= 3


class TestStepFormBuild:
    """测试表单构建"""

    def test_build_form_creates_widgets(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "姓名", "fieldType": "text"},
            {"fieldId": "f2", "fieldLabel": "备注", "fieldType": "textarea"},
            {"fieldId": "f3", "fieldLabel": "数量", "fieldType": "number"},
            {"fieldId": "f4", "fieldLabel": "类型", "fieldType": "select", "options": ["A", "B"]},
        ]
        step_form._build_form(fields)
        assert len(step_form._field_widgets) == 4
        assert "f1" in step_form._field_widgets
        assert "f2" in step_form._field_widgets
        assert "f3" in step_form._field_widgets
        assert "f4" in step_form._field_widgets

    def test_build_form_required_labels(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "必填项", "fieldType": "text", "required": True},
            {"fieldId": "f2", "fieldLabel": "选填项", "fieldType": "text", "required": False},
        ]
        step_form._build_form(fields)
        assert " *" in step_form._field_labels["f1"].text()
        assert " *" not in step_form._field_labels["f2"].text()

    def test_build_form_empty_fields_clears_widgets(self, step_form):
        """_build_form([]) 应清空字段控件"""
        # 先构建有字段的表单
        step_form._build_form([{"fieldId": "f1", "fieldLabel": "Field", "fieldType": "text"}])
        assert "f1" in step_form._field_widgets
        # 清空字段后应清除控件
        step_form._build_form([])
        assert len(step_form._field_widgets) == 0

    def test_build_form_with_no_flow_id_calls_load(self, step_form_no_flow):
        """无 flow_id 时 _load_form_from_flow 不加载表单"""
        # 验证：无 flow_id 时，_field_widgets 应为空（未加载）
        assert len(step_form_no_flow._field_widgets) == 0

    def test_build_form_clears_previous(self, step_form):
        fields1 = [{"fieldId": "f1", "fieldLabel": "Field 1", "fieldType": "text"}]
        fields2 = [{"fieldId": "f2", "fieldLabel": "Field 2", "fieldType": "text"}]
        step_form._build_form(fields1)
        assert "f1" in step_form._field_widgets
        step_form._build_form(fields2)
        assert "f1" not in step_form._field_widgets
        assert "f2" in step_form._field_widgets


class TestStepFormWidgets:
    """测试各类型控件"""

    def test_text_widget_is_qlineedit(self, step_form):
        step_form._build_form([{"fieldId": "text1", "fieldLabel": "Text", "fieldType": "text"}])
        from PySide6.QtWidgets import QLineEdit
        assert isinstance(step_form._field_widgets["text1"], QLineEdit)

    def test_textarea_widget_is_qtextedit(self, step_form):
        step_form._build_form([{"fieldId": "area1", "fieldLabel": "Area", "fieldType": "textarea"}])
        from PySide6.QtWidgets import QTextEdit
        assert isinstance(step_form._field_widgets["area1"], QTextEdit)

    def test_number_widget_is_qspinbox(self, step_form):
        step_form._build_form([{"fieldId": "num1", "fieldLabel": "Num", "fieldType": "number"}])
        from PySide6.QtWidgets import QSpinBox
        assert isinstance(step_form._field_widgets["num1"], QSpinBox)

    def test_select_widget_is_qcombobox(self, step_form):
        step_form._build_form([{"fieldId": "sel1", "fieldLabel": "Sel", "fieldType": "select", "options": ["A", "B"]}])
        from PySide6.QtWidgets import QComboBox
        assert isinstance(step_form._field_widgets["sel1"], QComboBox)

    def test_number_spinbox_respects_min_max(self, step_form):
        step_form._build_form([{"fieldId": "num1", "fieldLabel": "Num", "fieldType": "number", "min": 10, "max": 100}])
        spin = step_form._field_widgets["num1"]
        assert spin.minimum() == 10
        assert spin.maximum() == 100

    def test_set_widget_value_text(self, step_form):
        from PySide6.QtWidgets import QLineEdit
        step_form._build_form([{"fieldId": "f1", "fieldLabel": "F1", "fieldType": "text"}])
        step_form._set_widget_value(step_form._field_widgets["f1"], "hello")
        assert step_form._field_widgets["f1"].text() == "hello"


class TestStepFormValidation:
    """测试 validate()"""

    def test_validate_passes_when_all_required_filled(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "姓名", "fieldType": "text", "required": True},
        ]
        step_form._build_form(fields)
        step_form._field_widgets["f1"].setText("张三")
        ok, msg = step_form.validate()
        assert ok is True

    def test_validate_fails_when_required_empty(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "姓名", "fieldType": "text", "required": True},
        ]
        step_form._build_form(fields)
        step_form._field_widgets["f1"].setText("")
        ok, msg = step_form.validate()
        assert ok is False
        assert "姓名" in msg

    def test_validate_fails_when_required_whitespace_only(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "姓名", "fieldType": "text", "required": True},
        ]
        step_form._build_form(fields)
        step_form._field_widgets["f1"].setText("   ")
        ok, msg = step_form.validate()
        assert ok is False

    def test_validate_passes_when_no_required_fields(self, step_form):
        fields = [
            {"fieldId": "f1", "fieldLabel": "选填", "fieldType": "text", "required": False},
        ]
        step_form._build_form(fields)
        ok, msg = step_form.validate()
        assert ok is True

    def test_validate_passes_when_no_fields(self, step_form):
        step_form._build_form([])
        ok, msg = step_form.validate()
        assert ok is True


class TestStepFormData:
    """测试 get_form_data()"""

    def test_get_form_data_lineedit(self, step_form):
        step_form._build_form([{"fieldId": "f1", "fieldLabel": "Name", "fieldType": "text"}])
        step_form._field_widgets["f1"].setText("张三")
        data = step_form.get_form_data()
        assert data["f1"] == "张三"

    def test_get_form_data_textedit(self, step_form):
        step_form._build_form([{"fieldId": "f1", "fieldLabel": "Desc", "fieldType": "textarea"}])
        step_form._field_widgets["f1"].setPlainText("测试内容")
        data = step_form.get_form_data()
        assert data["f1"] == "测试内容"

    def test_get_form_data_spinbox(self, step_form):
        step_form._build_form([{"fieldId": "f1", "fieldLabel": "Count", "fieldType": "number"}])
        step_form._field_widgets["f1"].setValue(42)
        data = step_form.get_form_data()
        assert data["f1"] == 42


class TestStepFormClear:
    """测试清空"""

    def test_clear_resets_all_fields(self, step_form):
        step_form._build_form([
            {"fieldId": "f1", "fieldLabel": "Name", "fieldType": "text"},
            {"fieldId": "f2", "fieldLabel": "Count", "fieldType": "number"},
        ])
        step_form._field_widgets["f1"].setText("张三")
        step_form._field_widgets["f2"].setValue(10)
        step_form._on_clear()
        assert step_form._field_widgets["f1"].text() == ""
        assert step_form._field_widgets["f2"].value() == 0
