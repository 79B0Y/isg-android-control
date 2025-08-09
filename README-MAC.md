# Android Controller Service - macOS 使用指南

专为macOS环境优化的Android设备控制服务安装和使用指南。

## 🍎 macOS 快速开始

### 系统要求
- **macOS**: 10.15+ (Catalina及以上)
- **Xcode Command Line Tools**: 自动安装
- **Homebrew**: 自动安装 (如果未安装)
- **设备**: Android设备或模拟器

### ⚡ 一键安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd isg-android-control

# 2. 运行macOS安装脚本
./install-mac.sh
```

安装脚本会自动完成：
- ✅ 检查并安装Xcode Command Line Tools
- ✅ 安装Homebrew (如果需要)
- ✅ 安装Python 3.11、ADB、Redis等依赖
- ✅ 创建Python虚拟环境
- ✅ 安装所有Python包
- ✅ 启动Redis服务
- ✅ 生成macOS专用脚本

### 🔌 连接设备

#### 方式1: Android模拟器 (推荐新手)
```bash
# 1. 启动Android Studio的AVD Manager
# 2. 创建并启动Android虚拟设备
# 3. 连接模拟器
./connect-mac.sh
```

#### 方式2: 真实Android设备
```bash
# 1. 在Android设备上:
#    - 启用开发者选项
#    - 开启USB调试
#    - 开启网络ADB调试
# 2. 确保设备和Mac在同一WiFi
# 3. 连接设备
./connect-mac.sh 192.168.1.100:5555
```

### 🚀 启动服务

```bash
./start-mac.sh
```

启动后访问：
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📱 Android设备准备

### Android模拟器 (最简单)

**Android Studio AVD**:
1. 下载Android Studio
2. 打开AVD Manager
3. 创建Android虚拟设备 (推荐API 29+)
4. 启动模拟器
5. 运行 `./connect-mac.sh`

**Genymotion**:
1. 下载Genymotion
2. 创建虚拟设备
3. 启动模拟器
4. 运行 `./connect-mac.sh`

### 真实Android设备

**设备设置**:
1. 打开 **设置** → **关于手机**
2. 连续点击 **版本号** 7次启用开发者选项
3. 进入 **设置** → **系统** → **开发者选项**
4. 启用 **USB调试**
5. 启用 **网络ADB调试** (如果有)

**网络连接**:
1. 确保Android设备和Mac连接同一WiFi
2. 查看设备IP: **设置** → **关于手机** → **状态信息** → **IP地址**
3. 在Mac上连接: `./connect-mac.sh <设备IP>:5555`

## 🛠️ macOS 专用命令

### 基本操作
```bash
# 连接帮助
./connect-mac.sh --help

# 连接本地模拟器
./connect-mac.sh

# 连接真实设备
./connect-mac.sh 192.168.1.100:5555

# 启动服务
./start-mac.sh

# 停止服务
./stop-mac.sh

# 重启服务
./stop-mac.sh && ./start-mac.sh
```

### Redis管理 (Homebrew)
```bash
# 启动Redis
brew services start redis

# 停止Redis
brew services stop redis

# 重启Redis
brew services restart redis

# 查看Redis状态
brew services list | grep redis

# Redis命令行
redis-cli
```

### 系统监控
```bash
# 查看服务进程
ps aux | grep "src.main"

# 查看端口占用
lsof -i :8000

# 查看Python进程
ps aux | grep python

# 查看ADB设备
adb devices

# ADB连接状态
adb devices -l
```

### 日志查看
```bash
# 实时日志
tail -f data/logs/android_controller.log

# 错误日志
tail -f data/logs/errors.log

# 最近100行日志
tail -100 data/logs/android_controller.log

# 搜索特定内容
grep "ERROR" data/logs/android_controller.log
```

## 🏠 Home Assistant 集成

### MQTT Broker 设置

**选项1: 本地Mosquitto**
```bash
# 安装Mosquitto
brew install mosquitto

