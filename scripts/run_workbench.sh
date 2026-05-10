#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-.env}"

echo "🚀 启动接口回归测试工作台"

# 如果有 venv，优先使用
if [[ -f "$ROOT_DIR/.venv/bin/python" ]]; then
    source "$ROOT_DIR/.venv/bin/activate"
    echo "   使用虚拟环境: .venv"
elif python3 -c "import PySide6" 2>/dev/null; then
    echo "   使用系统 Python"
else
    echo "❌ 缺少 PySide6，请先运行: scripts/setup_venv.sh"
    exit 1
fi

echo "   环境文件: $ENV_FILE"
python -m workflow_test_desktop --env-file "$ENV_FILE"
