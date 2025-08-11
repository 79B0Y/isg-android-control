#!/bin/bash
# Android Controller Service - macOS启动脚本

cd "$(dirname "$0")"

echo "🚀 启动Android Controller Service (macOS版)"

# 检查虚拟环境
if [[ ! -d "venv" ]]; then
    echo "❌ 错误: 虚拟环境不存在，请先运行 ./install-mac.sh"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活Python虚拟环境..."
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 检查Redis服务
echo "🔍 检查Redis服务..."
if ! brew services list | grep redis | grep -q started; then
    echo "⚠️  Redis服务未运行，正在启动..."
    brew services start redis
    sleep 2
fi

# 检查ADB连接
echo "🔍 检查ADB连接..."
if command -v adb >/dev/null 2>&1; then
    if ! adb devices | grep -q "device$"; then
        echo "⚠️  警告: 未检测到ADB设备连接"
        echo "请先连接Android设备: ./connect.sh <设备IP>:5555"
        echo "或使用Android Studio的设备管理器连接模拟器"
    else
        echo "✅ ADB设备连接正常"
    fi
else
    echo "❌ ADB未安装，请运行: brew install android-platform-tools"
    exit 1
fi

# 显示启动信息
echo ""
echo "=========================================="
echo "🎮 Android Controller Service"
echo "=========================================="
echo "📡 API文档: http://localhost:8000/docs"
echo "🏠 Home Assistant: 配置MQTT broker后可用"
echo "⌨️  按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动服务
python -m src.main --config configs/config.yaml "$@"
