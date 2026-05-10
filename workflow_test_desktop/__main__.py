"""入口：python -m workflow_test_desktop"""
import sys
import argparse
from pathlib import Path

from workflow_test_desktop.app import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="接口编排自动化测试工具")
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="环境配置文件路径（默认: .env）",
    )
    args = parser.parse_args()

    env_path = Path(args.env_file).resolve()
    if not env_path.exists():
        print(f"警告: 环境文件不存在: {env_path}，将使用系统环境变量")

    sys.exit(main(str(env_path)))
