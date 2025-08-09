#!/bin/bash

# Android Controller Service - Mac安装脚本
# 适用于macOS Terminal环境

set -e

echo "=========================================="
echo "Android Controller Service - Mac版安装"
echo "适用于macOS Terminal环境"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查macOS环境
check_macos_environment() {
    log_info "检查macOS环境..."
    
    # 检查macOS版本
    MACOS_VERSION=$(sw_vers -productVersion)
    log_info "macOS版本: $MACOS_VERSION"
    
    # 检查架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检查Xcode Command Line Tools
    if xcode-select -p >/dev/null 2>&1; then
        log_success "Xcode Command Line Tools 已安装"
    else
        log_warning "Xcode Command Line Tools 未安装"
        log_info "正在安装Xcode Command Line Tools..."
        xcode-select --install
        log_info "请在弹出的对话框中点击'安装'，然后重新运行此脚本"
        exit 1
    fi
}

# 检查并安装Homebrew
install_homebrew() {
    log_info "检查Homebrew..."
    
    if command -v brew >/dev/null 2>&1; then
        log_success "Homebrew 已安装"
        BREW_VERSION=$(brew --version | head -n1)
        log_info "$BREW_VERSION"
    else
        log_info "Homebrew 未安装，正在安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        if [[ "$ARCH" == "arm64" ]]; then
            # Apple Silicon Mac
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            # Intel Mac
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        log_success "Homebrew 安装完成"
    fi
    
    # 更新Homebrew
    log_info "更新Homebrew..."
    brew update
}

# 检查Python环境
check_python_environment() {
    log_info "检查Python环境..."
    
    # 检查Python 3
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python版本: $PYTHON_VERSION"
        
        # 检查Python版本是否 >= 3.9
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_success "Python版本满足要求 (>= 3.9)"
        else
            log_error "Python版本过低，需要 >= 3.9"
            log_info "正在通过Homebrew安装最新Python..."
            brew install python@3.11
        fi
    else
        log_info "Python3未安装，正在安装..."
        brew install python@3.11
    fi
    
    # 检查pip
    if command -v pip3 >/dev/null 2>&1; then
        log_success "pip3 已安装"
    else
        log_info "安装pip..."
        python3 -m ensurepip --upgrade
    fi
}

# 安装macOS系统依赖
install_macos_deps() {
    log_info "安装macOS系统依赖..."
    
    # 安装必要的包
    local packages=(
        "android-platform-tools"  # ADB工具
        "redis"                    # Redis服务器
        "wget"                     # wget工具
        "curl"                     # curl工具 (通常已安装)
        "git"                      # git (通常已安装)
        "jpeg"                     # JPEG库
        "libpng"                   # PNG库
        "zlib"                     # zlib压缩库
    )
    
    for package in "${packages[@]}"; do
        log_info "安装 $package..."
        brew install "$package" || {
            log_warning "$package 安装失败，继续安装其他包..."
            continue
        }
    done
    
    log_success "系统依赖安装完成"
}

# 启动Redis服务
setup_redis() {
    log_info "配置Redis服务..."
    
    # 启动Redis服务
    if brew services list | grep redis | grep -q started; then
        log_info "Redis服务已在运行"
    else
        log_info "启动Redis服务..."
        brew services start redis
        
        # 等待Redis启动
        sleep 3
        
        if brew services list | grep redis | grep -q started; then
            log_success "Redis服务启动成功"
        else
            log_warning "Redis服务启动失败，手动启动: brew services start redis"
        fi
    fi
}

# 创建虚拟环境
setup_virtual_env() {
    log_info "设置Python虚拟环境..."
    
    VENV_DIR="venv"
    
    if [[ -d "$VENV_DIR" ]]; then
        log_info "虚拟环境已存在，跳过创建"
    else
        log_info "创建虚拟环境: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
        log_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    log_success "虚拟环境已激活"
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖包..."
    
    # 特别处理一些在macOS上可能有问题的包
    log_info "预先安装系统依赖的Python包..."
    
    # 安装Pillow的系统依赖
    export LDFLAGS="-L$(brew --prefix zlib)/lib -L$(brew --prefix jpeg)/lib -L$(brew --prefix libpng)/lib"
    export CPPFLAGS="-I$(brew --prefix zlib)/include -I$(brew --prefix jpeg)/include -I$(brew --prefix libpng)/include"
    export PKG_CONFIG_PATH="$(brew --prefix zlib)/lib/pkgconfig:$(brew --prefix jpeg)/lib/pkgconfig:$(brew --prefix libpng)/lib/pkgconfig"
    
    # 安装requirements.txt中的依赖
    if [[ -f "requirements.txt" ]]; then
        log_info "从requirements.txt安装依赖..."
        pip install -r requirements.txt || {
            log_warning "部分依赖安装失败，尝试安装核心依赖..."
            
            # 尝试安装核心依赖
            pip install fastapi uvicorn pydantic paho-mqtt Pillow aiofiles loguru click psutil || {
                log_error "核心依赖安装失败"
                exit 1
            }
        }
        log_success "Python依赖安装完成"
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
}

