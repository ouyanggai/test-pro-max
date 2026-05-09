from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping


@dataclass(frozen=True)
class EnvironmentConfig:
    env_name: str
    api_gateway: str
    required_secret_names: tuple[str, ...] = ()
    provided_secrets: Mapping[str, str] = field(default_factory=dict)
    connection_checker: Callable[[str], bool] | None = None


@dataclass(frozen=True)
class LayoutSnapshot:
    sections: tuple[str, ...]
    toolbar_height_px: int
    status_bar_height_px: int


@dataclass(frozen=True)
class EnvironmentSnapshot:
    env_name: str
    display_name: str
    api_gateway: str


@dataclass(frozen=True)
class ConnectionSnapshot:
    status: str
    missing_secret_names: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class WorkbenchSnapshot:
    layout: LayoutSnapshot
    environment: EnvironmentSnapshot
    connection: ConnectionSnapshot
    status_text: str


def load_environment_config(
    env_file: str | Path,
    *,
    required_secret_names: tuple[str, ...] = (),
) -> EnvironmentConfig:
    values = _read_env_file(Path(env_file))
    provided_secrets = {
        name: values[name] for name in required_secret_names if values.get(name)
    }

    return EnvironmentConfig(
        env_name=values.get("TEST_ENV_NAME", "local-dry-run"),
        api_gateway=values.get("GATEWAY_URL", ""),
        required_secret_names=required_secret_names,
        provided_secrets=provided_secrets,
    )


def build_workbench_snapshot(config: EnvironmentConfig) -> WorkbenchSnapshot:
    missing_secret_names = tuple(
        name for name in config.required_secret_names if not config.provided_secrets.get(name)
    )
    if not config.api_gateway.strip():
        connection = ConnectionSnapshot(
            status="unconfigured",
            missing_secret_names=(),
            message="API 网关未配置",
        )
    elif missing_secret_names:
        connection = ConnectionSnapshot(
            status="missing_secrets",
            missing_secret_names=missing_secret_names,
            message="缺少密钥配置：" + ", ".join(missing_secret_names),
        )
    elif config.connection_checker:
        connected = config.connection_checker(config.api_gateway)
        connection = ConnectionSnapshot(
            status="connected" if connected else "failed",
            missing_secret_names=(),
            message="环境连接正常" if connected else "环境连接失败",
        )
    else:
        connection = ConnectionSnapshot(
            status="unchecked",
            missing_secret_names=(),
            message="环境连接尚未检查",
        )

    return WorkbenchSnapshot(
        layout=LayoutSnapshot(
            sections=("navigation", "main", "details"),
            toolbar_height_px=32,
            status_bar_height_px=24,
        ),
        environment=EnvironmentSnapshot(
            env_name=config.env_name,
            display_name=_environment_display_name(config.env_name),
            api_gateway=config.api_gateway,
        ),
        connection=connection,
        status_text=_status_text(config, connection),
    )


def _read_env_file(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _environment_display_name(env_name: str) -> str:
    names = {
        "local-dry-run": "本地演示环境",
        "dev-test": "开发测试环境",
    }
    return names.get(env_name, env_name or "未命名环境")


def _status_text(config: EnvironmentConfig, connection: ConnectionSnapshot) -> str:
    gateway = config.api_gateway or "未配置"
    return (
        f"环境：{_environment_display_name(config.env_name)} | "
        f"网关：{gateway} | "
        f"状态：{connection.message}"
    )
