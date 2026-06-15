#!/bin/bash
# Claude Monitor 安装脚本

set -e

INSTALL_DIR="$HOME/Developer/claude-monitor"
LINK_PATH="$HOME/.local/bin/claude-monitor"

echo "🚀 安装 Claude Monitor..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.8+"
    exit 1
fi

# 检查并安装 rich
if ! python3 -c "import rich" &> /dev/null; then
    echo "📦 安装 rich 库..."
    pip3 install rich
fi

# 创建安装目录
mkdir -p "$INSTALL_DIR"
mkdir -p "$(dirname "$LINK_PATH")"

# 复制脚本
cp "$(dirname "$0")/claude_monitor.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/claude_monitor.py"

# 创建符号链接
ln -sf "$INSTALL_DIR/claude_monitor.py" "$LINK_PATH"

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  claude-monitor              # 启动监控（默认 30s 刷新）"
echo "  claude-monitor -i 10        # 10s 刷新"
echo "  claude-monitor --once       # 只显示一次"
echo "  claude-monitor -h           # 查看帮助"
echo ""
echo "💡 可以在多个终端窗口同时运行，数据共享"
echo ""
