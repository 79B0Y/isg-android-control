#!/bin/bash

# Android Controller Service 启动脚本

set -e

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

log_info "启动Android Controller Service..."

# 检查虚拟环境
if [[ ! -d "venv" ]]; then
    log_error "虚拟环境不存在，请先运行 ./scripts/install.sh"
    exit 1
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate

# 检查配置文件
if [[ ! -f "configs/config.yaml" ]]; then
    log_error "配置文件不存在: configs/config.yaml"
    exit 1
fi

# 检查数据目录
mkdir -p data/{logs,screenshots}

# 检查ADB连接
log_info "检查ADB连接..."
if command -v adb >/dev/null 2>&1; then
    if ! adb devices | grep -q "device$"; then
        log_error "未检测到ADB设备连接"
        log_info "请运行: ./scripts/setup_adb.sh"
        exit 1
    fi
    log_success "ADB设备连接正常"
else
    log_error "ADB未安装，请先运行安装脚本"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# 解析命令行参数
CONFIG_FILE="configs/config.yaml"
HOST=""
PORT=""
DEBUG=false

while getopts "c:h:p:d" opt; do
    case $opt in
        c)
            CONFIG_FILE="$OPTARG"
            ;;
        h)
            HOST="$OPTARG"
            ;;
        p)
            PORT="$OPTARG"
            ;;
        d)
            DEBUG=true
            ;;
        \?)
            echo "用法: $0 [-c config_file] [-h host] [-p port] [-d]"
            echo "  -c  配置文件路径 (默认: configs/config.yaml)"
            echo "  -h  绑定主机地址"
            echo "  -p  绑定端口"
            echo "  -d  启用调试模式"
            exit 1
            ;;
    esac
done

# 构建启动命令
CMD_ARGS="--config $CONFIG_FILE"

if [[ -n "$HOST" ]]; then
    CMD_ARGS="$CMD_ARGS --host $HOST"
fi

if [[ -n "$PORT" ]]; then
    CMD_ARGS="$CMD_ARGS --port $PORT"
fi

if [[ "$DEBUG" = true ]]; then
    CMD_ARGS="$CMD_ARGS --debug"
fi

# 检查端口是否被占用
DEFAULT_PORT=8000
if [[ -n "$PORT" ]]; then
    CHECK_PORT="$PORT"
else
    # 从配置文件中读取端口
    CHECK_PORT=$(grep -A5 "server:" "$CONFIG_FILE" | grep "port:" | awk '{print $2}' || echo "$DEFAULT_PORT")
fi

if command -v lsof >/dev/null 2>&1; then
    if lsof -i:"$CHECK_PORT" >/dev/null 2>&1; then
        log_error "端口 $CHECK_PORT 已被占用"
        log_info "请检查是否已有服务在运行，或修改配置文件中的端口设置"
        exit 1
    fi
fi

# 显示启动信息
log_info "=========================================="
log_info "Android Controller Service"
log_info "=========================================="
log_info "配置文件: $CONFIG_FILE"
log_info "项目目录: $PROJECT_DIR"
log_info "绑定端口: $CHECK_PORT"
log_info "调试模式: $([ "$DEBUG" = true ] && echo "启用" || echo "禁用")"
log_info "=========================================="

# 创建PID文件
PID_FILE="data/android_controller.pid"
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log_error "服务已在运行 (PID: $OLD_PID)"
        log_info "请先运行 ./scripts/stop.sh 停止现有服务"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动服务
log_success "正在启动服务..."

# 使用exec运行，这样脚本的PID就是服务的PID
exec python -m src.main $CMD_ARGS