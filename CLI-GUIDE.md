# iSG Android Controller - CLI 命令指南

统一的命令行接口，取代传统脚本管理方式。

## 🎯 核心优势

- **统一接口**: 跨平台统一命令，无需记忆不同脚本
- **智能管理**: 自动进程检测、PID管理、状态监控
- **详细反馈**: 丰富的状态信息和错误诊断
- **安全卸载**: 完整的服务清理和数据保护

## 📋 命令概览

```bash
isg-android-control <command> [options]

Commands:
  start        启动服务
  stop         停止服务
  status       查看状态
  restart      重启服务
  uninstall    卸载服务
```

## 🚀 命令详解

### start - 启动服务

```bash
# 后台启动服务（默认）
isg-android-control start

# 前台启动服务（用于调试）
isg-android-control start -f
isg-android-control start --foreground
```

**启动流程**:
1. ✅ 检查服务是否已运行
2. 🔍 验证运行环境（Python、ADB、配置文件）
3. ⚠️ 检查ADB设备连接状态
4. 🚀 启动服务进程并记录PID
5. 📋 显示访问信息和状态命令

**输出示例**:
```
🚀 启动iSG Android Controller Service...
[INFO] 以后台模式启动服务...
[SUCCESS] 服务启动成功 (PID: 12345)
📡 API文档: http://localhost:8000/docs
📋 服务状态: isg-android-control status
📝 日志文件: /path/to/logs/service.log
```

### stop - 停止服务

```bash
# 停止服务
isg-android-control stop
```

**停止流程**:
1. 🔍 查找运行中的服务进程
2. 🛑 发送TERM信号优雅停止
3. ⏰ 等待进程结束（最多10秒）
4. 🔨 必要时强制终止（KILL信号）
5. 🧹 清理PID文件

**输出示例**:
```
🛑 停止iSG Android Controller Service...
[INFO] 正在停止服务 (PID: 12345)
[SUCCESS] 服务已停止
```

### status - 查看状态

```bash
# 基本状态信息
isg-android-control status

# 详细状态信息
isg-android-control status -d
isg-android-control status --detailed
```

**状态信息**:

**基本模式**:
```
📊 iSG Android Controller Service 状态
==================================================
[STATUS] 状态: 运行中
进程ID: 12345
运行时间: 2h 15m
内存使用: 45.2MB
CPU使用: 1.2%
[STATUS] API状态: 健康
API文档: http://localhost:8000/docs
```

**详细模式额外显示**:
- 📂 环境检查结果
- 📱 ADB设备连接状态  
- 📝 日志文件信息
- 🔧 配置文件状态

**退出码**:
- `0`: 服务正常运行
- `3`: 服务未运行
- `1`: 检查过程出错

### restart - 重启服务

```bash
# 重启服务
isg-android-control restart
```

**重启流程**:
1. 🛑 停止当前运行的服务
2. ⏰ 等待1秒钟
3. 🚀 启动新的服务实例

等效于：
```bash
isg-android-control stop
sleep 1
isg-android-control start
```

### uninstall - 卸载服务

```bash
# 交互式卸载
isg-android-control uninstall

# 强制卸载（跳过确认）
isg-android-control uninstall -f
isg-android-control uninstall --force
```

**卸载选项**:
- 🛑 自动停止运行中的服务
- 🗑️ 删除Python虚拟环境
- 📂 可选保留/删除数据目录
- ⚙️ 可选保留/删除配置文件
- 🧹 清理macOS专用脚本
- 💡 提供系统清理建议

**交互示例**:
```
🗑️ 卸载iSG Android Controller Service...
确定要卸载 iSG Android Controller Service 吗? [y/N]: y
是否保留数据目录（日志、截图）? [Y/n]: y
是否保留配置文件? [Y/n]: n

[INFO] 正在停止运行中的服务...
[SUCCESS] 删除Python虚拟环境: /path/to/venv
[SUCCESS] 删除配置目录: /path/to/configs
[SUCCESS] 删除环境配置: /path/to/.env

✅ 卸载完成!
```

