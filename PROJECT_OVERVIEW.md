# Android TV Box Home Assistant Integration - Project Overview

## 项目简介

这是一个完整的Home Assistant自定义组件，用于通过ADB（Android Debug Bridge）控制Android TV盒子。该集成提供了全面的设备控制功能，包括媒体播放、系统设置、设备监控和远程控制。

## 项目结构

```
android-control/
├── custom_components/
│   └── android_tv_box/
│       ├── __init__.py              # 主组件文件
│       ├── manifest.json             # 组件清单
│       ├── config.py                 # 配置模式
│       ├── config_flow.py            # 配置流程
│       ├── adb_service.py            # ADB连接服务
│       ├── media_player.py           # 媒体播放器实体
│       ├── switch.py                 # 开关实体
│       ├── camera.py                 # 摄像头实体
│       ├── sensor.py                 # 传感器实体
│       ├── remote.py                 # 遥控器实体
│       ├── services.py               # 自定义服务
│       └── README.md                 # 组件文档
├── test_adb_connection.py            # ADB连接测试脚本
├── deploy.sh                         # 部署脚本
├── setup_android.sh                  # Android端设置脚本
├── setup_ubuntu.sh                   # Ubuntu容器设置脚本
├── requirements.txt                  # Python依赖
└── PROJECT_OVERVIEW.md               # 项目概览（本文件）
```

## 核心功能

### 1. 媒体播放器实体 (Media Player)
- **播放控制**: 播放、暂停、停止、上一首、下一首
- **音量控制**: 设置音量级别、静音/取消静音、音量增减
- **应用启动**: 启动Android应用程序
- **状态监控**: 当前应用、音量级别、电源状态

### 2. 开关实体 (Switch)
- **电源开关**: 开启/关闭设备
- **WiFi开关**: 启用/禁用WiFi连接

### 3. 摄像头实体 (Camera)
- **屏幕截图**: 每3秒自动截图
- **图像存储**: 保留最近3张带时间戳的截图
- **实时查看**: 在Home Assistant中查看设备屏幕

### 4. 传感器实体 (Sensor)
- **亮度传感器**: 当前屏幕亮度级别
- **WiFi SSID传感器**: 连接的WiFi网络名称
- **IP地址传感器**: 设备IP地址
- **当前应用传感器**: 前台应用程序
- **CPU使用率传感器**: 系统CPU利用率
- **内存使用传感器**: RAM使用量（MB）
- **高CPU警告传感器**: CPU使用率超过阈值时告警

### 5. 遥控器实体 (Remote)
- **导航控制**: 上、下、左、右、确认、返回、主页
- **媒体控制**: 播放、暂停、停止、下一首、上一首
- **音量控制**: 音量增减、静音
- **电源控制**: 开机/关机

### 6. 自定义服务
- **截图服务**: 手动截图
- **启动应用服务**: 启动特定Android应用
- **设置亮度服务**: 调整屏幕亮度（0-255）
- **设置音量服务**: 设置音量级别（0-100%）
- **终止进程服务**: 终止运行中的进程

## 技术架构

### 运行环境
- **宿主环境**: Android Termux
- **Linux容器**: Termux proot-distro Ubuntu
- **Home Assistant**: 运行在Ubuntu容器内
- **ADB服务**: 在Android系统层运行

### 连接方式
- **ADB连接**: `adb connect 127.0.0.1:5555`
- **通信协议**: 通过ADB shell命令执行各种操作
- **设备地址**: 127.0.0.1:5555
- **运行模式**: Home Assistant在Ubuntu容器内控制本机Android系统

## 部署指南

### 快速部署

1. **Android端设置**:
   ```bash
   # 在Termux中运行
   bash setup_android.sh
   ```

2. **Ubuntu容器设置**:
   ```bash
   # 在Ubuntu容器中运行
   bash setup_ubuntu.sh
   ```

3. **部署到Home Assistant**:
   ```bash
   # 在项目根目录运行
   bash deploy.sh
   ```

### 手动部署

1. **Android端准备**:
   - 安装Termux并获取root权限
   - 安装Android工具包
   - 配置ADB TCP服务

2. **Ubuntu容器环境**:
   - 安装proot-distro和Ubuntu
   - 安装系统依赖
   - 创建Python虚拟环境
   - 安装Python依赖

3. **Home Assistant集成**:
   - 复制集成到custom_components目录
   - 配置configuration.yaml
   - 重启Home Assistant

## 配置选项

