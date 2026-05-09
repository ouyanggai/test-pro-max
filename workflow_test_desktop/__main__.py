from __future__ import annotations

import argparse
import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from workflow_test_desktop.qt_workbench import create_workbench_window
from workflow_test_desktop.workbench import (
    build_workbench_snapshot,
    load_environment_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="接口编排自动化测试工具")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--verify-startup", action="store_true")
    args = parser.parse_args()

    if args.verify_startup:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    env_file = Path(args.env_file)
    if env_file.exists():
        config = load_environment_config(env_file)
    else:
        config = load_environment_config(_empty_env_file())

    app = QApplication.instance() or QApplication([])
    apply_stylesheet(app, theme="light_blue.xml")
    window = create_workbench_window(build_workbench_snapshot(config))
    window.show()

    if args.verify_startup:
        QTimer.singleShot(100, app.quit)

    app.exec()
    print("Workbench startup verified")
    return 0


def _empty_env_file() -> Path:
    path = Path(os.environ.get("TMPDIR", "/tmp")) / "workflow-test-desktop-empty.env"
    path.write_text("", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
