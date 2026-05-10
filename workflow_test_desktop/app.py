"""主程序入口 + qasync 事件循环初始化"""
from __future__ import annotations

import sys
import logging
import asyncio
import base64
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


# ─── 登录函数（对标 invest 前端 Login.vue）──────────────────────
# invest 前端登录请求格式：
#   POST /web/user/api/login/user/login
#   Body: { data: { account, password(base64), platformCode, customerCode, code }, sign: "" }


async def _do_login(env_id: str, login_type: str, username: str, password: str) -> dict:
    """
    调用登录接口，返回原始响应 dict。
    SessionManager 会从中提取 sid（通过 login_result.get("data", {}).get("sid")）。
    """
    from workflow_test_desktop.api.client import ApiClient, ApiError

    # 根据 env_id 决定 gateway_url
    env_svc = EnvironmentService()
    cfg = env_svc.load()
    gateway = cfg.gateway_url

    try:
        async with ApiClient(gateway) as client:
            # 密码 base64 编码（invest 前端用 $Encrypt 混淆，此处简化用纯 base64）
            encoded_password = base64.b64encode(password.encode()).decode()

            # 对标 invest 前端 Login.vue POST body
            body = {
                "data": {
                    "account": username,
                    "password": encoded_password,
                    "platformCode": "200001",
                    "customerCode": "",   # 从平台接口获取，简化置空
                    "code": "",          # 验证码，测试环境可能为空
                },
                "sign": "",
            }

            resp = await client.post(
                "/web/user/api/login/user/login",
                json=body,
            )
            data = resp.json()

            # 对标 invest 前端：isSuccess === false 时抛异常
            if data.get("isSuccess") is False:
                msg = data.get("message", "登录失败")
                raise RuntimeError(f"登录失败: {msg}")

            return data

    except ApiError as e:
        raise RuntimeError(f"登录接口调用失败: {e}")


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

    # 初始化 SessionManager（对标 invest 前端的 SID 会话管理）
    from workflow_test_desktop.core.session.manager import SessionManager
    sm = SessionManager(secret_provider=secrets, login_func=_do_login)
    SessionManager.set_instance(sm)

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
