#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-.env}"

echo "🚀 启动接口回归测试工作台"
echo "   环境文件: $ENV_FILE"

# 检查依赖
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "❌ 缺少 PySide6，正在安装..."
    pip install -r requirements.txt
fi

if ! python3 -c "import qasync" 2>/dev/null; then
    echo "❌ 缺少 qasync，正在安装..."
    pip install qasync
fi

python3 -m workflow_test_desktop --env-file "$ENV_FILE"
