"""日志配置：滚动写入 ~/.workflow_test_desktop/logs/，保留7天"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime


def get_log_dir() -> Path:
    """获取日志目录，默认 ~/.workflow_test_desktop/logs/"""
    log_dir = Path.home() / ".workflow_test_desktop" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file_path() -> Path:
    """获取今日日志文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return get_log_dir() / f"app_{today}.log"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    初始化日志系统：
    - 控制台输出（INFO+）
    - 滚动文件输出（DEBUG+，保留7天）
    - 返回根 logger
    """
    log_dir = get_log_dir()
    log_file = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"

    root_logger = logging.getLogger("workflow_test_desktop")
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    # 格式化
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # 控制台 Handler（INFO+）
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # 滚动文件 Handler（DEBUG+，保留7天）
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 清理过期日志（启动时检查）
    _cleanup_old_logs(log_dir)

    root_logger.info("日志系统初始化完成，日志目录: %s", log_dir)
    return root_logger


def _cleanup_old_logs(log_dir: Path):
    """删除超过7天的日志文件"""
    import time
    cutoff = time.time() - 7 * 86400
    for f in log_dir.glob("app_*.log"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
