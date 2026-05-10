"""EnvironmentService：读取 .env 和 config/ 下非敏感配置"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


class EnvironmentError(Exception):
    """环境配置异常"""


@dataclass
class AppConfig:
    """统一配置对象（非敏感）

    所有路径以 /web/ 开头（无 /api/ 前缀），
    base_url + path 拼接为完整 URL（对标 invest 前端）。
    """
    env_id: str = "dev"
    gateway_url: str = ""
    login_path: str = "/web/user/api/login/user/login"
    logout_path: str = "/web/user/api/login/user/loginOut"
    user_directory_path: str = "/web/user/api/user/findByCompanyIdUserList"
    flow_catalog_path: str = "/web/flowTemplateApi/list"
    flow_detail_path: str = "/web/flowTemplateApi/findById"
    todo_list_path: str = "/web/flowJobTaskLink/findPendingByFlowInstanceId"
    node_action_path: str = "/web/flowInstanceApi/audit"
    flow_history_path: str = "/web/flowInstanceApi/history"
    _raw: dict[str, str] = field(default_factory=dict)


class EnvironmentService:
    """
    读取环境配置。优先级：
    1. 显式传入的 .env 文件路径
    2. WORKFLOW_ENV_FILE 环境变量
    3. 项目根目录 .env
    """

    _config: AppConfig | None = None

    def __init__(self, env_file: str | Path | None = None):
        self._env_file = self._resolve_env_file(env_file)

    def _resolve_env_file(self, env_file: str | Path | None) -> Path:
        if env_file:
            path = Path(env_file)
            if not path.exists():
                raise EnvironmentError(f"环境文件不存在: {path}")
            return path
        env_var = os.environ.get("WORKFLOW_ENV_FILE")
        if env_var:
            path = Path(env_var)
            if not path.exists():
                raise EnvironmentError(f"WORKFLOW_ENV_FILE 不存在: {path}")
            return path
        root = Path(__file__).parent.parent.parent
        default = root / ".env"
        if default.exists():
            return default
        raise EnvironmentError("未找到 .env 文件，请创建或指定 --env-file")

    def load(self) -> AppConfig:
        """加载并解析配置，返回 AppConfig（不含密钥）"""
        if self._config:
            return self._config
        raw = self._read_env_file()
        self._validate_required(raw)
        self._config = self._parse(raw)
        return self._config

    def _read_env_file(self) -> dict[str, str]:
        """读取 .env 文件，KEY=value 格式，支持 # 注释"""
        result: dict[str, str] = {}
        for line in self._env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
        return result

    def _validate_required(self, raw: dict[str, str]) -> None:
        required = ["GATEWAY_URL"]
        missing = [k for k in required if k not in raw]
        if missing:
            raise EnvironmentError(f"缺少必需配置: {', '.join(missing)}")

    def _parse(self, raw: dict[str, str]) -> AppConfig:
        return AppConfig(
            env_id=raw.get("ENV_ID", "dev"),
            gateway_url=raw["GATEWAY_URL"],
            login_path=raw.get("LOGIN_PATH", "/web/user/api/login/user/login"),
            logout_path=raw.get("LOGOUT_PATH", "/web/user/api/login/user/loginOut"),
            user_directory_path=raw.get("USER_DIRECTORY_PATH", "/web/user/api/user/findByCompanyIdUserList"),
            flow_catalog_path=raw.get("FLOW_CATALOG_PATH", "/web/flowTemplateApi/list"),
            flow_detail_path=raw.get("FLOW_DETAIL_PATH", "/web/flowTemplateApi/findById"),
            todo_list_path=raw.get("TODO_LIST_PATH", "/web/flowJobTaskLink/findPendingByFlowInstanceId"),
            node_action_path=raw.get("NODE_ACTION_PATH", "/web/flowInstanceApi/audit"),
            flow_history_path=raw.get("FLOW_HISTORY_PATH", "/web/flowInstanceApi/history"),
            _raw=raw,
        )

    def get_raw(self, key: str, default: str = "") -> str:
        """获取原始配置值（不含密钥的字段）"""
        return self.load()._raw.get(key, default)

    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.load().env_id in ("prod", "production")