# 启动服务
brew services start mosquitto

# 配置文件编辑 .env
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
```

**选项2: Home Assistant Add-on**
```bash
# 在Home Assistant中安装Mosquitto broker
# 配置.env文件
MQTT_BROKER_HOST=<Home Assistant IP>
MQTT_BROKER_PORT=1883
MQTT_USERNAME=<username>
MQTT_PASSWORD=<password>
```

### Home Assistant 配置

在`configuration.yaml`中添加：
```yaml
mqtt:
  broker: 127.0.0.1  # 或你的MQTT broker IP
  discovery: true
  discovery_prefix: homeassistant
```

重启Home Assistant后，会自动发现Android Controller实体。

## 🔧 故障排除

### 常见问题

**1. ADB连接失败**
```bash
# 重启ADB服务
adb kill-server
adb start-server

# 检查ADB版本
adb --version

# 手动连接
adb connect <设备IP>:5555
```

**2. Redis连接错误**
```bash
# 检查Redis状态
brew services list | grep redis

# 启动Redis
brew services start redis

# 测试连接
redis-cli ping
```

**3. Python依赖问题**
```bash
# 重新激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt

# 检查依赖
./scripts/check_deps.py
```

**4. 端口被占用**
```bash
# 查看端口占用
lsof -i :8000

# 终止占用进程
sudo lsof -t -i :8000 | xargs kill -9

# 或更改配置中的端口
nano configs/config.yaml
```

### 模拟器特定问题

**Android Studio AVD**:
- 确保虚拟设备已正确启动
- 检查AVD Manager中的设备状态
- 尝试冷启动: Cold Boot Now

**Genymotion**:
- 确保ADB连接已启用
- 检查Settings → ADB → Use custom Android SDK tools

### 网络问题

**设备发现**:
```bash
# ping测试
ping <设备IP>

# 端口测试
nc -zv <设备IP> 5555

# 网络扫描
nmap -p 5555 192.168.1.0/24
```

**防火墙设置**:
- 确保macOS防火墙允许Python连接
- 系统偏好设置 → 安全性与隐私 → 防火墙

## 📖 API使用示例

### 基本控制
```bash
# 导航控制
curl -X POST "http://localhost:8000/api/v1/remote/navigate/up"

# 音量控制
curl -X POST "http://localhost:8000/api/v1/audio/volume" \
  -H "Content-Type: application/json" \
  -d '{"stream": "media", "level": 10}'

# 截图
curl -X POST "http://localhost:8000/api/v1/screenshot/capture"
```

### Python客户端示例
```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # 获取设备信息
        response = await client.get("http://localhost:8000/api/v1/system/info")
        print(response.json())
        
        # 导航控制
        await client.post("http://localhost:8000/api/v1/remote/navigate/up")
        
        # 截图
        await client.post("http://localhost:8000/api/v1/screenshot/capture")

# 运行测试
asyncio.run(test_api())
```

## 🎯 最佳实践

### 开发环境
- 使用Android Studio的AVD Manager管理模拟器
- 启用ADB over WiFi便于调试
- 配置VS Code的Python扩展

### 生产部署
- 使用真实设备时配置静态IP
- 设置MQTT认证
- 启用HTTPS (通过反向代理)
- 配置日志轮转

### 性能优化
- 调整截图质量以平衡文件大小和清晰度
- 设置合适的MQTT keep-alive间隔
- 根据网络情况调整ADB超时

---

## 🆘 获取帮助

如有问题，请:
1. 查看 `data/logs/` 中的日志文件
2. 运行 `./scripts/check_deps.py` 检查依赖
3. 访问项目GitHub仓库提交Issue
4. 查看完整文档 `README.md`

**常用链接**:
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- Redis监控: `redis-cli monitor`
- 系统日志: `tail -f data/logs/android_controller.log`