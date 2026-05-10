"""测试 StepAccount（步骤1：账号搜索下拉）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.steps.step_account import StepAccount

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    yield qapp


@pytest.fixture
def mock_secrets():
    """模拟 secrets（默认账号为「欧阳改」）"""
    secrets = MagicMock()
    secrets.get = MagicMock(side_effect=lambda k, d=None: {"DEFAULT_USERNAME": "欧阳改"}.get(k, d))
    return secrets


@pytest.fixture
def mock_config():
    """模拟 config"""
    config = MagicMock()
    config.get = MagicMock(side_effect=lambda k, d=None: {
        "GATEWAY_URL": "https://dev.example.com",
    }.get(k, d))
    return config


@pytest.fixture
def shared_data():
    return {}


@pytest.fixture
def step_account(app, mock_config, mock_secrets, shared_data):
    """构建 StepAccount widget（不触发 API 调用）"""
    with patch("workflow_test_desktop.ui.steps.step_account.QTimer.singleShot"):
        widget = StepAccount(
            config=mock_config,
            secrets=mock_secrets,
            db=MagicMock(),
            loop=MagicMock(),
            shared_data=shared_data,
        )
    yield widget
    widget.deleteLater()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestStepAccountInit:
    """测试初始化行为"""

    def test_widget_created(self, step_account):
        """Widget 应正常创建"""
        assert step_account is not None

    def test_default_username_prefilled(self, step_account):
        """默认账号「欧阳改」应预填到输入框"""
        assert step_account._combo.lineEdit().text() == "欧阳改"

    def test_default_username_in_shared_data(self, step_account, shared_data):
        """默认账号应写入 shared_data"""
        assert shared_data["starter_username"] == "欧阳改"
        assert shared_data["starter_display_name"] == "欧阳改"

    def test_status_shows_selected(self, step_account):
        """状态指示应为绿色（已选择）"""
        assert "10B981" in step_account._status_label.styleSheet()  # 绿色
        assert "已选择" in step_account._status_label.text()


class TestStepAccountValidation:
    """测试 validate() 方法"""

    def test_validate_passes_when_username_set(self, step_account):
        """已选择账号时验证通过"""
        ok, msg = step_account.validate()
        assert ok is True
        assert msg == ""

    def test_validate_fails_when_username_empty(self, step_account):
        """账号为空时验证失败"""
        step_account._shared_data["starter_username"] = ""
        ok, msg = step_account.validate()
        assert ok is False
        assert "请选择" in msg

    def test_validate_fails_when_username_whitespace_only(self, step_account):
        """账号仅为空白时验证失败"""
        step_account._shared_data["starter_username"] = "   "
        ok, msg = step_account.validate()
        assert ok is False


class TestStepAccountPopulate:
    """测试下拉列表填充逻辑"""

    def test_populate_with_users(self, step_account):
        """_populate_combo 应正确填充用户"""
        step_account._all_users = [
            {"userId": "u1", "username": "zhangsan", "displayName": "张三"},
            {"userId": "u2", "username": "lisi", "displayName": "李四"},
            {"userId": "u3", "username": "ouyang", "displayName": "欧阳改"},
        ]
        step_account._populate_combo("")

        # 下拉应有 3 项
        assert step_account._combo.count() == 3

    def test_populate_filters_keyword(self, step_account):
        """关键字「zhang」应只匹配到张三"""
        step_account._all_users = [
            {"userId": "u1", "username": "zhangsan", "displayName": "张三"},
            {"userId": "u2", "username": "lisi", "displayName": "李四"},
            {"userId": "u3", "username": "ouyang", "displayName": "欧阳改"},
        ]
        step_account._populate_combo("zhang")

        # 应只匹配到张三
        assert step_account._combo.count() == 1
        assert step_account._combo.itemText(0) == "张三"

    def test_populate_fuzzy_match_username(self, step_account):
        """模糊匹配：用户名含关键字"""
        step_account._all_users = [
            {"userId": "u1", "username": "testuser001", "displayName": "测试用户1"},
            {"userId": "u2", "username": "admin", "displayName": "管理员"},
        ]
        step_account._populate_combo("test")

        assert step_account._combo.count() == 1
        assert step_account._combo.itemText(0) == "测试用户1"

    def test_populate_fuzzy_match_displayName(self, step_account):
        """模糊匹配：displayName 含关键字"""
        step_account._all_users = [
            {"userId": "u1", "username": "user001", "displayName": "王五"},
            {"userId": "u2", "username": "user002", "displayName": "王小二"},
        ]
        step_account._populate_combo("王小")

        assert step_account._combo.count() == 1
        assert step_account._combo.itemText(0) == "王小二"

    def test_populate_max_20_items(self, step_account):
        """下拉最多显示 20 条"""
        step_account._all_users = [
            {"userId": f"u{i}", "username": f"user{i:03d}", "displayName": f"用户{i}"}
            for i in range(50)
        ]
        step_account._populate_combo("")

        assert step_account._combo.count() == 20

    def test_populate_case_insensitive(self, step_account):
        """关键字匹配不区分大小写"""
        step_account._all_users = [
            {"userId": "u1", "username": "ZhangSan", "displayName": "张三"},
            {"userId": "u2", "username": "lisi", "displayName": "李四"},
        ]
        step_account._populate_combo("ZHANGSAN")

        assert step_account._combo.count() == 1
        assert step_account._combo.itemText(0) == "张三"

    def test_populate_preserves_input_text(self, step_account):
        """填充后保留用户输入文字"""
        step_account._all_users = [
            {"userId": "u1", "username": "zhangsan", "displayName": "张三"},
        ]
        step_account._combo.lineEdit().setText("张")
        step_account._populate_combo("张")

        assert step_account._combo.lineEdit().text() == "张"


class TestStepAccountSelection:
    """测试用户选择逻辑"""

    def test_update_status_green(self, step_account):
        """_update_status(True) 应显示绿色"""
        step_account._update_status(True, "已选择：张三")
        assert "10B981" in step_account._status_label.styleSheet()
        assert step_account._status_label.text() == "已选择：张三"

    def test_update_status_yellow(self, step_account):
        """_update_status(False) 应显示黄色"""
        step_account._update_status(False, "输入中")
        assert "F59E0B" in step_account._status_label.styleSheet()
        assert step_account._status_label.text() == "输入中"


class TestStepAccountErrorBus:
    """测试 ErrorBus 集成"""

    def test_error_bus_subscribed(self, step_account):
        """StepAccount 实例可正常订阅 ErrorBus"""
        from workflow_test_desktop.ui.error_bus import ErrorBus
        received = []

        def handler(item):
            received.append(item)

        bus = ErrorBus()
        bus.clear_handlers()
        bus.on_error(handler)

        bus.emit("测试错误", "测试消息", source="TestSource")

        assert len(received) == 1
        assert received[0].title == "测试错误"
        assert received[0].source == "TestSource"
