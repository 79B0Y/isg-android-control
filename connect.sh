#!/bin/bash
# Android设备快速连接脚本

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

# 默认设备地址
DEFAULT_DEVICE="127.0.0.1:5555"
DEVICE_IP="${1:-$DEFAULT_DEVICE}"

log_info "连接Android设备: $DEVICE_IP"

# 检查ADB是否已安装
if ! command -v adb >/dev/null 2>&1; then
    log_error "ADB未安装！"
    echo "在Termux中运行: pkg install android-tools"
    echo "在Ubuntu中运行: apt install android-tools-adb"
    exit 1
fi

# 重启ADB服务器
log_info "重启ADB服务器..."
adb kill-server
sleep 1
adb start-server

# 连接设备
log_info "连接到设备..."
adb connect "$DEVICE_IP"

# 等待连接建立
sleep 3

# 检查连接状态
if adb devices | grep -q "$DEVICE_IP.*device"; then
    log_success "设备连接成功！"
    
    # 获取设备信息
    echo ""
    log_info "设备信息:"
    echo "型号: $(adb -s "$DEVICE_IP" shell getprop ro.product.model 2>/dev/null | tr -d '\r\n')"
    echo "Android版本: $(adb -s "$DEVICE_IP" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r\n')"
    echo "API级别: $(adb -s "$DEVICE_IP" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r\n')"
    
    # 测试基本功能
    echo ""
    log_info "测试设备响应..."
    if adb -s "$DEVICE_IP" shell echo "test" | grep -q "test"; then
        log_success "设备响应正常"
        echo ""
        log_success "设备已准备就绪，可以启动服务: ./start.sh"
    else
        log_error "设备响应异常"
    fi
    
elif adb devices | grep -q "$DEVICE_IP"; then
    log_error "设备连接异常，状态不是'device'"
    echo ""
    echo "当前设备列表:"
    adb devices
    echo ""
    echo "可能的解决方案:"
    echo "1. 在Android设备上允许USB调试"
    echo "2. 检查设备IP地址是否正确"
    echo "3. 确保设备和控制端在同一网络"
else
    log_error "设备连接失败"
    echo ""
    echo "故障排除:"
    echo "1. 检查设备IP地址: $DEVICE_IP"
    echo "2. 确保Android设备已启用开发者选项"
    echo "3. 确保已启用'USB调试'和'网络ADB调试'"
    echo "4. 检查网络连接: ping ${DEVICE_IP%:*}"
    echo "5. 检查端口是否开放: nc -zv ${DEVICE_IP%:*} ${DEVICE_IP#*:}"
    echo ""
    echo "用法: $0 [设备IP:端口]"
    echo "示例: $0 192.168.1.100:5555"
fi

echo ""
echo "当前连接的设备:"
adb devices