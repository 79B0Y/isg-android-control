# Android Controller Service

专为iSG Android设备设计的控制服务，运行在Termux Ubuntu环境中，通过ADB提供完整的设备控制功能，支持Home Assistant MQTT集成。

## ✨ 主要功能

### 🎮 遥控导航控制
- 方向键导航（上下左右）
- 确认、返回、主页键操作
- 自定义按键映射
- 批量操作支持

### 🔊 音频与显示控制
- 多音频流音量控制（媒体、通知、系统等）
- 屏幕亮度自动调节
- 屏幕开关控制
- 实时状态监控

### 📱 应用管理
- 应用启动、停止、切换
- 支持常用应用快捷方式（YouTube TV、Spotify、Netflix等）
- 运行中应用监控
- 应用包名自动识别

### 📊 系统监控
- CPU、内存、存储使用率
- 电池电量和温度监控
- 网络连接状态
- 系统运行时间统计

### 📸 截图功能
- 高质量屏幕截图
- 支持JPEG/PNG格式
- 自动文件管理（保留最新3张）
- Base64编码支持MQTT传输

### 🏠 Home Assistant集成
- MQTT自动发现
- 丰富的实体类型支持
- 实时状态同步
- 命令响应处理

## 🚀 快速开始

### 环境要求

#### Termux Ubuntu 环境
- **操作系统**: Termux + Ubuntu (proot)
- **Python**: >= 3.9
- **ADB**: Android SDK Platform Tools
- **设备**: 支持ADB调试的Android设备

#### macOS 环境
- **操作系统**: macOS 10.15+ (Catalina及以上)
- **Python**: >= 3.9 (通过Homebrew安装)
- **Homebrew**: macOS包管理器
- **Xcode Command Line Tools**: 编译工具
- **设备**: Android设备或模拟器

### 一键安装

#### Termux Ubuntu 环境
```bash
# 1. 克隆项目
git clone <repository-url>
cd isg-android-control

# 2. 一键安装
./install.sh

# 3. 连接Android设备
./connect.sh 192.168.1.100:5555

# 4. 启动服务
isg-android-control start
```

#### macOS 环境
```bash
# 1. 克隆项目
git clone <repository-url>
cd isg-android-control

# 2. macOS一键安装
./install-mac.sh

# 3. 连接Android设备或模拟器
./connect-mac.sh 192.168.1.100:5555  # 真实设备
./connect-mac.sh                      # 本地模拟器

# 4. 启动服务
isg-android-control start
```

**Termux安装脚本会自动：**
- 检查Python 3.9+环境
- 安装系统依赖 (ADB、Redis等)
- 创建虚拟环境
- 安装Python依赖包
- 创建必要目录和配置文件
- 设置管理脚本

**macOS安装脚本会自动：**
- 检查并安装Xcode Command Line Tools
- 安装Homebrew (如果未安装)
- 安装Python 3.11、ADB、Redis等
- 启动Redis服务
- 创建虚拟环境和安装依赖
- 生成macOS专用管理脚本

> 📖 **macOS用户**: 查看详细的 [macOS使用指南](README-MAC.md) 获取完整的安装、配置和使用说明

### 手动安装

```bash
# 1. 安装系统依赖
pkg update
pkg install python android-tools redis git

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装Python依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p data/{logs,screenshots}

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 6. 配置主配置文件
nano configs/config.yaml
```

### ADB环境配置

```bash
# 运行ADB配置脚本
chmod +x scripts/setup_adb.sh
./scripts/setup_adb.sh

# 手动连接设备
adb connect 192.168.1.100:5555

# 验证连接
adb devices
```

## ⚙️ 配置说明

### 主配置文件 (`configs/config.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000

adb:
  device_serial: "127.0.0.1:5555"
  timeout: 30
  retry_attempts: 3

network:
  static_ip: "192.168.1.100"
  gateway: "192.168.1.1"
  dns_primary: "8.8.8.8"

