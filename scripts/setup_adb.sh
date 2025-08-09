#!/bin/bash

# ADB环境配置脚本
# 用于Termux Ubuntu环境中的Android设备控制

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查并安装ADB
install_adb() {
    log_info "检查ADB安装状态..."
    
    if command -v adb >/dev/null 2>&1; then
        log_success "ADB已安装"
        adb --version
    else
        log_info "ADB未安装，正在安装..."
        
        if command -v pkg >/dev/null 2>&1; then
            # Termux环境
            pkg update
            pkg install -y android-tools
        elif command -v apt >/dev/null 2>&1; then
            # Ubuntu环境
            apt update
            apt install -y android-tools-adb android-tools-fastboot
        else
            log_error "未检测到支持的包管理器"
            exit 1
        fi
        
        log_success "ADB安装完成"
    fi
}

# 配置ADB服务器
setup_adb_server() {
    log_info "配置ADB服务器..."
    
    # 停止现有ADB服务器
    log_info "停止现有ADB服务器..."
    adb kill-server
    
    # 启动ADB服务器
    log_info "启动ADB服务器..."
    adb start-server
    
    # 等待服务器启动
    sleep 2
    
    log_success "ADB服务器启动完成"
}

# 检查设备连接
check_device_connection() {
    log_info "检查设备连接状态..."
    
    # 列出连接的设备
    DEVICES=$(adb devices | grep -v "List of devices attached" | grep -v "^$")
    
    if [[ -z "$DEVICES" ]]; then
        log_warning "未检测到连接的设备"
        return 1
    else
        log_success "检测到以下设备:"
        echo "$DEVICES"
        return 0
    fi
}

# 连接TCP设备
connect_tcp_device() {
    local device_ip="${1:-127.0.0.1:5555}"
    
    log_info "尝试连接TCP设备: $device_ip"
    
    # 连接设备
    adb connect "$device_ip"
    
    # 等待连接建立
    sleep 3
    
    # 检查连接状态
    if adb devices | grep -q "$device_ip"; then
        log_success "TCP设备连接成功: $device_ip"
        return 0
    else
        log_error "TCP设备连接失败: $device_ip"
        return 1
    fi
}

