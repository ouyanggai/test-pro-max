#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="$ROOT_DIR/.venv"

echo "========================================"
echo "  接口回归测试工作台 - 环境安装"
echo "========================================"

# 创建纯净 venv
if [[ ! -d "$VENV_DIR" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

echo "升级 pip..."
pip install --upgrade pip -q

echo "安装依赖..."
pip install -q PySide6==6.11.0 qasync==0.28.0 httpx==0.28.1 aiosqlite==0.22.1 pytest==9.0.2 pytest-asyncio==1.3.0

echo ""
echo "========================================"
echo "  安装完成！"
echo "  激活方式: source .venv/bin/activate"
echo "  启动方式: scripts/run_workbench.sh"
echo "========================================"
