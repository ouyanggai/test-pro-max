from workflow_test_desktop.workbench import (
    EnvironmentConfig,
    build_workbench_snapshot,
    load_environment_config,
)


def test_workbench_shows_layout_and_environment_without_leaking_secret_values():
    config = EnvironmentConfig(
        env_name="local-dry-run",
        api_gateway="http://127.0.0.1:38081/api",
        required_secret_names=("APPLICANT_PASSWORD", "NACOS_TOKEN"),
        provided_secrets={"APPLICANT_PASSWORD": "super-secret-password"},
    )

    snapshot = build_workbench_snapshot(config)

    assert snapshot.layout.sections == ("navigation", "main", "details")
    assert snapshot.layout.toolbar_height_px == 32
    assert snapshot.layout.status_bar_height_px == 24
    assert snapshot.environment.env_name == "local-dry-run"
    assert snapshot.environment.display_name == "本地演示环境"
    assert snapshot.environment.api_gateway == "http://127.0.0.1:38081/api"
    assert snapshot.connection.status == "missing_secrets"
    assert snapshot.connection.missing_secret_names == ("NACOS_TOKEN",)
    assert "super-secret-password" not in snapshot.connection.message


def test_workbench_snapshot_uses_chinese_environment_display_name():
    config = EnvironmentConfig(
        env_name="local-dry-run",
        api_gateway="http://127.0.0.1:38081/api",
    )

    snapshot = build_workbench_snapshot(config)

    assert snapshot.environment.display_name == "本地演示环境"
    assert "dry-run" not in snapshot.status_text
    assert snapshot.status_text == "环境：本地演示环境 | 网关：http://127.0.0.1:38081/api | 状态：环境连接尚未检查"


def test_workbench_reports_unconfigured_when_api_gateway_is_blank():
    config = EnvironmentConfig(
        env_name="local-dry-run",
        api_gateway="",
    )

    snapshot = build_workbench_snapshot(config)

    assert snapshot.connection.status == "unconfigured"
    assert snapshot.connection.message == "API 网关未配置"


def test_workbench_reports_connected_when_gateway_check_succeeds():
    config = EnvironmentConfig(
        env_name="local-dry-run",
        api_gateway="http://127.0.0.1:38081/api",
        connection_checker=lambda gateway: gateway.endswith("/api"),
    )

    snapshot = build_workbench_snapshot(config)

    assert snapshot.connection.status == "connected"
    assert snapshot.connection.message == "环境连接正常"


def test_workbench_reports_failed_when_gateway_check_fails():
    config = EnvironmentConfig(
        env_name="local-dry-run",
        api_gateway="http://127.0.0.1:38081/api",
        connection_checker=lambda gateway: False,
    )

    snapshot = build_workbench_snapshot(config)

    assert snapshot.connection.status == "failed"
    assert snapshot.connection.message == "环境连接失败"


def test_load_environment_config_reads_non_secret_values_and_secret_presence(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TEST_ENV_NAME=dev-test",
                "GATEWAY_URL=http://192.168.1.220:38081/api",
                "APPLICANT_PASSWORD=hidden-value",
            ]
        ),
        encoding="utf-8",
    )

    config = load_environment_config(
        env_file,
        required_secret_names=("APPLICANT_PASSWORD", "NACOS_TOKEN"),
    )
    snapshot = build_workbench_snapshot(config)

    assert snapshot.environment.env_name == "dev-test"
    assert snapshot.environment.api_gateway == "http://192.168.1.220:38081/api"
    assert snapshot.connection.missing_secret_names == ("NACOS_TOKEN",)
    assert "hidden-value" not in snapshot.connection.message
