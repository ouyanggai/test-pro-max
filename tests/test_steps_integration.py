"""测试步骤集成（steps 2-6 + main_window 验证回调）"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from workflow_test_desktop.ui.main_window import MainWindow
from workflow_test_desktop.ui.steps import StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport


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
def mock_secrets():
    secrets = MagicMock()
    secrets.get = MagicMock(side_effect=lambda k, d=None: {
        "DEFAULT_USERNAME": "欧阳改",
    }.get(k, d))
    return secrets


@pytest.fixture
def main_window(app, mock_config, mock_secrets):
    mw = MainWindow(config=mock_config, secrets=mock_secrets, db=MagicMock(), loop=MagicMock())
    yield mw
    mw.deleteLater()


class TestStepAccountIntegration:
    """集成测试：步骤1 验证"""

    def test_step_account_validate_passes(self, app, mock_config, mock_secrets):
        shared = {}
        with patch("workflow_test_desktop.ui.steps.step_account.QTimer.singleShot"):
            step = StepAccount(
                config=mock_config,
                secrets=mock_secrets,
                db=MagicMock(),
                loop=MagicMock(),
                shared_data=shared,
            )
        # 默认预填欧阳改，验证应通过
        ok, msg = step.validate()
        assert ok is True, f"StepAccount 默认应通过验证，但得到: {msg}"
        step.deleteLater()


class TestStepFlowIntegration:
    """集成测试：步骤2 验证"""

    def test_step_flow_validate_blocks_navigation(self, app, mock_config):
        shared = {}
        with patch("workflow_test_desktop.ui.steps.step_flow.QTimer.singleShot"):
            step = StepFlow(
                config=mock_config,
                secrets=MagicMock(),
                db=MagicMock(),
                loop=MagicMock(),
                shared_data=shared,
            )
        # 未选流程时应失败
        ok, msg = step.validate()
        assert ok is False, "StepFlow 未选时应失败"
        assert "流程" in msg
        step.deleteLater()

    def test_main_window_shows_step_flow(self, main_window, app):
        main_window._show_step(1)
        step = main_window._content_stack.layout().itemAt(0).widget()
        assert isinstance(step, StepFlow)


class TestMainWindowValidation:
    """集成测试：MainWindow 验证回调"""

    def test_on_next_respects_step_validation(self, main_window, app):
        """StepFlow 未选时 _on_next 不应前进"""
        main_window._show_step(1)
        initial = main_window._current_step
        main_window._on_next()
        # 由于验证失败，不应前进
        assert main_window._current_step == initial, (
            f"步骤1 验证失败时不应前进，但 current_step 从 {initial} 变为 {main_window._current_step}"
        )

    def test_on_next_passes_step_account(self, main_window, app):
        """StepAccount 默认预填，应能前进"""
        main_window._show_step(0)
        # StepAccount 默认已填欧阳改，验证通过
        step = main_window._content_stack.layout().itemAt(0).widget()
        ok, msg = step.validate()
        assert ok is True, f"StepAccount 验证应通过: {msg}"


class TestAllStepsHaveValidate:
    """所有步骤必须有 validate 方法"""

    def test_all_steps_have_validate(self, app, mock_config, mock_secrets):
        shared = {}
        # Patches: steps 1-5 use QTimer; StepReport doesn't
        patches = {
            "StepAccount": "workflow_test_desktop.ui.steps.step_account.QTimer.singleShot",
            "StepFlow": "workflow_test_desktop.ui.steps.step_flow.QTimer.singleShot",
            "StepForm": "workflow_test_desktop.ui.steps.step_form.QTimer.singleShot",
            "StepNodes": "workflow_test_desktop.ui.steps.step_nodes.QTimer.singleShot",
            "StepRun": "workflow_test_desktop.ui.steps.step_run.QTimer.singleShot",
            # StepReport doesn't use QTimer
        }
        for cls in [StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport]:
            patch_path = patches.get(cls.__name__)
            ctx = patch(patch_path) if patch_path else MagicMock()
            with ctx:
                step = cls(
                    config=mock_config,
                    secrets=mock_secrets,
                    db=MagicMock(),
                    loop=MagicMock(),
                    shared_data=shared,
                )
            assert hasattr(step, "validate"), f"{cls.__name__} 缺少 validate() 方法"
            # validate() 应返回 (bool, str)
            ok, msg = step.validate()
            assert isinstance(ok, bool), f"{cls.__name__}.validate() 应返回 bool"
            assert isinstance(msg, str), f"{cls.__name__}.validate() 应返回 str"
            step.deleteLater()


class TestStepNavigation:
    """导航测试"""

    def test_show_step_changes_content(self, main_window, app):
        """切换步骤应更新内容"""
        for i in range(6):
            main_window._show_step(i)
            step = main_window._content_stack.layout().itemAt(0).widget()
            expected_classes = [StepAccount, StepFlow, StepForm, StepNodes, StepRun, StepReport]
            assert isinstance(step, expected_classes[i])

    def test_nav_buttons_update(self, main_window, app):
        """导航按钮状态应随步骤更新"""
        main_window._show_step(0)
        assert not main_window._btn_prev.isEnabled()

        main_window._show_step(1)
        assert main_window._btn_prev.isEnabled()