# 检查ADB环境
setup_adb() {
    log_info "配置ADB环境..."
    
    if command -v adb >/dev/null 2>&1; then
        ADB_VERSION=$(adb --version | head -n1)
        log_success "ADB已安装: $ADB_VERSION"
        
        # 启动ADB服务器
        log_info "启动ADB服务器..."
        adb kill-server >/dev/null 2>&1 || true
        adb start-server
        
        log_success "ADB环境配置完成"
    else
        log_error "ADB安装失败"
        log_info "请手动安装: brew install android-platform-tools"
        exit 1
    fi
}

# 创建必要目录和文件
setup_directories() {
    log_info "创建必要目录..."
    
    # 创建数据目录
    mkdir -p data/{logs,screenshots}
    mkdir -p configs
    mkdir -p tests/{unit,integration,fixtures}
    
    # 创建.gitkeep文件
    touch data/logs/.gitkeep
    touch data/screenshots/.gitkeep
    
    # 设置权限
    chmod 755 data
    chmod 755 data/logs
    chmod 755 data/screenshots
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 设置配置文件
setup_config() {
    log_info "设置配置文件..."
    
    # 创建.env文件
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "已从.env.example创建.env文件"
        else
            log_info "创建默认.env文件..."
            cat > .env << 'EOF'
# Android Controller Service 环境变量 (macOS)

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ADB配置
ADB_DEVICE_SERIAL=127.0.0.1:5555
ADB_TIMEOUT=30

# MQTT配置 (可选)
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
MQTT_CLIENT_ID=android_controller

# Redis配置 (macOS Homebrew)
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=data/logs

# 截图配置
SCREENSHOT_QUALITY=80
SCREENSHOT_MAX_FILES=3
EOF
            log_success "创建了默认.env文件"
        fi
        
        log_warning "请根据需要编辑.env文件的配置"
    fi
    
    # 检查主配置文件
    if [[ -f "configs/config.yaml" ]]; then
        log_success "配置文件已存在"
    else
        log_success "配置文件已准备就绪"
    fi
}

# 创建命令行工具链接
setup_cli_command() {
    log_info "设置命令行工具..."
    
    # 创建软链接到/usr/local/bin (如果有权限)
    local target_dir="/usr/local/bin"
    local source_script="$(pwd)/isg-android-control"
    local target_link="$target_dir/isg-android-control"
    
    if [[ -d "$target_dir" ]] && [[ -w "$target_dir" ]]; then
        # 删除旧链接
        [[ -L "$target_link" ]] && rm "$target_link"
        
        # 创建新链接
        ln -s "$source_script" "$target_link"
        log_success "命令行工具已安装: isg-android-control"
    else
        log_warning "/usr/local/bin 不可写，跳过命令行工具安装"
        log_info "您可以手动创建链接:"
        echo "  sudo ln -s $(pwd)/isg-android-control /usr/local/bin/"
        echo "或添加到PATH中:"
        echo "  echo 'export PATH=\"$(pwd):\$PATH\"' >> ~/.zshrc"
    fi
}

# 创建macOS专用脚本
create_macos_scripts() {
    log_info "创建macOS管理脚本..."
    
    # 创建Mac版启动脚本
    cat > start-mac.sh << 'EOF'
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
EOF
    
    chmod +x start-mac.sh
    
    # 创建Mac版停止脚本
    cat > stop-mac.sh << 'EOF'
#!/bin/bash
# Android Controller Service - macOS停止脚本

echo "🛑 停止Android Controller Service..."

# 查找并停止进程
PIDS=$(pgrep -f "src.main" 2>/dev/null || true)

if [[ -n "$PIDS" ]]; then
    echo "🔍 发现进程: $PIDS"
    kill -TERM $PIDS
    
    # 等待进程结束
    sleep 3
    
    # 检查是否还在运行
    if pgrep -f "src.main" >/dev/null 2>&1; then
        echo "🔨 强制终止进程..."
        pkill -KILL -f "src.main"
    fi
    
    echo "✅ 服务已停止"
else
    echo "ℹ️  未找到运行中的服务"
fi

# 清理PID文件
rm -f data/android_controller.pid 2>/dev/null || true

echo "🧹 清理完成"
EOF
    
    chmod +x stop-mac.sh
    
    # 创建Mac版连接脚本
    cat > connect-mac.sh << 'EOF'
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
EOF
    
    chmod +x connect-mac.sh
    
    log_success "macOS专用脚本创建完成"
}

# 运行基本测试
run_tests() {
    log_info "运行基本测试..."
    
    # 测试导入
    if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.core.config import get_settings
    from src.models.requests import NavigationDirection
    from src.models.responses import BaseResponse
    print('✅ 基本模块导入成功')
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "基本测试通过"
    else
        log_warning "基本测试未完全通过，但可以尝试启动服务"
    fi
    
    # 测试Redis连接
    log_info "测试Redis连接..."
    if python3 -c "
import redis
try:
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    r.ping()
    print('✅ Redis连接正常')
except Exception as e:
    print(f'⚠️ Redis连接失败: {e}')
" 2>/dev/null; then
        log_success "Redis连接测试通过"
    else
        log_warning "Redis连接测试失败，请检查Redis服务状态"
    fi
}

# 显示安装完成信息
show_completion_info() {
    log_success "=========================================="
    log_success "🎉 macOS安装完成！"
    log_success "=========================================="
    
    echo ""
    echo "🚀 快速开始:"
    echo "1. 连接Android设备或启动模拟器:"
    echo "   ./connect-mac.sh                      # 本地模拟器"
    echo "   ./connect-mac.sh 192.168.1.100:5555  # 真实设备"
    echo ""
    echo "2. 启动服务:"
    echo "   isg-android-control start             # 使用CLI命令"
    echo "   ./start-mac.sh                        # 或使用脚本"
    echo ""
    echo "3. 管理服务:"
    echo "   isg-android-control status            # 查看状态"
    echo "   isg-android-control stop              # 停止服务"
    echo "   isg-android-control restart           # 重启服务"
    echo ""
    echo "4. 访问API文档:"
    echo "   http://localhost:8000/docs"
    echo ""
    
    echo "📁 重要文件:"
    echo "• 配置文件: configs/config.yaml"
    echo "• 环境变量: .env"
    echo "• Mac启动: ./start-mac.sh"
    echo "• Mac停止: ./stop-mac.sh"
    echo "• 设备连接: ./connect-mac.sh"
    echo ""
    
    echo "🛠️ 管理命令:"
    echo "• 启动服务: ./start-mac.sh"
    echo "• 停止服务: ./stop-mac.sh"
    echo "• 连接设备: ./connect-mac.sh [IP:PORT]"
    echo "• 查看日志: tail -f data/logs/android_controller.log"
    echo "• Redis状态: brew services list | grep redis"
    echo ""
    
    echo "📖 获取帮助:"
    echo "• 连接帮助: ./connect-mac.sh --help"
    echo "• 详细文档: cat README.md"
    echo ""
    
    if ! brew services list | grep redis | grep -q started; then
        log_warning "⚠️ 注意: Redis服务未启动"
        echo "启动Redis: brew services start redis"
        echo ""
    fi
    
    if ! adb devices | grep -q "device$"; then
        log_warning "⚠️ 提醒: 当前未连接Android设备"
        echo "连接模拟器: ./connect-mac.sh"
        echo "连接真实设备: ./connect-mac.sh <设备IP>:5555"
        echo ""
    fi
    
    echo "🎮 macOS版Android Controller Service安装完成！"
    echo "运行 ./start-mac.sh 启动服务"
}

# 主函数
main() {
    log_info "开始macOS环境安装..."
    
    # 检查macOS环境
    check_macos_environment
    
    # 安装Homebrew
    install_homebrew
    
    # 检查Python环境
    check_python_environment
    
    # 安装系统依赖
    install_macos_deps
    
    # 设置Redis
    setup_redis
    
    # 设置Python环境
    setup_virtual_env
    install_python_deps
    
    # 设置ADB
    setup_adb
    
    # 设置项目
    setup_directories
    setup_config
    setup_cli_command
    create_macos_scripts
    
    # 运行测试
    run_tests
    
    # 显示完成信息
    show_completion_info
}

# 错误处理
handle_error() {
    log_error "macOS安装过程中出现错误！"
    echo ""
    log_info "常见解决方案:"
    echo "1. 安装Xcode Command Line Tools: xcode-select --install"
    echo "2. 安装Homebrew: 访问 https://brew.sh"
    echo "3. 安装Python: brew install python@3.11"
    echo "4. 安装ADB: brew install android-platform-tools"
    echo "5. 启动Redis: brew services start redis"
    echo ""
    echo "如果问题持续，请查看详细错误信息或寻求帮助"
    exit 1
}

trap 'handle_error' ERR

# 解析命令行参数
SKIP_HOMEBREW=false
SKIP_DEPS=false

while getopts "hd" opt; do
    case $opt in
        h)
            SKIP_HOMEBREW=true
            ;;
        d)
            SKIP_DEPS=true
            ;;
        \?)
            echo "用法: $0 [-h] [-d]"
            echo "  -h  跳过Homebrew安装"
            echo "  -d  跳过系统依赖安装"
            exit 1
            ;;
    esac
done

# 运行主函数
main "$@"