# 测试设备功能
test_device_functions() {
    log_info "测试设备基本功能..."
    
    # 检查设备是否响应
    log_info "测试设备响应..."
    if adb shell echo "test" | grep -q "test"; then
        log_success "设备响应正常"
    else
        log_error "设备响应异常"
        return 1
    fi
    
    # 获取设备信息
    log_info "获取设备信息..."
    MODEL=$(adb shell getprop ro.product.model 2>/dev/null | tr -d '\r\n')
    ANDROID_VERSION=$(adb shell getprop ro.build.version.release 2>/dev/null | tr -d '\r\n')
    API_LEVEL=$(adb shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r\n')
    
    if [[ -n "$MODEL" ]]; then
        log_success "设备型号: $MODEL"
        log_info "Android版本: $ANDROID_VERSION"
        log_info "API级别: $API_LEVEL"
    else
        log_error "无法获取设备信息"
        return 1
    fi
    
    # 测试基本命令
    log_info "测试基本ADB命令..."
    
    # 测试输入命令
    if adb shell input keyevent KEYCODE_MENU >/dev/null 2>&1; then
        log_success "输入命令测试通过"
    else
        log_warning "输入命令测试失败，可能需要root权限"
    fi
    
    # 测试截图命令
    log_info "测试截图功能..."
    if adb shell screencap -p | head -c 10 | grep -q PNG; then
        log_success "截图功能测试通过"
    else
        log_warning "截图功能测试失败"
    fi
    
    return 0
}

# 配置设备权限
setup_device_permissions() {
    log_info "配置设备权限..."
    
    # 检查root权限
    log_info "检查root权限..."
    if adb shell su -c "echo 'root test'" 2>/dev/null | grep -q "root test"; then
        log_success "设备具有root权限"
        
        # 设置一些有用的权限
        log_info "配置系统权限..."
        adb shell su -c "setenforce 0" 2>/dev/null || log_warning "无法设置SELinux为宽松模式"
        
    else
        log_warning "设备没有root权限，部分功能可能受限"
        log_info "建议启用开发者选项中的以下设置:"
        echo "  - USB调试"
        echo "  - USB调试(安全设置)"
        echo "  - 撤销USB调试授权"
    fi
}

# 优化ADB连接
optimize_adb_connection() {
    log_info "优化ADB连接..."
    
    # 设置TCP连接保持活动
    if command -v sysctl >/dev/null 2>&1; then
        sysctl -w net.ipv4.tcp_keepalive_time=300 2>/dev/null || true
        sysctl -w net.ipv4.tcp_keepalive_probes=3 2>/dev/null || true
        sysctl -w net.ipv4.tcp_keepalive_intvl=30 2>/dev/null || true
    fi
    
    # 设置ADB环境变量
    export ADB_TCP_TIMEOUT=30
    export ADB_LOCAL_TRANSPORT_MAX_PORT=5037
    
    log_success "ADB连接优化完成"
}

# 创建ADB配置文件
create_adb_config() {
    log_info "创建ADB配置文件..."
    
    # 创建ADB配置目录
    mkdir -p "$HOME/.android"
    
    # 创建ADB密钥（如果不存在）
    if [[ ! -f "$HOME/.android/adbkey" ]]; then
        log_info "生成ADB密钥..."
        adb keygen "$HOME/.android/adbkey"
        log_success "ADB密钥生成完成"
    else
        log_info "ADB密钥已存在"
    fi
    
    # 创建设备配置脚本
    cat > adb_connect.sh << 'EOF'
#!/bin/bash
# ADB设备连接脚本

DEVICE_IP="${1:-127.0.0.1:5555}"

echo "连接到设备: $DEVICE_IP"

# 重启ADB服务器
adb kill-server
adb start-server

# 连接设备
adb connect "$DEVICE_IP"

# 等待连接
sleep 3

# 检查连接状态
if adb devices | grep -q "$DEVICE_IP"; then
    echo "✓ 设备连接成功"
    
    # 获取设备信息
    echo "设备型号: $(adb shell getprop ro.product.model)"
    echo "Android版本: $(adb shell getprop ro.build.version.release)"
    
    # 测试基本功能
    if adb shell echo "test" | grep -q "test"; then
        echo "✓ 设备响应正常"
    else
        echo "✗ 设备响应异常"
    fi
else
    echo "✗ 设备连接失败"
    exit 1
fi
EOF
    
    chmod +x adb_connect.sh
    log_success "设备连接脚本创建完成: adb_connect.sh"
}

# 主函数
main() {
    log_info "=========================================="
    log_info "ADB环境配置脚本"
    log_info "=========================================="
    
    # 安装ADB
    install_adb
    
    # 配置ADB服务器
    setup_adb_server
    
    # 优化连接
    optimize_adb_connection
    
    # 创建配置文件
    create_adb_config
    
    # 尝试连接设备
    if ! check_device_connection; then
        log_info "尝试连接本地TCP设备..."
        if connect_tcp_device "127.0.0.1:5555"; then
            log_success "本地TCP设备连接成功"
        else
            log_warning "本地TCP设备连接失败"
            log_info "请手动连接设备："
            echo "1. 在Android设备上启用开发者选项和USB调试"
            echo "2. 在Android设备上启用网络ADB调试"
            echo "3. 运行: adb connect <设备IP>:5555"
            echo "4. 运行: ./adb_connect.sh [设备IP:端口]"
        fi
    fi
    
    # 如果有设备连接，测试功能
    if check_device_connection; then
        test_device_functions
        setup_device_permissions
    fi
    
    log_success "=========================================="
    log_success "ADB环境配置完成！"
    log_success "=========================================="
    
    log_info "使用说明："
    echo "1. 连接设备: ./adb_connect.sh [IP:PORT]"
    echo "2. 查看设备: adb devices"
    echo "3. 测试连接: adb shell echo 'test'"
    echo "4. 获取设备信息: adb shell getprop"
    echo ""
    
    log_info "故障排除："
    echo "1. 连接失败时重启ADB: adb kill-server && adb start-server"
    echo "2. 检查设备IP和端口是否正确"
    echo "3. 确保设备和控制端在同一网络"
    echo "4. 检查防火墙设置"
}

# 错误处理
trap 'log_error "ADB配置过程中出现错误"; exit 1' ERR

# 解析命令行参数
DEVICE_IP=""
while getopts "d:h" opt; do
    case $opt in
        d)
            DEVICE_IP="$OPTARG"
            ;;
        h)
            echo "用法: $0 [-d DEVICE_IP:PORT]"
            echo "  -d  指定设备IP和端口 (默认: 127.0.0.1:5555)"
            echo "  -h  显示帮助信息"
            exit 0
            ;;
        \?)
            log_error "无效选项: -$OPTARG"
            exit 1
            ;;
    esac
done

# 运行主函数
main "$@"