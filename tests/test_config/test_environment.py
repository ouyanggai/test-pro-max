"""测试 EnvironmentService"""
import pytest
from pathlib import Path
from workflow_test_desktop.core.config.environment import (
    EnvironmentService, AppConfig, EnvironmentError
)


def test_load_success(mock_env_file):
    """测试正常加载配置"""
    svc = EnvironmentService(env_file=mock_env_file)
    cfg = svc.load()
    assert isinstance(cfg, AppConfig)
    assert cfg.gateway_url == "https://dev.example.com"
    assert cfg.login_path == "/api/auth/login"


def test_missing_required_key(tmp_path):
    """测试缺少必需配置时抛出异常"""
    env_file = tmp_path / ".env"
    env_file.write_text("LOGIN_PATH=/api/auth/login\n")  # 缺少 GATEWAY_URL
    with pytest.raises(EnvironmentError, match="缺少必需配置"):
        EnvironmentService(env_file=env_file).load()


def test_env_file_not_found():
    """测试环境文件不存在时抛出异常"""
    with pytest.raises(EnvironmentError, match="环境文件不存在"):
        EnvironmentService(env_file="/nonexistent/.env").load()


def test_get_raw(mock_env_file):
    """测试获取原始值"""
    svc = EnvironmentService(env_file=mock_env_file)
    assert svc.get_raw("GATEWAY_URL") == "https://dev.example.com"
    assert svc.get_raw("MISSING_KEY", "default") == "default"


def test_is_production(mock_env_file):
    """测试生产环境判断"""
    svc = EnvironmentService(env_file=mock_env_file)
    assert svc.is_production() is False
