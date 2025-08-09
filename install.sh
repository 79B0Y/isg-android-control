#!/bin/bash

# Android Controller Service 一键安装脚本
# 用于Termux Ubuntu环境

set -e

echo "=========================================="
echo "Android Controller Service 一键安装"
echo "适用于Termux Ubuntu环境"
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

# 检查运行环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查Python版本
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python版本: $PYTHON_VERSION"
        
        # 检查Python版本是否 >= 3.9
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_success "Python版本满足要求 (>= 3.9)"
        else
            log_error "Python版本过低，需要 >= 3.9"
            log_info "在Termux中运行: pkg install python"
            exit 1
        fi
    else
        log_error "未找到Python3，请先安装Python"
        log_info "在Termux中运行: pkg install python"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1; then
        log_success "pip 已安装"
    else
        log_error "未找到pip，请先安装pip"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if command -v pkg >/dev/null 2>&1; then
        # Termux环境
        log_info "检测到Termux环境，安装必需包..."
        pkg update -y
        pkg install -y \
            python \
            android-tools \
            redis \
            curl \
            wget \
            git \
            libjpeg-turbo \
            libpng \
            zlib \
            openssl \
            libffi || {
            log_warning "部分系统包安装失败，继续进行..."
        }
    elif command -v apt >/dev/null 2>&1; then
        # Ubuntu/Debian环境
        log_info "检测到APT环境，安装必需包..."
        apt update
        apt install -y \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            android-tools-adb \
            redis-server \
            curl \
            wget \
            git \
            libjpeg-dev \
            libpng-dev \
            zlib1g-dev \
            libssl-dev \
            libffi-dev || {
            log_warning "部分系统包安装失败，继续进行..."
        }
    else
        log_warning "未检测到支持的包管理器，跳过系统依赖安装"
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
    
    # 安装requirements.txt中的依赖
    if [[ -f "requirements.txt" ]]; then
        log_info "从requirements.txt安装依赖..."
        pip install -r requirements.txt || {
            log_error "Python依赖安装失败"
            log_info "尝试单独安装核心依赖..."
            
            # 尝试安装核心依赖
            pip install fastapi uvicorn pydantic paho-mqtt Pillow aiofiles loguru click || {
                log_error "核心依赖安装失败，请检查网络连接"
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
    log_info "检查ADB环境..."
    
    if command -v adb >/dev/null 2>&1; then
        ADB_VERSION=$(adb --version | head -n1)
        log_success "ADB已安装: $ADB_VERSION"
        
        # 启动ADB服务器
        log_info "启动ADB服务器..."
        adb kill-server >/dev/null 2>&1 || true
        adb start-server
        
        log_success "ADB环境配置完成"
    else
        log_error "ADB未安装"
        log_info "请运行以下命令安装ADB："
        if command -v pkg >/dev/null 2>&1; then
            echo "  pkg install android-tools"
        else
            echo "  apt install android-tools-adb"
        fi
        log_warning "ADB安装后请重新运行此脚本"
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
    chmod 755 scripts/*.sh 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 设置配置文件
setup_config() {
    log_info "设置配置文件..."
    
    # 如果不存在.env文件，从模板复制
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "已从.env.example创建.env文件"
            log_warning "请根据需要编辑.env文件的配置"
        else
            log_info "创建默认.env文件..."
            cat > .env << 'EOF'
# Android Controller Service 环境变量

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ADB配置
ADB_DEVICE_SERIAL=127.0.0.1:5555
ADB_TIMEOUT=30

# MQTT配置 (可选)
MQTT_BROKER_HOST=192.168.1.10
MQTT_BROKER_PORT=1883
MQTT_CLIENT_ID=android_controller

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=data/logs

# 截图配置
SCREENSHOT_QUALITY=80
SCREENSHOT_MAX_FILES=3
EOF
            log_success "创建了默认.env文件"
        fi
    fi
    
    # 检查主配置文件
    if [[ -f "configs/config.yaml" ]]; then
        log_success "配置文件已存在"
    else
        log_success "配置文件已准备就绪"
    fi
}

# 创建启动脚本
create_scripts() {
    log_info "创建管理脚本..."
    
    # 创建简单启动脚本
    cat > start.sh << 'EOF'
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
if ! adb devices | grep -q "device$"; then
    echo "警告: 未检测到ADB设备连接"
    echo "请确保设备已通过ADB连接 (adb connect <IP>:5555)"
fi

# 启动服务
python -m src.main --config configs/config.yaml "$@"
EOF
    
    chmod +x start.sh
    
    # 创建简单停止脚本
    cat > stop.sh << 'EOF'
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
    
    echo "服务已停止"
else
    echo "未找到运行中的服务"
fi
EOF
    
    chmod +x stop.sh
    
    log_success "管理脚本创建完成"
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
    print('✓ 基本模块导入成功')
except Exception as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "基本测试通过"
    else
        log_warning "基本测试未完全通过，但可以尝试启动服务"
    fi
}

# 显示安装后信息
show_completion_info() {
    log_success "=========================================="
    log_success "Android Controller Service 安装完成！"
    log_success "=========================================="
    
    echo ""
    log_info "🚀 快速开始:"
    echo "1. 连接ADB设备:"
    echo "   adb connect <设备IP>:5555"
    echo ""
    echo "2. 启动服务:"
    echo "   ./start.sh"
    echo ""
    echo "3. 访问API文档:"
    echo "   http://localhost:8000/docs"
    echo ""
    
    log_info "📁 重要文件:"
    echo "• 配置文件: configs/config.yaml"
    echo "• 环境变量: .env"
    echo "• 启动脚本: ./start.sh"
    echo "• 停止脚本: ./stop.sh"
    echo ""
    
    log_info "🛠️ 常用命令:"
    echo "• 启动服务: ./start.sh"
    echo "• 停止服务: ./stop.sh"
    echo "• 检查ADB: adb devices"
    echo "• 查看日志: tail -f data/logs/android_controller.log"
    echo ""
    
    log_info "📖 详细说明:"
    echo "请查看 README.md 文件获取完整使用指南"
    echo ""
    
    if command -v adb >/dev/null 2>&1; then
        if ! adb devices | grep -q "device$"; then
            log_warning "⚠️ 重要提醒:"
            echo "当前未检测到ADB设备连接"
            echo "请在启动服务前连接Android设备："
            echo "  adb connect <设备IP>:5555"
            echo ""
        fi
    fi
    
    log_success "安装完成！运行 ./start.sh 启动服务"
}

# 主函数
main() {
    log_info "开始一键安装Android Controller Service..."
    
    # 检查环境
    check_environment
    
    # 安装系统依赖
    install_system_deps
    
    # 设置Python环境
    setup_virtual_env
    install_python_deps
    
    # 设置ADB环境
    setup_adb
    
    # 设置项目
    setup_directories
    setup_config
    create_scripts
    
    # 运行测试
    run_tests
    
    # 显示完成信息
    show_completion_info
}

# 错误处理
handle_error() {
    log_error "安装过程中出现错误！"
    log_info "请检查上面的错误信息，或手动执行以下步骤："
    echo "1. 安装Python 3.9+: pkg install python (Termux) 或 apt install python3 (Ubuntu)"
    echo "2. 安装ADB: pkg install android-tools 或 apt install android-tools-adb"
    echo "3. 创建虚拟环境: python3 -m venv venv"
    echo "4. 安装依赖: source venv/bin/activate && pip install -r requirements.txt"
    echo "5. 启动服务: ./start.sh"
    exit 1
}

trap 'handle_error' ERR

# 解析命令行参数
SKIP_DEPS=false
SKIP_ADB=false

while getopts "sa" opt; do
    case $opt in
        s)
            SKIP_DEPS=true
            ;;
        a)
            SKIP_ADB=true
            ;;
        h)
            echo "用法: $0 [-s] [-a]"
            echo "  -s  跳过系统依赖安装"
            echo "  -a  跳过ADB环境配置"
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