#!/bin/bash

# Android Controller Service 安装脚本
# 用于Termux Ubuntu环境

set -e

echo "=========================================="
echo "Android Controller Service 安装脚本"
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
    
    # 检查是否在Termux环境中
    if [[ -z "$PREFIX" ]] && [[ ! -d "/data/data/com.termux" ]]; then
        log_warning "未检测到Termux环境，请确保在Termux中运行"
    fi
    
    # 检查Ubuntu proot环境
    if command -v proot-distro >/dev/null 2>&1; then
        log_info "检测到proot-distro环境"
    fi
    
    # 检查Python版本
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python版本: $PYTHON_VERSION"
        
        # 检查Python版本是否 >= 3.9
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_success "Python版本满足要求 (>= 3.9)"
        else
            log_error "Python版本过低，需要 >= 3.9"
            exit 1
        fi
    else
        log_error "未找到Python3，请先安装Python"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 >/dev/null 2>&1; then
        log_success "pip3 已安装"
    else
        log_error "未找到pip3，请先安装pip"
        exit 1
    fi
}

# 检查ADB环境
check_adb() {
    log_info "检查ADB环境..."
    
    if command -v adb >/dev/null 2>&1; then
        ADB_VERSION=$(adb --version | head -n1)
        log_success "ADB已安装: $ADB_VERSION"
    else
        log_error "未找到ADB，请先安装Android SDK Platform Tools"
        log_info "在Termux中运行: pkg install android-tools"
        exit 1
    fi
    
    # 检查ADB连接
    log_info "检查ADB连接..."
    if adb devices | grep -q "127.0.0.1:5555"; then
        log_success "ADB设备连接正常"
    else
        log_warning "未检测到ADB设备连接，请确保:"
        log_warning "1. 设备已启用开发者选项和USB调试"
        log_warning "2. 已通过TCP连接到设备 (adb connect 127.0.0.1:5555)"
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    # 更新包管理器
    if command -v apt >/dev/null 2>&1; then
        log_info "更新APT包索引..."
        apt update
        
        log_info "安装系统依赖包..."
        apt install -y \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            libffi-dev \
            libssl-dev \
            libjpeg-dev \
            libpng-dev \
            zlib1g-dev \
            redis-server \
            curl \
            wget \
            git
    elif command -v pkg >/dev/null 2>&1; then
        log_info "更新Termux包索引..."
        pkg update
        
        log_info "安装Termux依赖包..."
        pkg install -y \
            python \
            python-pip \
            clang \
            make \
            libjpeg-turbo \
            libpng \
            zlib \
            openssl \
            libffi \
            redis \
            curl \
            wget \
            git
    else
        log_warning "未检测到支持的包管理器"
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
        pip install -r requirements.txt
        log_success "Python依赖安装完成"
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 验证关键依赖
    log_info "验证关键依赖..."
    python3 -c "import fastapi, uvicorn, paho.mqtt.client, PIL" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        log_success "关键依赖验证通过"
    else
        log_error "关键依赖验证失败"
        exit 1
    fi
}

# 创建必要目录和文件
setup_directories() {
    log_info "创建必要目录..."
    
    # 创建数据目录
    mkdir -p data/{logs,screenshots}
    mkdir -p configs
    
    # 创建日志目录的.gitkeep文件
    touch data/logs/.gitkeep
    touch data/screenshots/.gitkeep
    
    # 设置权限
    chmod 755 data
    chmod 755 data/logs
    chmod 755 data/screenshots
    
    log_success "目录创建完成"
}

# 生成配置文件
setup_config() {
    log_info "设置配置文件..."
    
    # 如果不存在.env文件，从模板复制
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "已从.env.example创建.env文件"
            log_warning "请根据需要编辑.env文件的配置"
        fi
    fi
    
    # 检查配置文件
    if [[ -f "configs/config.yaml" ]]; then
        log_success "配置文件已存在"
    else
        log_warning "配置文件不存在，请确保configs/config.yaml正确配置"
    fi
}

# 设置系统服务（可选）
setup_service() {
    log_info "设置系统服务..."
    
    # 创建启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash
# Android Controller Service 启动脚本

cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main --config configs/config.yaml
EOF
    
    chmod +x start.sh
    log_success "启动脚本创建完成: start.sh"
    
    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash
# Android Controller Service 停止脚本

# 查找并停止Android Controller进程
pkill -f "src.main"

echo "Android Controller Service 已停止"
EOF
    
    chmod +x stop.sh
    log_success "停止脚本创建完成: stop.sh"
}

# 运行测试
run_tests() {
    log_info "运行基本测试..."
    
    # 测试导入
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.core.config import get_settings
    from src.core.adb_controller import get_adb_controller
    print('✓ 基本模块导入成功')
except Exception as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
" || {
        log_error "基本测试失败"
        exit 1
    }
    
    log_success "基本测试通过"
}

# 显示安装后信息
show_post_install_info() {
    log_success "=========================================="
    log_success "Android Controller Service 安装完成！"
    log_success "=========================================="
    
    echo ""
    log_info "下一步操作:"
    echo "1. 编辑配置文件: nano configs/config.yaml"
    echo "2. 配置环境变量: nano .env"
    echo "3. 启动服务: ./start.sh"
    echo "4. 查看API文档: http://localhost:8000/docs"
    echo ""
    
    log_info "常用命令:"
    echo "启动服务: ./start.sh"
    echo "停止服务: ./stop.sh"
    echo "查看日志: tail -f data/logs/android_controller.log"
    echo ""
    
    log_warning "重要提醒:"
    echo "1. 确保ADB设备已正确连接"
    echo "2. 配置MQTT broker地址（如果使用Home Assistant集成）"
    echo "3. 根据网络环境调整IP配置"
}

# 主函数
main() {
    log_info "开始安装Android Controller Service..."
    
    # 检查环境
    check_environment
    check_adb
    
    # 安装依赖
    install_system_deps
    
    # 设置Python环境
    setup_virtual_env
    install_python_deps
    
    # 设置项目
    setup_directories
    setup_config
    setup_service
    
    # 运行测试
    run_tests
    
    # 显示完成信息
    show_post_install_info
    
    log_success "安装完成！"
}

# 错误处理
trap 'log_error "安装过程中出现错误，请检查上面的输出"; exit 1' ERR

# 运行主函数
main "$@"