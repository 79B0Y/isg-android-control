#!/bin/bash
# Android Controller Service 启动脚本

cd "$(dirname "$0")"

if [[ ! -d "venv" ]]; then
    echo "错误: 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

echo "启动Android Controller Service..."
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 检查ADB连接
if command -v adb >/dev/null 2>&1; then
    if ! adb devices | grep -q "device$"; then
        echo "警告: 未检测到ADB设备连接"
        echo "请确保设备已通过ADB连接 (adb connect <IP>:5555)"
    fi
else
    echo "警告: ADB未安装，部分功能可能无法使用"
fi

# 启动服务
echo "正在启动服务..."
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "=========================================="

python -m src.main --config configs/config.yaml "$@"