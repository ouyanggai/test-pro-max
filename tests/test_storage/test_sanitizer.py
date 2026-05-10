"""测试脱敏工具"""
import pytest
from workflow_test_desktop.core.storage.sanitizer import (
    sanitize, sanitize_dict, sanitize_list,
    sanitize_request_summary, sanitize_response_summary,
)


def test_sanitize_none():
    assert sanitize(None) is None


def test_sanitize_normal_string():
    assert sanitize("hello world") == "hello world"


def test_sanitize_password():
    result = sanitize('{"password": "secret123"}')
    assert "secret123" not in result
    assert "****" in result


def test_sanitize_token():
    result = sanitize('"token": "abc_xyz_token"')
    assert "abc_xyz_token" not in result
    assert "****" in result


def test_sanitize_bearer():
    result = sanitize("Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0")
    assert "eyJ" not in result
    assert "****" in result


def test_sanitize_dict():
    data = {
        "username": "testuser",
        "password": "supersecret",
        "nested": {"token": "tok_123"},
    }
    result = sanitize_dict(data)
    assert result["username"] == "testuser"
    assert result["password"] == "****"
    assert result["nested"]["token"] == "****"


def test_sanitize_list():
    data = [
        {"name": "item1", "password": "pass1"},
        "plain_string",
        [1, 2, 3],
    ]
    result = sanitize_list(data)
    assert result[0]["password"] == "****"
    assert result[1] == "plain_string"
    assert result[2] == [1, 2, 3]


def test_sanitize_request_summary():
    result = sanitize_request_summary(
        method="POST",
        url="https://api.example.com/login",
        params={"username": "admin", "password": "secret123"},
        headers={"Authorization": "Bearer token_abc"},
    )
    assert result["method"] == "POST"
    assert result["params"]["username"] == "admin"
    assert result["params"]["password"] == "****"
    assert result["headers"]["Authorization"] == "****"


def test_sanitize_response_summary():
    result = sanitize_response_summary(200, '{"status": "ok", "sid": "real_sid_here"}')
    assert result["status_code"] == 200
    assert "real_sid_here" not in str(result["body_preview"])


def test_mask_url_credentials():
    result = sanitize_request_summary("GET", "https://user:pass@api.example.com/secure", {}, {})
    assert "user:pass" not in result["url"]
    assert "api.example.com" in result["url"]
