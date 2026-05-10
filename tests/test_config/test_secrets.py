"""测试 SecretProvider"""
import pytest
from pathlib import Path
from workflow_test_desktop.core.config.secrets import SecretProvider


def test_get_success(tmp_path):
    """测试正常获取密钥"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GATEWAY_URL=https://api.example.com\n"
        "TEST_PASSWORD=secret123\n"
        "API_TOKEN=token_abc\n"
    )
    sp = SecretProvider(env_file=env_file)
    assert sp.get("TEST_PASSWORD") == "secret123"
    assert sp.get("API_TOKEN") == "token_abc"


def test_get_case_insensitive(tmp_path):
    """测试大小写不敏感"""
    env_file = tmp_path / ".env"
    env_file.write_text("MY_SECRET=abc123\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get("my_secret") == "abc123"
    assert sp.get("MY_SECRET") == "abc123"


def test_get_default(tmp_path):
    """测试默认值"""
    env_file = tmp_path / ".env"
    env_file.write_text("GATEWAY_URL=https://api.example.com\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get("MISSING") is None
    assert sp.get("MISSING", "default_val") == "default_val"


def test_get_password_shortcut(tmp_path):
    """测试 get_password 快捷方法"""
    env_file = tmp_path / ".env"
    env_file.write_text("PASSWORD=pass123\n")
    sp = SecretProvider(env_file=env_file)
    assert sp.get_password() == "pass123"
    assert sp.get_token() is None


def test_is_sensitive_key():
    """测试敏感字段判断"""
    sp = SecretProvider(env_file="/dev/null")
    for key in ["password", "PASSWORD", "token", "sid", "authorization", "client_secret"]:
        assert sp.is_sensitive_key(key), f"{key} should be sensitive"


def test_file_not_found(tmp_path):
    """测试文件不存在时抛出异常"""
    nonexistent = tmp_path / "nonexistent.env"
    sp = SecretProvider(env_file=nonexistent)
    with pytest.raises(FileNotFoundError):
        sp.get("KEY")