screenshot:
  quality: 80
  format: "JPEG"
  max_files: 3

mqtt:
  broker_host: "192.168.1.10"
  broker_port: 1883
  client_id: "android_controller"
  device_id: "android_controller"

apps:
  youtube_tv: "com.google.android.youtube.tv"
  spotify: "com.spotify.music"
  netflix: "com.netflix.mediaclient"
```

### 环境变量 (`.env`)

```bash
# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ADB配置
ADB_DEVICE_SERIAL=127.0.0.1:5555
ADB_TIMEOUT=30

# MQTT配置
MQTT_BROKER_HOST=192.168.1.10
MQTT_BROKER_PORT=1883
MQTT_CLIENT_ID=android_controller

# 日志级别
LOG_LEVEL=INFO
```

## 🚦 启动服务

```bash
# 使用启动脚本
./start.sh

# 或者直接运行
source venv/bin/activate
python -m src.main --config configs/config.yaml

# 后台运行
nohup python -m src.main > /dev/null 2>&1 &
```

## 📖 API文档

启动服务后，访问以下地址查看完整API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 主要API端点

#### 遥控导航
```bash
# 导航控制
POST /api/v1/remote/navigate/up
POST /api/v1/remote/navigate/down
POST /api/v1/remote/key/KEYCODE_HOME
```

#### 音频控制
```bash
# 设置音量
POST /api/v1/audio/volume
{
  "stream": "media",
  "level": 10
}

# 获取音量
GET /api/v1/audio/volume/media
```

#### 显示控制
```bash
# 设置亮度
POST /api/v1/display/brightness
{
  "level": 150
}

# 屏幕开关
POST /api/v1/display/screen
{
  "action": "on"
}
```

#### 应用管理
```bash
# 启动应用
POST /api/v1/apps/launch
{
  "package_name": "com.spotify.music"
}

# 获取已安装应用
GET /api/v1/apps/installed
```

#### 截图功能
```bash
# 捕获截图
POST /api/v1/screenshot/capture

# 获取截图列表
GET /api/v1/screenshot/list

# 下载截图
GET /api/v1/screenshot/download/{filename}
```

#### 系统监控
```bash
# 获取系统信息
GET /api/v1/system/info

# 获取性能统计
GET /api/v1/system/performance

# 获取电池信息
GET /api/v1/system/battery
```

## 🏠 Home Assistant集成

### MQTT自动发现实体

服务启动后会自动在Home Assistant中创建以下实体：

#### 摄像头实体
- `camera.android_screenshot` - 实时截图显示

#### 按钮实体
- `button.android_take_screenshot` - 截图按钮
- `button.android_nav_up/down/left/right` - 导航按钮
- `button.android_nav_ok/back/home` - 功能按钮

#### 数值控制实体
- `number.android_volume_media` - 媒体音量
- `number.android_volume_notification` - 通知音量
- `number.android_brightness` - 屏幕亮度

#### 开关实体
- `switch.android_screen` - 屏幕电源开关

#### 传感器实体
- `sensor.android_cpu_usage` - CPU使用率
- `sensor.android_memory_usage` - 内存使用率
- `sensor.android_battery_level` - 电池电量
- `sensor.android_battery_temperature` - 电池温度

#### 应用快捷方式
- `button.android_app_youtube_tv` - YouTube TV
- `button.android_app_spotify` - Spotify
- `button.android_app_netflix` - Netflix

### Home Assistant配置

在Home Assistant的`configuration.yaml`中添加：

```yaml
mqtt:
  broker: 192.168.1.10
  discovery: true
  discovery_prefix: homeassistant
```

### 示例Dashboard卡片

```yaml
# 遥控器卡片
type: grid
cards:
  - type: button
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.android_nav_up
    icon: mdi:arrow-up
  - type: button
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.android_nav_ok
    icon: mdi:checkbox-marked-circle

