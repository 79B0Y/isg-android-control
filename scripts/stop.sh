#!/bin/bash

# Android Controller Service 停止脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

log_info "停止Android Controller Service..."

PID_FILE="data/android_controller.pid"
FOUND_PROCESS=false

# 方法1：通过PID文件停止
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        log_info "通过PID文件停止服务 (PID: $PID)"
        kill -TERM "$PID"
        
        # 等待进程结束
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # 如果进程仍在运行，强制杀死
        if kill -0 "$PID" 2>/dev/null; then
            log_info "正常停止失败，强制终止进程"
            kill -KILL "$PID"
        fi
        
        FOUND_PROCESS=true
        rm -f "$PID_FILE"
    else
        log_info "PID文件中的进程不存在，清理PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 方法2：通过进程名查找并停止
PIDS=$(pgrep -f "src.main" 2>/dev/null || true)

if [[ -n "$PIDS" ]]; then
    log_info "发现Android Controller进程: $PIDS"
    
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            log_info "停止进程: $PID"
            kill -TERM "$PID"
            
            # 等待进程结束
            for i in {1..5}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # 如果进程仍在运行，强制杀死
            if kill -0 "$PID" 2>/dev/null; then
                log_info "强制终止进程: $PID"
                kill -KILL "$PID"
            fi
            
            FOUND_PROCESS=true
        fi
    done
fi

# 方法3：通过端口查找并停止
if command -v lsof >/dev/null 2>&1; then
    # 检查默认端口8000
    PORT_PIDS=$(lsof -t -i:8000 2>/dev/null || true)
    
    if [[ -n "$PORT_PIDS" ]]; then
        for PID in $PORT_PIDS; do
            # 检查是否是我们的服务
            if ps -p "$PID" -o command= | grep -q "src.main"; then
                log_info "通过端口找到进程，停止: $PID"
                kill -TERM "$PID" 2>/dev/null || true
                FOUND_PROCESS=true
            fi
        done
    fi
fi

# 清理临时文件
log_info "清理临时文件..."
rm -f data/android_controller.pid
rm -f data/*.tmp

# 显示结果
if [[ "$FOUND_PROCESS" = true ]]; then
    log_success "Android Controller Service 已停止"
else
    log_info "未找到运行中的Android Controller Service"
fi

# 显示当前状态
sleep 1
REMAINING_PIDS=$(pgrep -f "src.main" 2>/dev/null || true)
if [[ -n "$REMAINING_PIDS" ]]; then
    log_error "仍有相关进程在运行: $REMAINING_PIDS"
    log_info "如需强制停止，请运行: kill -9 $REMAINING_PIDS"
else
    log_success "所有相关进程已停止"
fi