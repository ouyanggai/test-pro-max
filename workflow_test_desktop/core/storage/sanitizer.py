"""统一脱敏工具：禁止各模块自行处理，所有写入必须经此"""
from __future__ import annotations

import re
import urllib.parse
from typing import Any


_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(token|api_token|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(sid|session_id)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(cookie)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(authorization)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"(client_secret|secret)[\"']?\s*[:=]\s*[\"']?([^\"',\s]+)", re.IGNORECASE),
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]+)", re.IGNORECASE),
    re.compile(r"sid=([a-zA-Z0-9_\-]{16,})", re.IGNORECASE),
]


def sanitize(value: str | None) -> str | None:
    """对单个字符串值脱敏（不处理 dict/list，只处理字符串内容）"""
    if value is None:
        return None
    result = value
    for pattern in _SENSITIVE_PATTERNS:
        if "Bearer" in pattern.pattern:
            result = pattern.sub(lambda m: "****", result)
        else:
            result = pattern.sub(lambda m: f'"{m.group(1)}": "****"', result)
    return result


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """递归脱敏字典"""
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            result[k] = sanitize_dict(v)
        elif isinstance(v, list):
            result[k] = sanitize_list(v)
        elif isinstance(v, str):
            result[k] = _sanitize_dict_value(k, v)
        else:
            result[k] = v
    return result


def sanitize_list(data: list[Any]) -> list[Any]:
    """递归脱敏列表"""
    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(sanitize_dict(item))
        elif isinstance(item, list):
            result.append(sanitize_list(item))
        elif isinstance(item, str):
            result.append(sanitize(item))
        else:
            result.append(item)
    return result


def _sanitize_dict_value(key: str, value: str) -> str:
    """对字典中的字符串值脱敏，同时考虑 key 名称"""
    result = sanitize(value)
    # 如果 key 名含敏感词，强制脱敏
    if _looks_like_sensitive(key) and result != "****":
        return "****"
    return result


def _looks_like_sensitive(s: str) -> bool:
    """判断字符串是否像敏感值"""
    sensitive_keywords = [
        "password", "passwd", "pwd",
        "token", "api_token", "access_token",
        "sid", "session_id",
        "authorization",
        "secret", "client_secret",
        "nacos_token",
    ]
    return any(kw in s.lower() for kw in sensitive_keywords)


def sanitize_request_summary(method: str, url: str,
                             params: dict | None = None,
                             headers: dict | None = None) -> dict[str, Any]:
    """生成安全的请求摘要（用于写入数据库/报告）"""
    summary: dict[str, Any] = {
        "method": method.upper(),
        "url": _mask_url_credentials(url),
    }
    if params:
        summary["params"] = sanitize_dict(params)
    if headers:
        summary["headers"] = _sanitize_headers(headers)
    return summary


def sanitize_response_summary(status_code: int,
                              body_preview: str | None = None) -> dict[str, Any]:
    """生成安全的响应摘要"""
    return {
        "status_code": status_code,
        "body_preview": sanitize(body_preview) if body_preview else None,
    }


def _mask_url_credentials(url: str) -> str:
    """URL 中移除用户信息（支持 user:pass@host 格式）"""
    try:
        parsed = urllib.parse.urlparse(url)
        # Python 3.12+ 需要用 parse_qs 解开 user:pass
        userinfo = parsed.netloc.split("@")[0] if "@" in parsed.netloc else ""
        if userinfo:
            netloc = parsed.netloc[len(userinfo) + 1:]
            return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return url


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """headers 中移除授权相关值"""
    result = {}
    auth_keys = {"authorization", "cookie", "x-api-token", "x-sid"}
    for k, v in headers.items():
        if k.lower() in auth_keys or "auth" in k.lower() or "token" in k.lower():
            result[k] = "****"
        else:
            result[k] = v
    return result
