#!/bin/bash

# Android Controller Service 一键安装脚本
# 专用于 Termux proot Ubuntu 环境
# 版本: 2.0

set -e

echo "=============================================="
echo "Android Controller Service 一键安装"
echo "专用于 Termux proot Ubuntu 环境"
echo "版本: 2.0"
echo "=============================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 显示进度条
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local width=50
    local percent=$((current * 100 / total))
    local completed=$((current * width / total))
    
    printf "\r${CYAN}[%3d%%]${NC} [" $percent
    for ((i=0; i<completed; i++)); do printf "█"; done
    for ((i=completed; i<width; i++)); do printf "░"; done
    printf "] %s" "$desc"
    
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# 检查proot Ubuntu环境
check_proot_environment() {
    log_step "检查 proot Ubuntu 环境..."
    
    # 检查是否在proot中（更宽松的检测）
    if [[ -f "/proc/version" ]]; then
        log_success "✓ 可以访问 /proc/version"
    else
        log_warning "⚠ 无法访问 /proc/version（某些proot环境正常）"
    fi
    
    # 检查是否在Ubuntu中
    if [[ -f "/etc/os-release" ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            log_success "✓ 检测到Ubuntu环境: $VERSION_ID ($VERSION_CODENAME)"
        else
            log_warning "⚠ 当前环境不是Ubuntu，检测到: $ID"
            log_info "注意: 此脚本专为 Termux proot Ubuntu 环境设计"
            log_info "如果您确认在正确环境中，可以继续安装"
        fi
    else
        log_warning "⚠ 无法读取 /etc/os-release，可能在兼容环境中"
    fi
    
    # 检查proot特征
    if [[ -n "$PROOT_L2S_DIR" ]]; then
        log_success "✓ 检测到proot环境变量 (PROOT_L2S_DIR)"
    elif [[ -n "$PREFIX" ]] && [[ "$PREFIX" =~ termux ]]; then
        log_success "✓ 检测到Termux环境变量 (PREFIX)"
    elif pgrep -f "proot" > /dev/null 2>&1; then
        log_success "✓ 检测到proot进程运行"
    else
        log_warning "⚠ 未检测到明显的proot特征"
        log_info "如果您在Termux proot环境中，这可能是正常的"
    fi
    
    # 检查包管理器和环境
    if command -v apt >/dev/null 2>&1; then
        # 验证这是真正的Ubuntu apt，而不是macOS上的Java工具
        if apt --version 2>&1 | grep -q "Java\|Unable to locate a Java Runtime"; then
            log_error "✗ 检测到macOS上的apt命令（Java工具）"
            log_info "您当前在macOS环境中，不是Termux proot Ubuntu"
            log_info "请使用: ./install-mac.sh 进行macOS安装"
            return 1
        elif apt --version 2>&1 | grep -q "apt.*ubuntu\|apt.*debian"; then
            log_success "✓ 找到Ubuntu/Debian apt包管理器"
        else
            log_warning "⚠ apt命令存在但版本信息异常"
        fi
    elif command -v brew >/dev/null 2>&1; then
        log_error "✗ 检测到brew包管理器（macOS环境）"
        log_info "您当前在macOS环境中，不是Termux proot Ubuntu"
        log_info "请使用: ./install-mac.sh 进行macOS安装"
        return 1
    else
        log_error "✗ 未找到支持的包管理器"
        log_info "此脚本需要Ubuntu/Debian环境中的apt包管理器"
        return 1
    fi
    
    # 检查网络连接
    log_info "检查网络连接..."
    if curl -s --connect-timeout 5 https://pypi.org > /dev/null 2>&1; then
        log_success "网络连接正常"
    else
        log_warning "网络连接可能有问题，安装过程中可能失败"
    fi
    
    return 0
}

# 检查Python环境
check_python_environment() {
    log_step "检查Python环境..."
    
    # 检查Python版本
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python版本: $PYTHON_VERSION"
        
        # 检查Python版本是否 >= 3.9
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
            log_success "Python版本满足要求 (>= 3.9)"
        else
            log_error "Python版本过低，需要 >= 3.9"
            log_info "请运行: apt install python3.11 python3.11-venv python3.11-dev"
            return 1
        fi
    else
        log_error "未找到Python3"
        log_info "请运行: apt install python3 python3-venv python3-dev"
        return 1
    fi
    
    # 检查pip和venv
    local missing_modules=()
    
    if ! python3 -c "import venv" 2>/dev/null; then
        missing_modules+=("python3-venv")
    fi
    
    if ! python3 -c "import pip" 2>/dev/null && ! command -v pip3 >/dev/null 2>&1; then
        missing_modules+=("python3-pip")
    fi
    
    if [[ ${#missing_modules[@]} -gt 0 ]]; then
        log_warning "缺少Python模块: ${missing_modules[*]}"
        log_info "将在系统依赖安装阶段修复"
    else
        log_success "Python环境检查通过"
    fi
    
    return 0
}

# 更新系统并安装依赖
install_system_dependencies() {
    log_step "安装系统依赖..."
    
    # 验证apt命令是否为真正的Debian/Ubuntu apt
    if apt --version 2>&1 | grep -q "Java\|APKTool"; then
        log_error "检测到非Ubuntu的apt命令（可能是Java APKTool）"
        log_info "您似乎在macOS环境中运行此脚本"
        log_info "请使用: ./install-mac.sh 进行macOS安装"
        return 1
    fi
    
    # 检查是否有dpkg（Ubuntu/Debian特有）
    if ! command -v dpkg >/dev/null 2>&1; then
        log_error "未找到dpkg包管理器，这不是Ubuntu/Debian系统"
        log_info "此脚本仅适用于Termux proot Ubuntu环境"
        log_info "对于macOS，请使用: ./install-mac.sh"
        return 1
    fi
    
    local total_steps=4
    local current_step=0
    
    # 更新包列表
    ((current_step+=1))
    show_progress $current_step $total_steps "更新包列表..."
    log_info "更新apt包列表..."
    if apt update > /tmp/apt_update.log 2>&1; then
        log_success "包列表更新完成"
    else
        log_warning "包列表更新有警告，查看 /tmp/apt_update.log"
        # 检查是否是严重错误
        if grep -q "Java\|Unable to locate a Java Runtime" /tmp/apt_update.log; then
            log_error "apt命令指向错误的程序，请使用macOS安装脚本"
            return 1
        fi
    fi
    
    # 安装基础构建工具
    ((current_step+=1))
    show_progress $current_step $total_steps "安装基础构建工具..."
    log_info "安装基础构建工具..."
    
    local build_packages=(
        "build-essential"
        "pkg-config"
        "cmake"
        "git"
        "curl"
        "wget"
        "unzip"
    )
    
    if apt install -y "${build_packages[@]}" > /tmp/build_install.log 2>&1; then
        log_success "基础构建工具安装完成"
    else
        log_error "基础构建工具安装失败，查看 /tmp/build_install.log"
        return 1
    fi
    
    # 安装Python相关包
    ((current_step+=1))
    show_progress $current_step $total_steps "安装Python环境..."
    log_info "安装Python开发环境..."
    
    local python_packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "python3-setuptools"
        "python3-wheel"
    )
    
    if apt install -y "${python_packages[@]}" > /tmp/python_install.log 2>&1; then
        log_success "Python环境安装完成"
    else
        log_error "Python环境安装失败，查看 /tmp/python_install.log"
        return 1
    fi
    
    # 安装项目特定依赖
    ((current_step+=1))
    show_progress $current_step $total_steps "安装项目依赖..."
    log_info "安装项目特定依赖..."
    
    local project_packages=(
        "android-tools-adb"
        "redis-server"
        "libjpeg-dev"
        "libpng-dev"
        "zlib1g-dev"
        "libssl-dev"
        "libffi-dev"
        "libyaml-dev"
        "libxml2-dev"
        "libxslt1-dev"
        "libcurl4-openssl-dev"
        "libmosquitto-dev"
    )
    
    if apt install -y "${project_packages[@]}" > /tmp/project_install.log 2>&1; then
        log_success "项目依赖安装完成"
    else
        log_warning "部分项目依赖安装失败，查看 /tmp/project_install.log"
        log_info "尝试继续安装，可能不会影响核心功能"
    fi
    
    show_progress $total_steps $total_steps "系统依赖安装完成"
    
    return 0
}

# 创建和配置虚拟环境
setup_virtual_environment() {
    log_step "设置Python虚拟环境..."
    
    local venv_dir="venv"
    
    # 删除旧虚拟环境（如果存在）
    if [[ -d "$venv_dir" ]]; then
        log_warning "检测到已存在的虚拟环境，将重新创建..."
        rm -rf "$venv_dir"
    fi
    
    # 创建虚拟环境
    log_info "创建虚拟环境: $venv_dir"
    if python3 -m venv "$venv_dir" --prompt "android-controller"; then
        log_success "虚拟环境创建完成"
    else
        log_error "虚拟环境创建失败"
        return 1
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source "$venv_dir/bin/activate"
    
    # 验证虚拟环境
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_success "虚拟环境已激活: $VIRTUAL_ENV"
    else
        log_error "虚拟环境激活失败"
        return 1
    fi
    
    # 升级pip和基础工具
    log_info "升级pip和基础工具..."
    pip install --upgrade pip setuptools wheel > /tmp/pip_upgrade.log 2>&1
    
    if [[ $? -eq 0 ]]; then
        log_success "pip升级完成"
    else
        log_warning "pip升级有问题，查看 /tmp/pip_upgrade.log"
    fi
    
    return 0
}

# 安装Python依赖
install_python_dependencies() {
    log_step "安装Python依赖包..."
    
    if [[ ! -f "requirements.txt" ]]; then
        log_error "未找到requirements.txt文件"
        return 1
    fi
    
    # 检查虚拟环境
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "虚拟环境未激活"
        return 1
    fi
    
    # 显示依赖列表
    log_info "将安装以下依赖:"
    cat requirements.txt | grep -v '^#' | grep -v '^$' | sed 's/^/  • /'
    echo ""
    
    # 设置编译优化选项
    export CFLAGS="-O2 -g0"
    export CXXFLAGS="-O2 -g0"
    
    # 分步安装依赖（避免大包安装失败）
    local core_deps=(
        "wheel"
        "setuptools"
        "pydantic>=2.5.0"
        "pydantic-settings>=2.0.0"
        "fastapi>=0.104.0"
        "uvicorn[standard]>=0.24.0"
        "click>=8.1.7"
        "loguru>=0.7.2"
        "python-dotenv>=1.0.0"
        "PyYAML>=6.0"
        "aiofiles>=23.2.1"
        "httpx>=0.25.0"
        "python-multipart>=0.0.6"
    )
    
    local optional_deps=(
        "redis>=5.0.0"
        "paho-mqtt>=1.6.1"
        "asyncio-mqtt>=0.13.0"
        "Pillow>=10.0.0"
        "psutil>=5.9.6"
    )
    
    # 安装核心依赖
    log_info "安装核心依赖..."
    for dep in "${core_deps[@]}"; do
        log_debug "安装: $dep"
        if pip install "$dep" > /tmp/pip_install.log 2>&1; then
            echo -n "✓"
        else
            echo -n "✗"
            log_warning "核心依赖 $dep 安装失败"
        fi
    done
    echo ""
    
    # 安装可选依赖
    log_info "安装可选依赖..."
    for dep in "${optional_deps[@]}"; do
        log_debug "安装: $dep"
        if pip install "$dep" > /tmp/pip_install.log 2>&1; then
            echo -n "✓"
        else
            echo -n "✗"
            log_warning "可选依赖 $dep 安装失败，某些功能可能不可用"
        fi
    done
    echo ""
    
    # 尝试从requirements.txt安装剩余依赖
    log_info "安装剩余依赖..."
    if pip install -r requirements.txt > /tmp/pip_full_install.log 2>&1; then
        log_success "所有依赖安装完成"
    else
        log_warning "部分依赖安装失败，查看 /tmp/pip_full_install.log"
        log_info "尝试继续安装，核心功能应该可用"
    fi
    
    # 验证关键模块
    log_info "验证关键模块..."
    local verify_modules=(
        "fastapi"
        "uvicorn"
        "pydantic"
        "pydantic_settings"
        "loguru"
        "click"
        "yaml"
    )
    
    local failed_modules=()
    for module in "${verify_modules[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            log_debug "✓ $module"
        else
            failed_modules+=("$module")
            log_debug "✗ $module"
        fi
    done
    
    if [[ ${#failed_modules[@]} -eq 0 ]]; then
        log_success "关键模块验证通过"
    else
        log_error "以下关键模块验证失败: ${failed_modules[*]}"
        return 1
    fi
    
    return 0
}

# 配置ADB环境
setup_adb_environment() {
    log_step "配置ADB环境..."
    
    if command -v adb >/dev/null 2>&1; then
        ADB_VERSION=$(adb --version | head -n1)
        log_success "ADB已安装: $ADB_VERSION"
        
        # 在proot环境中启动ADB服务器可能有问题，提供指导
        log_info "配置ADB服务器..."
        
        # 尝试启动ADB服务器
        if adb kill-server > /dev/null 2>&1 && adb start-server > /dev/null 2>&1; then
            log_success "ADB服务器启动成功"
        else
            log_warning "ADB服务器启动失败，这在proot环境中是正常的"
            log_info "您需要在启动服务前手动连接ADB设备："
            echo "  1. 在Termux主环境中运行: adb connect <设备IP>:5555"
            echo "  2. 或在设备上启用网络ADB调试"
        fi
        
        # 检查设备连接
        log_info "检查ADB设备连接..."
        local devices=$(adb devices 2>/dev/null | grep -v "List of devices" | grep "device$" || true)
        if [[ -n "$devices" ]]; then
            log_success "检测到已连接的设备:"
            echo "$devices" | sed 's/^/  • /'
        else
            log_warning "当前无设备连接"
            log_info "服务启动后，您可以使用以下命令连接设备:"
            echo "  adb connect <设备IP>:5555"
        fi
    else
        log_error "ADB未安装或不可用"
        log_info "请检查android-tools-adb包是否正确安装"
        return 1
    fi
    
    return 0
}

# 创建配置文件
setup_configuration_files() {
    log_step "设置配置文件..."
    
    # 创建必要目录
    local dirs=(
        "data/logs"
        "data/screenshots"
        "configs"
        "scripts"
        "tests/unit"
        "tests/integration"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_debug "创建目录: $dir"
    done
    
    # 创建.env文件
    if [[ ! -f ".env" ]]; then
        log_info "创建环境变量文件: .env"
        cat > .env << 'EOF'
# Android Controller Service 环境变量
# Termux proot Ubuntu 环境配置

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=1
SERVER_RELOAD=false

# ADB配置
ADB_DEVICE_SERIAL=127.0.0.1:5555
ADB_TIMEOUT=30
ADB_RETRY_ATTEMPTS=3
ADB_RETRY_DELAY=1.0
ADB_CONNECTION_TIMEOUT=10

# MQTT配置 (可选，用于Home Assistant集成)
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=admin
MQTT_CLIENT_ID=android_controller_stable
MQTT_DEVICE_ID=android_controller
MQTT_BASE_TOPIC=homeassistant
MQTT_QOS=0
MQTT_RETAIN=true
MQTT_KEEP_ALIVE=60

# 截图配置
SCREENSHOT_QUALITY=80
SCREENSHOT_FORMAT=JPEG
SCREENSHOT_MAX_FILES=5
SCREENSHOT_STORAGE_PATH=data/screenshots
SCREENSHOT_AUTO_CLEANUP=true

# 监控配置
MONITORING_PERFORMANCE_INTERVAL=30
MONITORING_BATTERY_INTERVAL=60
MONITORING_NETWORK_INTERVAL=30
MONITORING_CACHE_TTL=60

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=structured
LOG_FILE_LEVEL=DEBUG
LOG_CONSOLE_LEVEL=INFO
LOG_MAX_FILE_SIZE=50MB
LOG_BACKUP_COUNT=10
LOG_DIR=data/logs
EOF
        log_success "环境变量文件创建完成"
        log_warning "请根据需要修改 .env 文件中的配置"
    else
        log_info ".env文件已存在，跳过创建"
    fi
    
    # 验证配置文件
    if [[ -f "configs/config.yaml" ]]; then
        log_success "主配置文件已存在"
    else
        log_warning "主配置文件不存在，将使用默认配置"
    fi
    
    # 设置文件权限
    chmod 755 data/logs data/screenshots 2>/dev/null || true
    touch data/logs/.gitkeep data/screenshots/.gitkeep 2>/dev/null || true
    
    return 0
}

# 创建管理脚本
create_management_scripts() {
    log_step "创建管理脚本..."
    
    # 创建启动脚本
    log_info "创建启动脚本: start.sh"
    cat > start.sh << 'EOF'
#!/bin/bash
# Android Controller Service 启动脚本
# 适用于 Termux proot Ubuntu 环境

cd "$(dirname "$0")"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}启动 Android Controller Service...${NC}"

# 检查虚拟环境
if [[ ! -d "venv" ]]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请先运行: ./install-termux-ubuntu.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"
export PYTHONIOENCODING=utf-8

# 检查配置文件
if [[ ! -f "configs/config.yaml" ]]; then
    echo -e "${YELLOW}警告: 未找到主配置文件，将使用默认配置${NC}"
fi

# 检查ADB连接
echo "检查ADB设备连接..."
if adb devices 2>/dev/null | grep -q "device$"; then
    echo -e "${GREEN}✓ 检测到ADB设备连接${NC}"
else
    echo -e "${YELLOW}⚠ 未检测到ADB设备连接${NC}"
    echo "提示: 使用 adb connect <设备IP>:5555 连接设备"
    echo ""
fi

# 启动服务
echo "启动服务..."
echo "访问 http://localhost:8000/docs 查看API文档"
echo "使用 Ctrl+C 停止服务"
echo ""

exec python -m src.main --config configs/config.yaml "$@"
EOF
    
    chmod +x start.sh
    
    # 创建停止脚本
    log_info "创建停止脚本: stop.sh"
    cat > stop.sh << 'EOF'
#!/bin/bash
# Android Controller Service 停止脚本

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}停止 Android Controller Service...${NC}"

# 查找并停止进程
PIDS=$(pgrep -f "src.main" 2>/dev/null || true)

if [[ -n "$PIDS" ]]; then
    echo "发现运行中的服务进程: $PIDS"
    
    # 优雅停止
    echo "发送停止信号..."
    kill -TERM $PIDS 2>/dev/null || true
    
    # 等待进程结束
    for i in {1..10}; do
        if ! pgrep -f "src.main" >/dev/null 2>&1; then
            echo -e "${GREEN}服务已优雅停止${NC}"
            exit 0
        fi
        sleep 1
    done
    
    # 强制停止
    echo "强制终止进程..."
    pkill -KILL -f "src.main" 2>/dev/null || true
    
    # 再次检查
    if ! pgrep -f "src.main" >/dev/null 2>&1; then
        echo -e "${GREEN}服务已强制停止${NC}"
    else
        echo -e "${RED}无法停止服务，请手动检查${NC}"
        exit 1
    fi
else
    echo "未找到运行中的服务"
fi
EOF
    
    chmod +x stop.sh
    
    # 创建状态检查脚本
    log_info "创建状态检查脚本: status.sh"
    cat > status.sh << 'EOF'
#!/bin/bash
# Android Controller Service 状态检查脚本

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Android Controller Service 状态检查${NC}"
echo "========================================"

# 检查进程状态
PIDS=$(pgrep -f "src.main" 2>/dev/null || true)
if [[ -n "$PIDS" ]]; then
    echo -e "${GREEN}✓ 服务正在运行${NC}"
    echo "  进程ID: $PIDS"
    
    # 检查端口
    if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
        echo -e "${GREEN}✓ 端口8000正在监听${NC}"
    else
        echo -e "${YELLOW}⚠ 端口8000未监听${NC}"
    fi
else
    echo -e "${RED}✗ 服务未运行${NC}"
fi

# 检查虚拟环境
if [[ -d "venv" ]]; then
    echo -e "${GREEN}✓ 虚拟环境存在${NC}"
else
    echo -e "${RED}✗ 虚拟环境不存在${NC}"
fi

# 检查配置文件
if [[ -f "configs/config.yaml" ]]; then
    echo -e "${GREEN}✓ 配置文件存在${NC}"
else
    echo -e "${YELLOW}⚠ 主配置文件不存在${NC}"
fi

if [[ -f ".env" ]]; then
    echo -e "${GREEN}✓ 环境变量文件存在${NC}"
else
    echo -e "${YELLOW}⚠ 环境变量文件不存在${NC}"
fi

# 检查ADB
if command -v adb >/dev/null 2>&1; then
    echo -e "${GREEN}✓ ADB已安装${NC}"
    
    # 检查ADB设备
    devices=$(adb devices 2>/dev/null | grep -v "List of devices" | grep "device$" | wc -l)
    if [[ $devices -gt 0 ]]; then
        echo -e "${GREEN}✓ ADB设备已连接 ($devices 台)${NC}"
    else
        echo -e "${YELLOW}⚠ 无ADB设备连接${NC}"
    fi
else
    echo -e "${RED}✗ ADB未安装${NC}"
fi

# 检查日志文件
if [[ -d "data/logs" ]]; then
    log_files=$(find data/logs -name "*.log" 2>/dev/null | wc -l)
    if [[ $log_files -gt 0 ]]; then
        echo -e "${GREEN}✓ 发现 $log_files 个日志文件${NC}"
        echo "  最新日志: $(find data/logs -name "*.log" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
    else
        echo -e "${YELLOW}⚠ 无日志文件${NC}"
    fi
else
    echo -e "${RED}✗ 日志目录不存在${NC}"
fi

echo ""
echo "API文档: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
EOF
    
    chmod +x status.sh
    
    # 创建ADB连接脚本
    log_info "创建ADB连接脚本: connect.sh"
    cat > connect.sh << 'EOF'
#!/bin/bash
# ADB设备连接脚本

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ $# -eq 0 ]]; then
    echo "用法: $0 <设备IP:端口>"
    echo "例如: $0 192.168.1.100:5555"
    echo ""
    echo "当前连接的设备:"
    adb devices
    exit 1
fi

DEVICE="$1"

echo -e "${YELLOW}连接到设备: $DEVICE${NC}"

# 停止ADB服务器
adb kill-server > /dev/null 2>&1

# 启动ADB服务器
if adb start-server > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ADB服务器启动成功${NC}"
else
    echo -e "${RED}✗ ADB服务器启动失败${NC}"
    exit 1
fi

# 连接设备
echo "连接到 $DEVICE..."
if adb connect "$DEVICE"; then
    echo -e "${GREEN}✓ 设备连接成功${NC}"
    
    # 验证连接
    if adb -s "$DEVICE" shell echo "test" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 设备通信正常${NC}"
        
        # 显示设备信息
        echo ""
        echo "设备信息:"
        adb -s "$DEVICE" shell getprop ro.product.model 2>/dev/null | sed 's/^/  型号: /'
        adb -s "$DEVICE" shell getprop ro.build.version.release 2>/dev/null | sed 's/^/  Android版本: /'
        adb -s "$DEVICE" shell wm size 2>/dev/null | grep "Physical size" | sed 's/^/  /' || true
    else
        echo -e "${YELLOW}⚠ 设备连接但通信异常${NC}"
    fi
else
    echo -e "${RED}✗ 设备连接失败${NC}"
    echo "请确保:"
    echo "1. 设备开启了ADB网络调试"
    echo "2. 设备IP地址正确"
    echo "3. 端口号正确（通常是5555）"
    exit 1
fi
EOF
    
    chmod +x connect.sh
    
    log_success "管理脚本创建完成"
    return 0
}

# 设置CLI命令链接
setup_cli_tool() {
    log_step "设置CLI命令工具..."
    
    # 确保isg-android-control文件存在且可执行
    local cli_script="isg-android-control"
    if [[ ! -f "$cli_script" ]]; then
        log_warning "CLI脚本文件不存在: $cli_script"
        return 1
    fi
    
    # 设置可执行权限
    chmod +x "$cli_script"
    
    # 尝试创建系统链接
    local target_dirs=(
        "/usr/local/bin"
        "$HOME/.local/bin"
        "$HOME/bin"
        "/bin"
        "/usr/bin"
    )
    
    local linked=false
    for target_dir in "${target_dirs[@]}"; do
        if [[ -d "$target_dir" ]] && [[ -w "$target_dir" ]]; then
            local target_link="$target_dir/isg-android-control"
            
            # 删除旧链接
            [[ -L "$target_link" ]] && rm "$target_link" 2>/dev/null || true
            
            # 创建新链接
            if ln -sf "$(pwd)/$cli_script" "$target_link" 2>/dev/null; then
                log_success "CLI工具已安装: $target_link"
                linked=true
                break
            fi
        fi
    done
    
    if [[ "$linked" != "true" ]]; then
        log_warning "无法自动安装CLI工具到系统PATH"
        log_info "您可以手动添加到PATH中:"
        echo "  export PATH=\"$(pwd):\$PATH\" >> ~/.bashrc"
        echo "  source ~/.bashrc"
        echo ""
        log_info "或直接使用相对路径:"
        echo "  ./isg-android-control --help"
    fi
    
    return 0
}

# 运行集成测试
run_integration_tests() {
    log_step "运行集成测试..."
    
    # 检查虚拟环境
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "虚拟环境未激活"
        return 1
    fi
    
    # 测试模块导入
    log_info "测试模块导入..."
    local test_modules=(
        "src.core.config"
        "src.models.requests"
        "src.models.responses"
        "src.api.main"
        "src.mqtt.client"
    )
    
    local failed_imports=()
    for module in "${test_modules[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            log_debug "✓ $module"
        else
            failed_imports+=("$module")
            log_debug "✗ $module"
        fi
    done
    
    if [[ ${#failed_imports[@]} -eq 0 ]]; then
        log_success "模块导入测试通过"
    else
        log_error "模块导入测试失败: ${failed_imports[*]}"
        return 1
    fi
    
    # 测试配置加载
    log_info "测试配置加载..."
    if python -c "
import sys
sys.path.insert(0, '.')
from src.core.config import get_settings
try:
    settings = get_settings()
    print(f'配置加载成功: {settings.server.host}:{settings.server.port}')
except Exception as e:
    print(f'配置加载失败: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "配置加载测试通过"
    else
        log_error "配置加载测试失败"
        return 1
    fi
    
    # 测试MQTT客户端创建（不连接）
    log_info "测试MQTT客户端..."
    if python -c "
import sys
sys.path.insert(0, '.')
from src.mqtt.client import MQTTClient
try:
    client = MQTTClient()
    print('MQTT客户端创建成功')
except Exception as e:
    print(f'MQTT客户端创建失败: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "MQTT客户端测试通过"
    else
        log_warning "MQTT客户端测试失败，但不影响基本功能"
    fi
    
    log_success "集成测试完成"
    return 0
}

# 显示安装完成信息
show_installation_summary() {
    log_success "=============================================="
    log_success "Android Controller Service 安装完成！"
    log_success "=============================================="
    
    echo ""
    echo -e "${CYAN}🚀 快速开始:${NC}"
    echo ""
    echo "1. 连接ADB设备:"
    echo "   ./connect.sh <设备IP>:5555"
    echo "   # 例如: ./connect.sh 192.168.1.100:5555"
    echo ""
    echo "2. 启动服务:"
    echo "   ./start.sh"
    echo ""
    echo "3. 访问API文档:"
    echo "   http://localhost:8000/docs"
    echo ""
    echo "4. 检查状态:"
    echo "   isg-android-control status"
    echo "   # 或使用脚本: ./status.sh"
    echo ""
    echo "5. 查看日志:"
    echo "   isg-android-control logs"
    echo "   isg-android-control logs -f   # 实时跟踪"
    echo ""
    echo "6. 停止服务:"
    echo "   isg-android-control stop"
    echo "   # 或使用脚本: ./stop.sh"
    echo ""
    
    echo -e "${CYAN}📁 重要文件:${NC}"
    echo "• 主配置: configs/config.yaml"
    echo "• 环境变量: .env"
    echo "• 日志目录: data/logs/"
    echo "• 截图目录: data/screenshots/"
    echo ""
    
    echo -e "${CYAN}🛠️ CLI命令:${NC}"
    echo "• 启动服务: isg-android-control start"
    echo "• 前台运行: isg-android-control start -f"
    echo "• 停止服务: isg-android-control stop"
    echo "• 检查状态: isg-android-control status"
    echo "• 查看日志: isg-android-control logs"
    echo "• 重启服务: isg-android-control restart"
    echo ""
    echo -e "${CYAN}🛠️ 管理脚本:${NC}"
    echo "• 启动服务: ./start.sh"
    echo "• 停止服务: ./stop.sh"
    echo "• 检查状态: ./status.sh"
    echo "• 连接设备: ./connect.sh <IP>:5555"
    echo ""
    
    echo -e "${CYAN}🏠 Home Assistant 集成:${NC}"
    echo "1. 修改 .env 文件中的MQTT配置"
    echo "2. 启动服务后，实体将自动添加到Home Assistant"
    echo "3. 支持的功能: 截图、导航控制、音量调节、屏幕控制等"
    echo ""
    
    echo -e "${CYAN}📖 故障排除:${NC}"
    echo "• 查看日志: tail -f data/logs/*.log"
    echo "• 检查ADB: adb devices"
    echo "• 测试连接: curl http://localhost:8000/health"
    echo "• 重新安装: rm -rf venv && ./install-termux-ubuntu.sh"
    echo ""
    
    # 环境检查提醒
    if ! adb devices 2>/dev/null | grep -q "device$"; then
        echo -e "${YELLOW}⚠️ 重要提醒:${NC}"
        echo "当前未检测到ADB设备连接"
        echo "请在启动服务前连接Android设备："
        echo "  ./connect.sh <设备IP>:5555"
        echo ""
    fi
    
    # 配置提醒
    echo -e "${YELLOW}📝 配置提醒:${NC}"
    echo "• 请根据您的环境修改 .env 文件"
    echo "• 如需使用Home Assistant，请配置MQTT相关参数"
    echo "• ADB设备IP请设置为实际的设备地址"
    echo ""
    
    log_success "安装完成！运行 ./start.sh 启动服务"
    echo ""
}

# 错误处理
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    echo ""
    log_error "安装过程在第 $line_number 行出现错误 (退出码: $exit_code)"
    log_error "安装失败！"
    
    echo ""
    echo -e "${YELLOW}常见问题解决方案:${NC}"
    echo ""
    echo "1. 网络问题:"
    echo "   - 检查网络连接: ping google.com"
    echo "   - 更换pip镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple"
    echo ""
    echo "2. 依赖问题:"
    echo "   - 更新包列表: apt update"
    echo "   - 手动安装Python: apt install python3 python3-venv python3-dev"
    echo ""
    echo "3. 权限问题:"
    echo "   - 确保在proot Ubuntu环境中运行"
    echo "   - 检查写入权限: touch test_file && rm test_file"
    echo ""
    echo "4. 环境问题:"
    echo "   - 验证环境: cat /etc/os-release"
    echo "   - 重新进入proot: proot-distro login ubuntu"
    echo ""
    echo "如问题持续，请查看 /tmp/ 目录下的日志文件："
    echo "  • /tmp/apt_update.log"
    echo "  • /tmp/pip_install.log"
    echo "  • /tmp/python_install.log"
    echo ""
    
    exit $exit_code
}

# 主安装流程
main_installation() {
    local start_time=$(date +%s)
    
    log_info "开始安装 Android Controller Service (Termux proot Ubuntu版)"
    echo ""
    
    # 安装步骤
    local steps=(
        "check_proot_environment"
        "check_python_environment" 
        "install_system_dependencies"
        "setup_virtual_environment"
        "install_python_dependencies"
        "setup_adb_environment"
        "setup_configuration_files"
        "create_management_scripts"
        "setup_cli_tool"
        "run_integration_tests"
    )
    
    local total_steps=${#steps[@]}
    local current_step=0
    
    for step in "${steps[@]}"; do
        ((current_step+=1))
        echo -e "${PURPLE}[步骤 $current_step/$total_steps]${NC} 执行: $step"
        
        if ! $step; then
            log_error "步骤 $step 执行失败"
            return 1
        fi
        
        echo ""
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    show_installation_summary
    
    log_success "总安装时间: ${duration}秒"
    
    return 0
}

# 解析命令行参数
SKIP_DEPS=false
DEBUG=false
FORCE_REINSTALL=false

while getopts "sdfh" opt; do
    case $opt in
        s)
            SKIP_DEPS=true
            log_info "跳过系统依赖安装"
            ;;
        d)
            DEBUG=true
            log_info "启用调试模式"
            ;;
        f)
            FORCE_REINSTALL=true
            log_info "强制重新安装"
            ;;
        h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -s    跳过系统依赖安装"
            echo "  -d    启用调试模式"
            echo "  -f    强制重新安装（删除现有虚拟环境）"
            echo "  -h    显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0        # 标准安装"
            echo "  $0 -d     # 调试模式安装"
            echo "  $0 -s     # 跳过系统依赖"
            echo "  $0 -f     # 强制重新安装"
            exit 0
            ;;
        \?)
            log_error "无效选项: -$OPTARG"
            echo "使用 -h 查看帮助"
            exit 1
            ;;
    esac
done

# 设置错误处理
set -eE
trap 'handle_error ${LINENO}' ERR

# 开始安装
log_info "Android Controller Service 一键安装脚本"
log_info "适用环境: Termux proot Ubuntu"
log_info "脚本版本: 2.0"
echo ""

if [[ "$FORCE_REINSTALL" == "true" ]] && [[ -d "venv" ]]; then
    log_warning "强制重新安装，删除现有虚拟环境..."
    rm -rf venv
fi

# 运行主安装流程
main_installation

log_success "安装脚本执行完成！"