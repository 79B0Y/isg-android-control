# Android Controller Service - Termux proot Ubuntu 安装指南

> **专用于 Termux 中 proot Ubuntu 环境的完整安装和使用指南**

## 📋 目录

- [环境要求](#环境要求)
- [快速安装](#快速安装)
- [详细安装步骤](#详细安装步骤)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [Home Assistant 集成](#home-assistant-集成)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

## 🔧 环境要求

### Termux 环境
- **Termux**: 最新版本 (从 F-Droid 或 GitHub 下载)
- **proot-distro**: 已安装 Ubuntu 系统
- **存储权限**: 确保 Termux 有存储访问权限

### 系统要求
- **Ubuntu 版本**: 20.04 或更新版本
- **Python**: 3.9+ (脚本会自动安装)
- **内存**: 至少 2GB 可用内存
- **存储**: 至少 2GB 可用空间

### 网络要求
- **网络连接**: 能访问互联网下载依赖包
- **ADB 设备**: Android 设备开启网络 ADB 调试

## ⚡ 快速安装

### 1. 准备 Termux 环境

```bash
# 在 Termux 主环境中安装 proot-distro
pkg update && pkg upgrade -y
pkg install proot-distro -y

# 安装 Ubuntu (如果尚未安装)
proot-distro install ubuntu

# 登录到 Ubuntu 环境
proot-distro login ubuntu
```

### 2. 一键安装

```bash
# 在 proot Ubuntu 环境中执行
cd /path/to/isg-android-control
./install-termux-ubuntu.sh
```

### 3. 启动服务

```bash
# 连接 Android 设备 (在 Termux 主环境或 Ubuntu 中)
./connect.sh 192.168.1.100:5555

# 启动服务
./start.sh
```

访问 http://localhost:8000/docs 查看 API 文档。

## 📦 详细安装步骤

### 步骤 1: 环境准备

1. **安装和配置 Termux**
   ```bash
   # 下载 Termux (推荐从 F-Droid)
   # 授予存储权限
   termux-setup-storage
   
   # 更新包管理器
   pkg update && pkg upgrade -y
   ```

2. **安装 proot-distro**
   ```bash
   pkg install proot-distro git curl wget -y
   
   # 安装 Ubuntu 系统
   proot-distro install ubuntu
   
   # 首次登录配置
   proot-distro login ubuntu
   ```

3. **配置 Ubuntu 环境**
   ```bash
   # 在 Ubuntu 中更新系统
   apt update && apt upgrade -y
   
   # 安装基础工具 (可选，脚本会自动安装)
   apt install curl wget git -y
   ```

### 步骤 2: 获取项目代码

```bash
# 克隆项目 (在 Ubuntu 环境中)
git clone <项目地址>
cd isg-android-control

# 或者从现有目录复制
# cp -r /path/to/project ./
```

### 步骤 3: 运行安装脚本

```bash
# 使脚本可执行
chmod +x install-termux-ubuntu.sh

# 标准安装
./install-termux-ubuntu.sh

# 调试模式安装
./install-termux-ubuntu.sh -d

# 跳过系统依赖 (如已安装)
./install-termux-ubuntu.sh -s

# 强制重新安装
./install-termux-ubuntu.sh -f
```

### 步骤 4: 验证安装

```bash
# 检查服务状态
./status.sh

# 检查虚拟环境
source venv/bin/activate
python -c "import src.core.config; print('✓ 安装成功')"
```

## ⚙️ 配置说明

### 主要配置文件

1. **`.env` - 环境变量配置**
   ```bash
   # 服务器配置
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   
   # ADB 设备配置
   ADB_DEVICE_SERIAL=192.168.1.100:5555
   
   # MQTT 配置 (Home Assistant 集成)
   MQTT_BROKER_HOST=192.168.1.100
   MQTT_USERNAME=admin
   MQTT_PASSWORD=admin
   ```

2. **`configs/config.yaml` - 主配置文件**
   ```yaml
   # 详细的服务配置
   server:
     host: "0.0.0.0"
     port: 8000
   
   adb:
     device_serial: "192.168.1.100:5555"
     timeout: 30
   
   mqtt:
     broker_host: "192.168.1.100"
     broker_port: 1883
     username: "admin"
     password: "admin"
   ```

### ADB 设备配置

1. **Android 设备端**
   ```bash
   # 开启开发者选项
   # 设置 > 关于手机 > 连续点击"版本号" 7次
   
   # 开启 USB 调试和网络 ADB 调试
   # 设置 > 开发者选项 > USB调试 (开启)
   # 设置 > 开发者选项 > 网络ADB调试 (开启)
   
   # 设置 ADB 端口 (通常是 5555)
   ```

2. **连接设备**
   ```bash
   # 方法1: 使用连接脚本
   ./connect.sh 192.168.1.100:5555
   
   # 方法2: 手动连接
   adb connect 192.168.1.100:5555
   adb devices  # 验证连接
   ```

## 🚀 使用指南

### 启动和停止服务

```bash
# CLI命令方式（推荐）
isg-android-control start          # 后台启动
isg-android-control start -f       # 前台启动
isg-android-control stop           # 停止服务
isg-android-control restart        # 重启服务
isg-android-control status         # 基本状态
isg-android-control status -d      # 详细状态
isg-android-control logs           # 查看日志（最后50行）
isg-android-control logs -f        # 实时跟踪日志
isg-android-control logs -n 100    # 查看最后100行
isg-android-control logs --error   # 只显示错误日志

# 传统脚本方式
./start.sh                         # 启动服务
./stop.sh                          # 停止服务
./status.sh                        # 检查状态

# 在后台启动（脚本方式）
nohup ./start.sh > service.log 2>&1 &
```

### API 使用

1. **访问 API 文档**
   - 浏览器访问: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

2. **常用 API 端点**
   ```bash
   # 获取设备信息
   curl http://localhost:8000/api/device/info
   
   # 截图
   curl -X POST http://localhost:8000/api/screenshot/capture
   
   # 导航控制
   curl -X POST http://localhost:8000/api/navigation \
        -H "Content-Type: application/json" \
        -d '{"direction": "up"}'
   
   # 启动应用
   curl -X POST http://localhost:8000/api/apps/launch \
        -H "Content-Type: application/json" \
        -d '{"package_name": "com.android.settings"}'
   ```

### 日志查看

```bash
# CLI命令方式（推荐）
isg-android-control logs           # 查看最后50行日志
isg-android-control logs -f        # 实时跟踪日志
isg-android-control logs -n 200    # 查看最后200行日志
isg-android-control logs --error   # 只显示错误日志

# 传统命令方式
tail -f data/logs/android_controller.log     # 查看实时日志
grep "ERROR" data/logs/*.log                 # 查看错误日志
tail -100 data/logs/android_controller.log   # 查看最近日志
```

## 🏠 Home Assistant 集成

### 配置 MQTT

1. **修改配置文件**
   ```bash
   # 编辑 .env 文件
   nano .env
   
   # 设置 MQTT 配置
   MQTT_BROKER_HOST=<你的HA服务器IP>
   MQTT_BROKER_PORT=1883
   MQTT_USERNAME=<MQTT用户名>
   MQTT_PASSWORD=<MQTT密码>
   ```

2. **启动服务**
   ```bash
   ./start.sh
   ```

3. **Home Assistant 中查看设备**
   - 设备会自动通过 MQTT Discovery 添加
   - 在 HA 中查看: 配置 > 设备与服务 > MQTT

### 可用功能

- **📱 截图相机**: 实时查看设备屏幕
- **🎮 导航控制**: 方向键、返回、主页等
- **🔊 音量控制**: 媒体、通知、系统音量
- **💡 亮度控制**: 屏幕亮度调节
- **🔌 屏幕开关**: 屏幕开关控制
- **📊 系统监控**: CPU、内存、电池等传感器
- **🎯 应用快捷**: 快速启动常用应用

## ❓ 常见问题

### Q1: 安装失败，提示网络错误
**A**: 
```bash
# 检查网络连接
ping google.com

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或使用代理
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
```

### Q2: ADB 设备连接失败
**A**: 
```bash
# 检查设备网络 ADB 调试是否开启
# 检查 IP 地址是否正确
# 尝试重启 ADB 服务
adb kill-server
adb start-server
adb connect <设备IP>:5555
```

### Q3: 虚拟环境创建失败
**A**: 
```bash
# 确保 Python 版本 >= 3.9
python3 --version

# 手动安装 venv
apt install python3-venv python3-dev -y

# 重新运行安装脚本
./install-termux-ubuntu.sh -f
```

### Q4: 服务启动失败
**A**: 
```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 更换端口
export SERVER_PORT=8001
./start.sh

# 查看详细错误
./start.sh --debug
```

### Q5: MQTT 连接失败
**A**: 
```bash
# 检查 MQTT 服务器连通性
telnet <MQTT服务器IP> 1883

# 检查用户名密码
mosquitto_sub -h <MQTT服务器IP> -p 1883 -u <用户名> -P <密码> -t test

# 查看 MQTT 日志
tail -f data/logs/*.log | grep MQTT
```

### Q6: Home Assistant 中看不到设备
**A**: 
```bash
# 检查 MQTT 集成是否启用
# 重启 MQTT 集成: 配置 > 设备与服务 > MQTT > 重新载入

# 手动触发发现
curl -X POST http://localhost:8000/api/homeassistant/discovery

# 检查 MQTT 主题
mosquitto_sub -h <HA服务器IP> -p 1883 -u <用户名> -P <密码> -t "homeassistant/#" -v
```

## 🔧 故障排除

### 检查安装环境

```bash
# 检查 proot 环境
cat /etc/os-release
echo $PROOT_L2S_DIR

# 检查 Python 环境
python3 --version
python3 -c "import venv, pip; print('✓ Python环境正常')"

# 检查依赖安装
pip list | grep -E "(fastapi|uvicorn|pydantic|loguru)"
```

### 日志分析

```bash
# 系统日志
journalctl -u android-controller --tail=50

# 应用日志
tail -f data/logs/android_controller.log

# 错误日志
grep -i "error\|exception\|traceback" data/logs/*.log
```

### 网络诊断

```bash
# 检查端口监听
netstat -tlnp | grep 8000
ss -tlnp | grep 8000

# 检查 API 访问
curl -I http://localhost:8000/health

# 检查 ADB 网络连接
adb connect <设备IP>:5555
adb shell echo "test"
```

### 重置和重装

```bash
# 软重置 (保留配置)
./stop.sh
rm -rf venv
./install-termux-ubuntu.sh

# 硬重置 (完全重新安装)
./stop.sh
rm -rf venv data/logs/* data/screenshots/*
./install-termux-ubuntu.sh -f

# 重置配置
cp .env .env.backup
rm .env
./install-termux-ubuntu.sh
```

## 📝 高级配置

### 性能优化

1. **内存优化**
   ```yaml
   # configs/config.yaml
   server:
     workers: 1  # proot环境建议使用单进程
     
   monitoring:
     performance_interval: 60  # 降低监控频率
   ```

2. **网络优化**
   ```bash
   # .env
   ADB_TIMEOUT=60
   ADB_RETRY_ATTEMPTS=5
   MQTT_KEEP_ALIVE=120
   ```

### 安全配置

1. **网络安全**
   ```yaml
   server:
     host: "127.0.0.1"  # 仅本地访问
   ```

2. **ADB 安全**
   ```bash
   # 使用 ADB 密钥认证
   adb pair <设备IP>:5555
   ```

### 自动启动

```bash
# 创建系统服务 (Ubuntu)
sudo tee /etc/systemd/system/android-controller.service > /dev/null <<EOF
[Unit]
Description=Android Controller Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用自动启动
sudo systemctl enable android-controller
sudo systemctl start android-controller
```

---

## 📞 支持和反馈

如果遇到问题或需要帮助:

1. 查看日志文件: `data/logs/*.log`
2. 检查配置文件: `.env` 和 `configs/config.yaml`
3. 运行状态检查: `./status.sh`
4. 查看安装日志: `/tmp/*.log`

**项目地址**: [GitHub Repository]
**文档**: 查看项目根目录下的其他 README 文件

---

*本文档专门针对 Termux proot Ubuntu 环境编写，其他环境请参考对应的安装指南。*