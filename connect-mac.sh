#!/bin/bash
# Android设备快速连接脚本 - macOS版

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "📱 Android设备连接助手 (macOS版)"

# 默认设备地址
DEFAULT_DEVICE="127.0.0.1:5555"
DEVICE_IP="${1:-$DEFAULT_DEVICE}"

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo ""
    echo "用法: $0 [设备IP:端口]"
    echo ""
    echo "示例:"
    echo "  $0                          # 连接本地模拟器 (127.0.0.1:5555)"
    echo "  $0 192.168.1.100:5555      # 连接真实设备"
    echo ""
    echo "设备准备步骤:"
    echo "1. Android设备开启开发者选项"
    echo "2. 启用'USB调试'和'网络ADB调试'"
    echo "3. 连接到同一WiFi网络"
    echo "4. 运行此脚本连接"
    echo ""
    echo "模拟器选项:"
    echo "• Android Studio AVD Manager"
    echo "• Genymotion"
    echo "• BlueStacks (需要启用ADB)"
    exit 0
fi

log_info "连接目标: $DEVICE_IP"

# 检查ADB是否已安装
if ! command -v adb >/dev/null 2>&1; then
    log_error "ADB未安装！"
    echo ""
    echo "安装方法:"
    echo "  brew install android-platform-tools"
    echo ""
    exit 1
fi

# 重启ADB服务器
log_info "重启ADB服务器..."
adb kill-server
sleep 1
adb start-server

# 连接设备
log_info "连接设备..."
if [[ "$DEVICE_IP" == "127.0.0.1:5555" || "$DEVICE_IP" == "localhost:5555" ]]; then
    log_info "检测模拟器连接..."
    # 对于本地模拟器，直接检查连接
    sleep 2
else
    # 对于真实设备，执行连接命令
    adb connect "$DEVICE_IP"
    sleep 3
fi

# 检查连接状态
if adb devices | grep -E "(127\.0\.0\.1:5555|$DEVICE_IP)" | grep -q "device"; then
    log_success "设备连接成功！"
    
    # 获取设备信息
    echo ""
    log_info "设备信息:"
    SERIAL=$(adb devices | grep -E "(127\.0\.0\.1:5555|$DEVICE_IP)" | awk '{print $1}')
    MODEL=$(adb -s "$SERIAL" shell getprop ro.product.model 2>/dev/null | tr -d '\r\n')
    ANDROID_VERSION=$(adb -s "$SERIAL" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r\n')
    API_LEVEL=$(adb -s "$SERIAL" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r\n')
    
    echo "📱 设备序列号: $SERIAL"
    echo "📱 设备型号: ${MODEL:-未知}"
    echo "🤖 Android版本: ${ANDROID_VERSION:-未知}"
    echo "🔢 API级别: ${API_LEVEL:-未知}"
    
    # 测试基本功能
    echo ""
    log_info "测试设备响应..."
    if adb -s "$SERIAL" shell echo "test" 2>/dev/null | grep -q "test"; then
        log_success "设备响应正常"
        echo ""
        echo "🎉 设备已准备就绪！"
        echo "现在可以启动服务: ./start-mac.sh"
    else
        log_error "设备响应异常"
    fi
    
else
    log_error "设备连接失败"
    echo ""
    echo "故障排除:"
    echo ""
    echo "📱 真实设备:"
    echo "  1. 确保Android设备开启开发者选项"
    echo "  2. 启用'USB调试'和'网络ADB调试'"
    echo "  3. 设备和Mac在同一WiFi网络"
    echo "  4. 检查设备IP: 设置 → 关于手机 → 状态信息"
    echo "  5. 测试网络: ping ${DEVICE_IP%:*}"
    echo ""
    echo "🖥️ 模拟器:"
    echo "  1. 启动Android Studio AVD Manager"
    echo "  2. 创建并启动Android虚拟设备"
    echo "  3. 确保模拟器ADB端口为5555"
    echo "  4. 重新运行: $0"
    echo ""
    echo "🔧 通用方法:"
    echo "  • 重启ADB: adb kill-server && adb start-server"
    echo "  • 检查端口: lsof -i :5555"
    echo "  • 手动连接: adb connect $DEVICE_IP"
fi

echo ""
echo "当前已连接的设备:"
adb devices
