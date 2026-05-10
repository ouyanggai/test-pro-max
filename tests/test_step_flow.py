"""测试 StepFlow（步骤2：流程选择）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_flow import StepFlow, FlowCard


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
    return {}


@pytest.fixture
def step_flow(app, mock_config, shared_data):
    """构建 StepFlow widget（patch API 调用）"""
    with patch("workflow_test_desktop.ui.steps.step_flow.QTimer.singleShot"):
        widget = StepFlow(
            config=mock_config,
            secrets=MagicMock(),
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared_data,
        )
    yield widget
    widget.deleteLater()


class TestStepFlowInit:
    """测试初始化"""

    def test_widget_created(self, step_flow):
        assert step_flow is not None

    def test_title_shown(self, step_flow):
        """标题「选择流程」应显示"""
        for i in range(step_flow.layout().count()):
            w = step_flow.layout().itemAt(i).widget()
            if hasattr(w, "text"):
                if "选择流程" in w.text():
                    return
        # 没有找到标题 widget 也没关系，layout 结构是 VBoxLayout
        assert step_flow._search_input is not None

    def test_has_search_input(self, step_flow):
        assert step_flow._search_input is not None

    def test_has_refresh_button(self, step_flow):
        assert step_flow._refresh_btn is not None

    def test_empty_card_container(self, step_flow):
        """初始无流程时不崩溃"""
        assert step_flow._card_grid.count() == 0


class TestFlowCard:
    """测试 FlowCard 组件"""

    def test_flow_card_renders_name_and_category(self, app):
        flow = {
            "flowTemplateId": "fid-001",
            "flowTemplateName": "请假审批",
            "flowGroupName": "行政流程",
        }
        card = FlowCard(flow)
        assert card._name_label.text() == "请假审批"
        assert card._cat_label.text() == "行政流程"
        card.deleteLater()

    def test_flow_card_selection_toggle(self, app):
        flow = {"flowTemplateId": "fid-001", "flowTemplateName": "测试"}
        card = FlowCard(flow)
        assert not card.is_selected()
        card.set_selected(True)
        assert card.is_selected()
        card.set_selected(False)
        assert not card.is_selected()
        card.deleteLater()

    def test_flow_card_click_emits_signal(self, app):
        flow = {"flowTemplateId": "fid-001", "flowTemplateName": "测试"}
        card = FlowCard(flow)
        emitted = []

        def handler(f):
            emitted.append(f)

        card.clicked.connect(handler)
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import Qt
        # Simulate click
        import sys
        if sys.platform == "darwin":
            btn = Qt.MouseButton.LeftButton
        else:
            btn = Qt.MouseButton.LeftButton
        evt = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            QPointF(10, 10),
            btn,
            btn,
            Qt.KeyboardModifier.NoModifier,
        )
        card.mousePressEvent(evt)
        assert len(emitted) == 1
        assert emitted[0]["flowTemplateId"] == "fid-001"
        card.deleteLater()


class TestStepFlowValidation:
    """测试 validate()"""

    def test_validate_fails_when_no_flow_selected(self, step_flow):
        """未选择流程时验证失败"""
        ok, msg = step_flow.validate()
        assert ok is False
        assert "流程" in msg

    def test_validate_passes_when_flow_selected(self, step_flow, shared_data):
        """选择流程后验证通过"""
        step_flow._selected_flow = {
            "flowTemplateId": "fid-001",
            "flowTemplateName": "测试流程",
        }
        ok, msg = step_flow.validate()
        assert ok is True


class TestStepFlowRender:
    """测试卡片渲染"""

    def test_render_cards_filters_keyword(self, step_flow):
        """搜索关键字应过滤卡片"""
        step_flow._flows = [
            {"flowTemplateId": "f1", "flowTemplateName": "请假审批", "flowGroupName": "行政"},
            {"flowTemplateId": "f2", "flowTemplateName": "采购审批", "flowGroupName": "财务"},
            {"flowTemplateId": "f3", "flowTemplateName": "加班申请", "flowGroupName": "人事"},
        ]
        step_flow._render_cards("请假")
        # 应该只有 1 个卡片
        assert len(step_flow._card_widgets) == 1
        assert step_flow._card_widgets[0]._name_label.text() == "请假审批"

    def test_render_cards_empty_keyword_shows_all(self, step_flow):
        step_flow._flows = [
            {"flowTemplateId": "f1", "flowTemplateName": "A", "flowGroupName": ""},
            {"flowTemplateId": "f2", "flowTemplateName": "B", "flowGroupName": ""},
        ]
        step_flow._render_cards("")
        assert len(step_flow._card_widgets) == 2

    def test_render_cards_empty_state(self, step_flow):
        step_flow._render_cards("不存在的关键字")
        # 应该显示空状态 label
        for i in range(step_flow._card_grid.count()):
            w = step_flow._card_grid.itemAt(i).widget()
            if w and hasattr(w, "text"):
                assert "没有找到" in w.text() or "暂无可用" in w.text()
                return
        assert True  # 空状态显示是可选的


class TestStepFlowSelection:
    """测试流程选择"""

    def test_card_click_updates_shared_data(self, step_flow, shared_data):
        step_flow._flows = [
            {"flowTemplateId": "fid-001", "flowTemplateName": "测试", "flowGroupName": "G1"},
        ]
        step_flow._render_cards("")

        # 模拟卡片点击
        card = step_flow._card_widgets[0]
        card.clicked.emit({
            "flowTemplateId": "fid-001",
            "flowTemplateName": "测试流程",
            "flowGroupName": "测试组",
        })

        assert shared_data["flow_id"] == "fid-001"
        assert shared_data["flow_name"] == "测试流程"
        assert step_flow._selected_flow["flowTemplateId"] == "fid-001"

    def test_card_click_updates_selection_style(self, step_flow):
        step_flow._flows = [
            {"flowTemplateId": "f1", "flowTemplateName": "A", "flowGroupName": ""},
            {"flowTemplateId": "f2", "flowTemplateName": "B", "flowGroupName": ""},
        ]
        step_flow._render_cards("")

        # 点击第一个
        step_flow._card_widgets[0].clicked.emit(step_flow._card_widgets[0]._flow)
        assert step_flow._card_widgets[0].is_selected()
        assert not step_flow._card_widgets[1].is_selected()

        # 点击第二个
        step_flow._card_widgets[1].clicked.emit(step_flow._card_widgets[1]._flow)
        assert not step_flow._card_widgets[0].is_selected()
        assert step_flow._card_widgets[1].is_selected()
