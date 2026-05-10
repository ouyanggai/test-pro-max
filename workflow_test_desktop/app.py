"""主程序入口 + qasync 事件循环初始化"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

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
from workflow_test_desktop.core.storage.database import DBManager
from workflow_test_desktop.ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(env_file_path: str | None = None) -> int:
    """主入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("接口回归测试工作台")

    loop = qasync.QEventLoop(app)

    try:
        env_svc = EnvironmentService(env_file_path)
        config = env_svc.load()
        secrets = SecretProvider(env_file_path or str(Path(__file__).parent / ".env"))

        db_path = Path(__file__).parent / "workflow_runs.db"

        async def init_db():
            db_manager = DBManager(db_path)
            async with db_manager:
                return db_manager

        with loop:
            db = loop.run_until_complete(init_db())

            window = MainWindow(config=config, secrets=secrets, db=db, loop=loop)
            window.resize(1200, 760)
            window.show()

            loop.run_forever()

    except Exception:
        logger.exception("启动失败")
        return 1
    return 0