### 基本配置
```yaml
android_tv_box:
  host: "127.0.0.1"                    # ADB主机地址
  port: 5555                           # ADB端口
  name: "Android TV Box"               # 设备名称
  screenshot_path: "/sdcard/isgbackup/screenshot/"  # 截图路径
  screenshot_keep_count: 3              # 保留截图数量
  screenshot_interval: 3                # 截图间隔（秒）
  performance_check_interval: 500       # 性能检查间隔（毫秒）
  cpu_threshold: 50                    # CPU使用率阈值
  termux_mode: true                    # Termux模式
  ubuntu_venv_path: "~/uiauto_env"      # Python虚拟环境路径
  adb_path: "/usr/bin/adb"             # ADB二进制路径
```

> 提示：早期版本中使用的 `device_name` 字段依旧可用，但建议切换为标准的 `name`。

### 实体配置
```yaml
android_tv_box:
  # ... 其他选项 ...
  media_player: true    # 启用媒体播放器
  switch: true          # 启用开关
  camera: true          # 启用摄像头
  sensor: true          # 启用传感器
  remote: true          # 启用遥控器
```

## 使用示例

### 自动化示例

#### 基于时间的亮度调整
```yaml
automation:
  - alias: "Evening brightness"
    trigger:
      platform: time
      at: "18:00:00"
    action:
      service: android_tv_box.set_brightness
      data:
        brightness: 100

  - alias: "Night brightness"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: android_tv_box.set_brightness
      data:
        brightness: 50
```

#### 高CPU使用率监控
```yaml
automation:
  - alias: "High CPU warning"
    trigger:
      platform: state
      entity_id: sensor.android_tv_box_high_cpu_warning
      to: "High CPU detected"
    action:
      service: notify.persistent_notification
      data:
        message: "Android TV Box CPU usage is high!"
```

### 服务调用示例

#### 启动应用
```yaml
service: android_tv_box.launch_app
data:
  package_name: "com.example.app"
  activity_name: "com.example.app.MainActivity"
```

#### 设置音量
```yaml
service: android_tv_box.set_volume
data:
  volume: 75
```

#### 手动截图
```yaml
service: android_tv_box.take_screenshot
data:
  filename: "custom_screenshot.png"
  keep_count: 5
```

## 测试和调试

### 连接测试
```bash
# 运行ADB连接测试
python3 test_adb_connection.py
```

### 集成测试
```bash
# 在Ubuntu容器中运行
python3 test_integration.py
```

### 日志查看
- Home Assistant日志: `hass --config ~/.homeassistant --log-file homeassistant.log`
- ADB命令日志: 在adb_service.py中启用调试日志

## 故障排除

### 常见问题

1. **ADB连接失败**
   - 检查ADB服务是否运行
   - 确认端口5555是否开放
   - 验证设备是否已root

2. **权限问题**
   - 确保ADB配置有root权限
   - 检查文件权限设置
   - 验证ADB二进制可执行性

3. **性能问题**
   - 调整截图间隔
   - 减少传感器更新频率
   - 监控CPU使用率并调整阈值

### 调试步骤

1. **检查ADB连接**:
   ```bash
   adb devices
   adb shell getprop ro.product.model
   ```

2. **测试基本命令**:
   ```bash
   adb shell input keyevent 3  # Home键
   adb shell input keyevent 4  # Back键
   ```

3. **检查Home Assistant日志**:
   ```bash
   tail -f ~/.homeassistant/homeassistant.log
   ```

## 安全考虑

- **本地连接**: ADB连接限制在localhost（127.0.0.1）
- **容器隔离**: Ubuntu容器提供额外的安全层
- **命令验证**: 所有ADB命令在执行前都经过验证
- **访问日志**: ADB操作被记录用于监控

## 开发路线图

### Phase 1: 基础功能 ✅
- [x] ADB连接管理
- [x] 基本媒体播放控制
- [x] 电源开关控制
- [x] 音量控制实现

### Phase 2: 高级功能 ✅
- [x] 屏幕截图摄像头实体
- [x] 系统传感器监控
- [x] 遥控器按键映射
- [x] 应用状态监控

### Phase 3: 优化与扩展 ✅
- [x] 性能监控和自动处理
- [x] 错误恢复机制
- [x] 配置界面开发
- [x] 多设备支持

### Phase 4: 未来计划
- [ ] Web界面配置
- [ ] 更多传感器类型
- [ ] 批量操作支持
- [ ] 设备模板系统

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 进行更改并添加测试
4. 提交拉取请求

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件。

## 支持

如有问题或疑问：
1. 查看故障排除部分
2. 检查Home Assistant日志
3. 在GitHub上创建详细的问题报告

---

**项目状态**: ✅ 完成  
**版本**: 1.0.0  
**最后更新**: 2024年12月
