#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "========================================"
echo "  接口回归测试工作台 - 打包"
echo "========================================"

# 创建/激活虚拟环境
if [[ ! -f "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "创建虚拟环境..."
    bash "$ROOT_DIR/scripts/setup_venv.sh"
fi
source "$ROOT_DIR/.venv/bin/activate"

# 安装 PyInstaller
if ! command -v pyinstaller &>/dev/null; then
    echo "安装 PyInstaller..."
    pip install -q pyinstaller
fi

# 创建图标（如果没有）
ICON_DIR="$ROOT_DIR/resources"
ICON_PNG="$ICON_DIR/icon.png"
mkdir -p "$ICON_DIR"

if [[ ! -f "$ICON_PNG" ]]; then
    echo "生成应用图标..."
    python3 - <<'PYEOF'
import struct, zlib, base64

def create_png(size=256):
    def chunk(tag, data):
        c = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', c)

    # IHDR
    ihdr = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    ihdr_chunk = chunk(b'IHDR', ihdr)

    # IDAT - blue gradient with "R" letter hint
    raw = b''
    for y in range(size):
        raw += b'\x00'
        for x in range(size):
            cx, cy = x - size//2, y - size//2
            dist = (cx*cx + cy*cy) ** 0.5
            if dist < size * 0.42:
                r, g, b = 14, 165, 233  # accent blue #0EA5E9
            elif dist < size * 0.48:
                r, g, b = 10, 131, 194
            else:
                r, g, b = 240, 246, 249
            raw += bytes([r, g, b])
    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + ihdr_chunk + idat + iend

png_data = create_png(256)
with open('resources/icon.png', 'wb') as f:
    f.write(png_data)
print("icon.png created")
PYEOF
fi

# 运行 PyInstaller
SPEC_FILE="$ROOT_DIR/app.spec"
if [[ ! -f "$SPEC_FILE" ]]; then
    echo "❌ 缺少 app.spec，请检查项目配置"
    exit 1
fi

echo "运行 PyInstaller..."
pyinstaller "$SPEC_FILE" --noconfirm \
    --distpath "$ROOT_DIR/dist" \
    --workpath "$ROOT_DIR/build" \
    --clean

echo ""
echo "========================================"
echo "  打包完成！"
echo "  输出目录: dist/"
ls -lh "$ROOT_DIR/dist/" 2>/dev/null || echo "  (dist 目录尚未生成)"
echo ""
echo "  运行打包后的应用:"
echo "  open dist/workflow_test_desktop.app"
echo "========================================"
