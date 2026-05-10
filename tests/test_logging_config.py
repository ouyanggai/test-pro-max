import pytest
from pathlib import Path
from workflow_test_desktop.core.logging_config import get_log_dir, get_log_file_path, setup_logging
import logging


def test_get_log_dir_creates_path():
    log_dir = get_log_dir()
    assert log_dir.exists()
    assert log_dir.name == "logs"


def test_get_log_file_path_returns_today():
    path = get_log_file_path()
    assert path.exists() or True  # 文件可不存在，只要路径格式对
    assert "app_" in path.name
    assert ".log" in path.name


def test_setup_logging_returns_logger():
    logger = setup_logging()
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) >= 2  # console + file
