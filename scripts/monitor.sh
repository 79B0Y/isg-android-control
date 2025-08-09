#!/bin/bash

# Android Controller Service 监控脚本

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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 检查服务状态
check_service_status() {
    local status="stopped"
    local pid=""
    local port=""
    local memory=""
    local cpu=""
    
    # 检查进程
    local pids=$(pgrep -f "src.main" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        status="running"
        pid="$pids"
        
        # 获取资源使用情况
        if command -v ps >/dev/null 2>&1; then
            local ps_output=$(ps -p "$pid" -o pid,pcpu,pmem,etime,command --no-headers 2>/dev/null || true)
            if [[ -n "$ps_output" ]]; then
                cpu=$(echo "$ps_output" | awk '{print $2}')
                memory=$(echo "$ps_output" | awk '{print $3}')
            fi
        fi
        
        # 检查监听端口
        if command -v lsof >/dev/null 2>&1; then
            port=$(lsof -i -P -n | grep "$pid" | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
        fi
    fi
    
    echo "status:$status"
    echo "pid:$pid"
    echo "port:$port"
    echo "cpu:$cpu"
    echo "memory:$memory"
}

# 检查ADB连接
check_adb_status() {
    local adb_status="disconnected"
    local device_count=0
    local devices=""
    
    if command -v adb >/dev/null 2>&1; then
        local adb_output=$(adb devices 2>/dev/null | grep -v "List of devices attached" | grep -v "^$")
        if [[ -n "$adb_output" ]]; then
            device_count=$(echo "$adb_output" | wc -l)
            devices="$adb_output"
            adb_status="connected"
        fi
    fi
    
    echo "adb_status:$adb_status"
    echo "device_count:$device_count"
    echo "devices:$devices"
}

# 检查API健康状态
check_api_health() {
    local api_status="unknown"
    local response_time=""
    local error=""
    
    # 尝试调用健康检查接口
    if command -v curl >/dev/null 2>&1; then
        local start_time=$(date +%s%3N)
        local response=$(curl -s -f -m 5 "http://localhost:8000/health" 2>/dev/null || echo "error")
        local end_time=$(date +%s%3N)
        
        if [[ "$response" != "error" ]]; then
            api_status="healthy"
            response_time=$((end_time - start_time))
        else
            api_status="unhealthy"
            error="API请求失败"
        fi
    fi
    
    echo "api_status:$api_status"
    echo "response_time:$response_time"
    echo "error:$error"
}

# 检查日志文件
check_logs() {
    local log_size=""
    local error_count=""
    local latest_error=""
    
    if [[ -f "data/logs/android_controller.log" ]]; then
        log_size=$(stat -f%z "data/logs/android_controller.log" 2>/dev/null || stat -c%s "data/logs/android_controller.log" 2>/dev/null || echo "unknown")
        
        # 统计最近100行中的错误数量
        if command -v tail >/dev/null 2>&1 && command -v grep >/dev/null 2>&1; then
            error_count=$(tail -100 "data/logs/android_controller.log" | grep -c "ERROR" || echo "0")
            latest_error=$(tail -100 "data/logs/android_controller.log" | grep "ERROR" | tail -1 || echo "")
        fi
    fi
    
    echo "log_size:$log_size"
    echo "error_count:$error_count"
    echo "latest_error:$latest_error"
}

# 显示详细状态
show_detailed_status() {
    echo "=========================================="
    echo "Android Controller Service 状态监控"
    echo "=========================================="
    echo "时间: $(date)"
    echo ""
    
    # 服务状态
    log_info "服务状态:"
    local service_info=$(check_service_status)
    local status=$(echo "$service_info" | grep "status:" | cut -d: -f2)
    local pid=$(echo "$service_info" | grep "pid:" | cut -d: -f2)
    local port=$(echo "$service_info" | grep "port:" | cut -d: -f2)
    local cpu=$(echo "$service_info" | grep "cpu:" | cut -d: -f2)
    local memory=$(echo "$service_info" | grep "memory:" | cut -d: -f2)
    
    if [[ "$status" == "running" ]]; then
        log_success "服务状态: 运行中"
        echo "  进程ID: $pid"
        echo "  监听端口: $port"
        echo "  CPU使用率: ${cpu}%"
        echo "  内存使用率: ${memory}%"
    else
        log_error "服务状态: 已停止"
    fi
    echo ""
    
    # ADB状态
    log_info "ADB连接状态:"
    local adb_info=$(check_adb_status)
    local adb_status=$(echo "$adb_info" | grep "adb_status:" | cut -d: -f2)
    local device_count=$(echo "$adb_info" | grep "device_count:" | cut -d: -f2)
    
    if [[ "$adb_status" == "connected" ]]; then
        log_success "ADB状态: 已连接"
        echo "  设备数量: $device_count"
        echo "$adb_info" | grep "devices:" | cut -d: -f2- | while read -r device; do
            echo "  设备: $device"
        done
    else
        log_error "ADB状态: 未连接"
    fi
    echo ""
    
    # API健康状态
    if [[ "$status" == "running" ]]; then
        log_info "API健康状态:"
        local api_info=$(check_api_health)
        local api_status=$(echo "$api_info" | grep "api_status:" | cut -d: -f2)
        local response_time=$(echo "$api_info" | grep "response_time:" | cut -d: -f2)
        
        if [[ "$api_status" == "healthy" ]]; then
            log_success "API状态: 健康"
            echo "  响应时间: ${response_time}ms"
        else
            log_error "API状态: 异常"
        fi
        echo ""
    fi
    
    # 日志状态
    log_info "日志状态:"
    local log_info=$(check_logs)
    local log_size=$(echo "$log_info" | grep "log_size:" | cut -d: -f2)
    local error_count=$(echo "$log_info" | grep "error_count:" | cut -d: -f2)
    local latest_error=$(echo "$log_info" | grep "latest_error:" | cut -d: -f2-)
    
    if [[ -n "$log_size" && "$log_size" != "unknown" ]]; then
        echo "  日志文件大小: $log_size bytes"
        echo "  最近错误数量: $error_count"
        if [[ -n "$latest_error" && "$latest_error" != "" ]]; then
            echo "  最新错误: $latest_error"
        fi
    else
        log_warning "日志文件不存在"
    fi
    echo ""
    
    # 存储状态
    log_info "存储状态:"
    if [[ -d "data/screenshots" ]]; then
        local screenshot_count=$(ls data/screenshots/*.{jpg,jpeg,png} 2>/dev/null | wc -l)
        echo "  截图文件数量: $screenshot_count"
    fi
    
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' || echo "unknown")
    echo "  磁盘使用率: $disk_usage"
}

# 实时监控模式
watch_mode() {
    local interval=${1:-5}
    
    echo "开始实时监控 (刷新间隔: ${interval}秒, 按Ctrl+C退出)"
    echo ""
    
    while true; do
        clear
        show_detailed_status
        sleep "$interval"
    done
}

# 简单状态检查
simple_status() {
    local service_info=$(check_service_status)
    local status=$(echo "$service_info" | grep "status:" | cut -d: -f2)
    
    if [[ "$status" == "running" ]]; then
        log_success "Android Controller Service 正在运行"
        exit 0
    else
        log_error "Android Controller Service 未运行"
        exit 1
    fi
}

# 主函数
main() {
    case "${1:-status}" in
        "status"|"")
            show_detailed_status
            ;;
        "watch")
            watch_mode "${2:-5}"
            ;;
        "simple")
            simple_status
            ;;
        "check")
            simple_status > /dev/null 2>&1
            ;;
        "logs")
            if [[ -f "data/logs/android_controller.log" ]]; then
                tail -f "data/logs/android_controller.log"
            else
                log_error "日志文件不存在"
                exit 1
            fi
            ;;
        "errors")
            if [[ -f "data/logs/errors.log" ]]; then
                tail -f "data/logs/errors.log"
            else
                log_error "错误日志文件不存在"
                exit 1
            fi
            ;;
        "help")
            echo "用法: $0 [command] [options]"
            echo ""
            echo "命令:"
            echo "  status          显示详细状态 (默认)"
            echo "  watch [间隔]    实时监控模式 (默认间隔5秒)"
            echo "  simple          简单状态检查"
            echo "  check           静默检查 (用于脚本)"
            echo "  logs            查看实时日志"
            echo "  errors          查看错误日志"
            echo "  help            显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                  # 显示详细状态"
            echo "  $0 watch 3          # 3秒间隔实时监控"
            echo "  $0 simple           # 简单状态检查"
            echo "  $0 logs             # 查看实时日志"
            ;;
        *)
            log_error "未知命令: $1"
            echo "运行 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"