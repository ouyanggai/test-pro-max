"""
主程序入口
"""
import sys
import logging
from pathlib import Path

from workflow_test_desktop.config.themes import build_theme_css, LIGHT


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(env_file_path: str = ".env") -> int:
    """主入口（Task 1 stub: 仅展示欢迎界面）"""

    # 动态检查 Qt 是否可用
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
        from PySide6.QtCore import Qt
    except ImportError:
        print("错误: 需要安装 PySide6")
        print("  pip install PySide6")
        return 1

    # 动态检查 qasync
    try:
        import qasync
    except ImportError:
        print("错误: 需要安装 qasync")
        print("  pip install qasync")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("接口回归测试工作台")

    # 构建主题 CSS
    css = build_theme_css(LIGHT)
    app.setStyleSheet(css)

    # 尝试加载配置（容错：不阻塞启动）
    config = None
    env_file = Path(env_file_path)
    env_info = f"未配置（{env_file})"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or not line or "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            if key == "ENV_ID":
                env_info = f"env={line.split('=', 1)[1].strip()}"
                break
        if env_info == f"未配置（{env_file}）":
            env_info = f"env=dev（未指定 ENV_ID）"

    # 展示欢迎窗口
    from workflow_test_desktop.config.themes import FONT_FAMILY, RADIUS_CARD

    w = QWidget()
    w.setWindowTitle("接口回归测试工作台")
    layout = QVBoxLayout(w)
    layout.setContentsMargins(40, 40, 40, 40)
    layout.setSpacing(16)

    title = QLabel("接口回归测试工作台")
    title.setFont(FONT_FAMILY)
    title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0EA5E9; padding-bottom: 8px;")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    status = QLabel(f"当前状态: ✅ 脚手架就绪  |  {env_info}")
    status.setFont(FONT_FAMILY)
    status.setStyleSheet("color: #10B981; padding: 8px; background: #F0FDF4; "
                        f"border-radius: {RADIUS_CARD}; border: 1px solid #BBF7D0;")
    status.setAlignment(Qt.AlignCenter)
    layout.addWidget(status)

    tasks = (
        "📋 开发进度\n\n"
        "  ✅ Task 1   项目脚手架\n"
        "  ⏳ Task 2   配置层与存储层\n"
        "  ⬜ Task 3   会话管理层\n"
        "  ⬜ Task 4   流程服务层\n"
        "  ⬜ Task 5   指派引擎\n"
        "  ⬜ Task 6   执行调度层\n"
        "  ⬜ Task 7   UI 层\n"
        "  ⬜ Task 8   报告导出层"
    )
    info = QLabel(tasks)
    info.setFont(FONT_FAMILY)
    info.setStyleSheet(
        f"background: #F9FAFB; border: 1px solid #E5E7EB; "
        f"border-radius: {RADIUS_CARD}; padding: 16px; color: #374151;"
    )
    info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    layout.addWidget(info, 1)

    hint = QLabel("关闭此窗口即退出程序。完成后可通过 scripts/run_workbench.sh 启动完整版。")
    hint.setFont(FONT_FAMILY)
    hint.setStyleSheet("color: #9CA3AF; font-size: 12px;")
    hint.setAlignment(Qt.AlignCenter)
    layout.addWidget(hint)

    w.resize(480, 520)
    w.show()

    # 初始化 qasync 事件循环
    loop = qasync.QEventLoop(app)
    with loop:
        loop.run_forever()

    return 0
