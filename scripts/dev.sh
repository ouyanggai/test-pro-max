#!/usr/bin/env bash
set -euo pipefix

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 如果没有 venv，先安装
if [[ ! -f "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "首次运行，先安装环境..."
    bash "$ROOT_DIR/scripts/setup_venv.sh"
fi

# 启动
bash "$ROOT_DIR/scripts/run_workbench.sh"