# 音量控制卡片
type: entities
entities:
  - entity: number.android_volume_media
  - entity: number.android_volume_notification
  - entity: number.android_brightness

# 系统状态卡片
type: entities
entities:
  - entity: sensor.android_cpu_usage
  - entity: sensor.android_memory_usage
  - entity: sensor.android_battery_level
```

## 🔧 常用命令

### 统一CLI命令 (推荐)
```bash
# 服务管理
isg-android-control start            # 启动服务
isg-android-control stop             # 停止服务
isg-android-control restart          # 重启服务
isg-android-control status           # 查看状态
isg-android-control status -d        # 详细状态信息
isg-android-control uninstall        # 卸载服务

# 设备连接
./connect.sh 192.168.1.100:5555      # Termux环境
./connect-mac.sh 192.168.1.100:5555  # macOS环境
```

### 传统脚本方式
```bash
# Termux Ubuntu
./start.sh                           # 启动
./stop.sh                            # 停止
./scripts/monitor.sh                 # 监控

# macOS
./start-mac.sh                       # 启动
./stop-mac.sh                        # 停止
brew services start redis            # Redis管理
```

### 日志查看
```bash
# 查看实时日志
tail -f data/logs/android_controller.log

# 查看错误日志
tail -f data/logs/errors.log

# 查看API访问日志
tail -f data/logs/access.log
```

### ADB操作
```bash
# 连接设备
./adb_connect.sh 192.168.1.100:5555

# 检查连接
adb devices

# 测试设备响应
adb shell echo "test"

# 重启ADB服务
adb kill-server && adb start-server
```

### 截图管理
```bash
# 手动触发截图
curl -X POST http://localhost:8000/api/v1/screenshot/capture

# 查看截图列表
ls -la data/screenshots/

# 清理旧截图
curl -X DELETE http://localhost:8000/api/v1/screenshot/
```

## 🛠️ 故障排除

### ADB连接问题

1. **设备连接失败**
   ```bash
   # 检查设备IP和端口
   adb connect 192.168.1.100:5555
   
   # 重启ADB服务
   adb kill-server
   adb start-server
   ```

2. **权限不足**
   ```bash
   # 确保设备已启用USB调试
   # 检查开发者选项设置
   adb shell su -c "echo test"
   ```

3. **网络连接问题**
   ```bash
   # 检查设备网络连接
   ping 192.168.1.100
   
   # 检查端口是否开放
   nc -zv 192.168.1.100 5555
   ```

### MQTT连接问题

1. **Broker连接失败**
   ```bash
   # 检查broker地址和端口
   nc -zv 192.168.1.10 1883
   
   # 检查认证信息
   mosquitto_sub -h 192.168.1.10 -t test
   ```

2. **Home Assistant发现问题**
   ```bash
   # 检查发现主题
   mosquitto_sub -h 192.168.1.10 -t "homeassistant/+/+/config"
   
   # 手动触发发现
   curl -X POST http://localhost:8000/api/v1/system/status
   ```

### 服务启动问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000
   
   # 修改配置文件中的端口
   nano configs/config.yaml
   ```

2. **依赖包问题**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall
   
   # 检查虚拟环境
   which python
   ```

## 📝 开发说明

### 项目结构
```
isg-android-control/
├── src/
│   ├── core/           # 核心功能模块
│   ├── api/            # REST API接口
│   ├── mqtt/           # MQTT集成
│   ├── models/         # 数据模型
│   └── services/       # 业务服务
├── configs/            # 配置文件
├── scripts/            # 部署脚本
├── data/              # 数据目录
└── tests/             # 测试用例
```

### 开发环境搭建
```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black isort flake8

# 运行测试
python -m pytest tests/

# 代码格式化
black src/
isort src/

# 代码检查
flake8 src/
```

### 添加新功能

1. 在相应模块中实现功能
2. 添加API接口
3. 更新MQTT集成
4. 编写测试用例
5. 更新文档

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题请提交Issue或联系开发者。