## 🔧 高级用法

### 环境诊断

```bash
# 详细状态检查运行环境
isg-android-control status -d

# 检查内容包括：
# - Python虚拟环境
# - 配置文件存在性  
# - ADB工具可用性
# - Python依赖包
# - ADB设备连接
# - 日志文件状态
```

### 进程管理

CLI命令使用智能进程检测：

1. **PID文件方式**: 读取 `data/android_controller.pid`
2. **进程搜索方式**: 搜索包含 `src.main` 的进程
3. **验证方式**: 确认进程命令行包含项目路径

### 错误诊断

**常见问题自动检测**:
- ❌ 虚拟环境不存在 → 提示运行安装脚本
- ❌ 配置文件缺失 → 检查配置目录
- ❌ ADB工具缺失 → 提示安装方法
- ❌ Python依赖缺失 → 提示重装依赖
- ⚠️ ADB设备未连接 → 显示连接命令

## 🆚 对比传统脚本

| 功能 | 传统脚本 | CLI命令 |
|------|----------|---------|
| 跨平台 | 需要不同脚本 | 统一命令 |
| 进程检测 | 基础grep | 智能PID+进程搜索 |
| 状态信息 | 基本信息 | 详细诊断 |
| 错误处理 | 简单提示 | 智能建议 |
| 卸载功能 | 无 | 完整清理 |
| 环境检查 | 无 | 自动诊断 |

## 🔄 迁移指南

### 从传统脚本迁移

**旧方式**:
```bash
./start-mac.sh
./stop-mac.sh
./scripts/monitor.sh
```

**新方式**:
```bash
isg-android-control start
isg-android-control stop
isg-android-control status
```

### 保留的脚本

以下脚本仍然保留，用于特殊用途：
- `./connect.sh` / `./connect-mac.sh` - 设备连接
- `./install.sh` / `./install-mac.sh` - 系统安装
- `./scripts/monitor.sh` - 高级监控
- `./scripts/check_deps.py` - 依赖检查

## 📚 完整示例

### 典型使用流程

```bash
# 1. 安装后首次使用
./install-mac.sh                     # macOS安装
./connect-mac.sh 192.168.1.100:5555  # 连接设备
isg-android-control start            # 启动服务

# 2. 日常管理
isg-android-control status           # 检查状态
isg-android-control restart          # 重启服务
isg-android-control stop             # 停止服务

# 3. 问题诊断
isg-android-control status -d        # 详细诊断
tail -f data/logs/android_controller.log  # 查看日志

# 4. 完全卸载
isg-android-control uninstall        # 交互式卸载
```

### 自动化脚本示例

```bash
#!/bin/bash
# 自动启动脚本

echo "检查服务状态..."
if ! isg-android-control status > /dev/null; then
    echo "启动服务..."
    isg-android-control start
    
    # 等待启动
    sleep 5
    
    if isg-android-control status > /dev/null; then
        echo "✅ 服务启动成功"
    else
        echo "❌ 服务启动失败"
        exit 1
    fi
else
    echo "✅ 服务已运行"
fi
```

## 🛠️ 开发者信息

### 技术实现

- **语言**: Python 3.9+
- **依赖**: psutil (进程管理)
- **架构**: 单文件CLI工具
- **配置**: 自动检测项目结构

### 文件位置

- **CLI脚本**: `./isg-android-control`
- **PID文件**: `./data/android_controller.pid`
- **日志文件**: `./data/logs/service.log`
- **配置文件**: `./configs/config.yaml`

---

## 💡 最佳实践

1. **优先使用CLI命令** 替代传统脚本
2. **定期检查状态** `isg-android-control status -d`
3. **使用详细模式** 进行问题诊断
4. **保留数据目录** 卸载时选择保留日志
5. **结合脚本** 复杂操作仍可使用专用脚本

通过统一的CLI命令，Android Controller Service 的管理变得更加简单、直观和可靠！ 🎉