#!/bin/bash
# Android Controller Service 停止脚本

echo "停止Android Controller Service..."

# 查找并停止进程
PIDS=$(pgrep -f "src.main" 2>/dev/null || true)

if [[ -n "$PIDS" ]]; then
    echo "发现进程: $PIDS"
    kill -TERM $PIDS
    
    # 等待进程结束
    sleep 3
    
    # 检查是否还在运行
    if pgrep -f "src.main" >/dev/null 2>&1; then
        echo "强制终止进程..."
        pkill -KILL -f "src.main"
    fi
    
    echo "✓ 服务已停止"
else
    echo "未找到运行中的服务"
fi

# 清理PID文件
rm -f data/android_controller.pid 2>/dev/null || true