"""主程序入口 + qasync 事件循环初始化"""
from __future__ import annotations

import sys
import logging
import asyncio
from pathlib import Path

from workflow_test_desktop.core.logging_config import setup_logging

logger = setup_logging(logging.INFO)

try:
    import qasync
except ImportError:
    print("错误: 需要安装 qasync")
    print("  pip install qasync")
    sys.exit(1)

from PySide6.QtWidgets import QApplication

from workflow_test_desktop.config.themes import build_theme_css, LIGHT
from workflow_test_desktop.core.config.environment import EnvironmentService
from workflow_test_desktop.core.config.secrets import SecretProvider
from workflow_test_desktop.core.storage.database import get_db
from workflow_test_desktop.ui.main_window import MainWindow



def main(env_file_path: str | None = None) -> int:
    """主入口"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("接口回归测试工作台")

    # 先加载所有同步配置
    try:
        env_svc = EnvironmentService(env_file_path)
        config = env_svc.load()
        secrets = SecretProvider(env_file_path or str(Path(__file__).parent / ".env"))
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        # 容错：继续启动，UI 层会显示未配置状态
        config = None
        secrets = None

    # 数据库路径
    db_path = Path(__file__).parent / "workflow_runs.db"

    # qasync 事件循环
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        with loop:
            # 初始化数据库（异步，在 Qt 事件循环内运行）
            async def init_db():
                return await get_db(db_path)

            db = loop.run_until_complete(init_db())

            # 创建并显示主窗口
            window = MainWindow(config=config, secrets=secrets, db=db, loop=loop)
            window.resize(1200, 760)
            window.show()

            # 运行 Qt 事件循环
            loop.run_forever()

    except Exception:
        logger.exception("启动失败")
        return 1
    return 0
