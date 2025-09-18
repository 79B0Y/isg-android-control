# Android TV Box Home Assistant Integration - 快速开始指南

## 🚀 安装方式

### 方式1: 通过HACS安装 (推荐)

> **最简单的方式**: 通过HACS (Home Assistant Community Store) 安装

1. **安装HACS** (如果尚未安装)
   - 参考 [HACS官方安装指南](https://hacs.xyz/docs/installation/installation/)

2. **添加自定义仓库**
   - 打开HACS → Integrations
   - 点击右上角菜单 → Custom repositories
   - 添加仓库: `https://github.com/your-username/android-tv-box`
   - 类别选择: Integration

3. **安装集成**
   - 搜索 "Android TV Box"
   - 点击下载安装
   - 重启Home Assistant

4. **配置集成**
   - 设置 → 设备与服务 → 添加集成
   - 搜索 "Android TV Box" 并配置

> 📖 **详细HACS安装指南**: 查看 [HACS_INSTALLATION.md](HACS_INSTALLATION.md)

### 方式2: 手动安装

> **传统方式**: 手动下载和配置

## 🚀 5分钟快速部署

### 前置条件
- Android设备（已root）
- Termux应用
- 网络连接

### 步骤1: Android端设置 (2分钟)

> **注意**: 此步骤只设置ADB服务，Home Assistant将在Ubuntu容器中安装

1. **打开Termux应用**
2. **运行设置脚本**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/your-repo/android-tv-box/main/setup_android.sh | bash
   ```
   或者手动运行：
   ```bash
   pkg update
   pkg install android-tools
   su
   setprop service.adb.tcp.port 5555
   stop adbd && start adbd
   adb connect 127.0.0.1:5555
   exit
   ```

### 步骤2: Ubuntu容器设置 (2分钟)

> **注意**: Home Assistant已经在Ubuntu容器中预装，只需要安装集成组件依赖

1. **安装proot-distro**:
   ```bash
   pkg install proot-distro
   proot-distro install ubuntu
   ```

2. **进入Ubuntu容器**:
   ```bash
   proot-distro login ubuntu
   ```

3. **运行Ubuntu设置脚本**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/your-repo/android-tv-box/main/setup_ubuntu.sh | bash
   ```

### 步骤3: 部署集成 (1分钟)

1. **下载并部署**:
   ```bash
   # 在Ubuntu容器中
   cd ~
   git clone https://github.com/your-repo/android-tv-box.git
   cd android-tv-box
   bash deploy.sh
   ```

2. **启动Home Assistant**:
   ```bash
   ./start_homeassistant.sh
   ```

## ✅ 验证安装

### 测试ADB连接
```bash
python3 test_adb_connection.py
```

### 检查Home Assistant
1. 打开浏览器访问 `http://localhost:8123`
2. 查看设备列表中的"Android TV Box"
3. 测试媒体播放器控制

### 访问Web管理界面
1. 打开浏览器访问 `http://localhost:3003`
2. 查看Dashboard了解设备状态
3. 在Apps标签中添加/管理应用
4. 在Configuration标签中调整设置

## 🎯 快速使用

### 基本控制
- **媒体播放**: 使用Home Assistant媒体播放器卡片
- **电源控制**: 使用电源开关
- **音量调节**: 使用音量滑块
- **屏幕查看**: 使用摄像头实体

### Web管理界面使用
- **Dashboard**: 实时监控设备状态和iSG运行情况
- **Apps管理**: 添加、编辑、删除Android应用
- **配置管理**: 调整ADB、HA、MQTT等设置
- **连接测试**: 测试ADB和MQTT连接状态

### 自动化示例
```yaml
# 晚上自动降低亮度
automation:
  - alias: "Night mode"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: android_tv_box.set_brightness
      data:
        brightness: 50
```

### 服务调用
```yaml
# 启动Netflix
service: android_tv_box.launch_app
data:
  package_name: "com.netflix.mediaclient"

# 设置音量到75%
service: android_tv_box.set_volume
data:
  volume: 75
```

## 🔧 常见问题

### Q: ADB连接失败
**A**: 检查是否已root，运行 `adb devices` 确认连接

### Q: Home Assistant无法启动
**A**: 检查Python环境，运行 `source ~/uiauto_env/bin/activate`

### Q: 设备不显示
**A**: 重启Home Assistant，检查configuration.yaml配置

### Q: 截图不工作
**A**: 检查存储权限，确认路径 `/sdcard/isgbackup/screenshot/` 存在

### Q: 无法访问Web管理界面
**A**: 检查端口3003是否被占用，确认防火墙允许该端口访问

### Q: Web界面显示错误
**A**: 检查Home Assistant日志，确认所有依赖已正确安装

## 📱 支持的Android应用

### 媒体应用
- Netflix
- YouTube
- Spotify
- Plex
- Kodi

### 系统应用
- 设置
- 文件管理器
- 浏览器

## 🎮 遥控器命令

| 命令 | 功能 |
|------|------|
| `up`, `down`, `left`, `right` | 方向键 |
| `enter`, `ok` | 确认键 |
| `back` | 返回键 |
| `home` | 主页键 |
| `play`, `pause`, `stop` | 媒体控制 |
| `volume_up`, `volume_down` | 音量控制 |

## 📊 监控功能

### 实时监控
- CPU使用率
- 内存使用量
- 网络状态
- 当前应用

### 告警功能
- 高CPU使用率告警
- 设备离线检测
- 性能异常监控

## 🔐 安全提示

- 仅在受信任的网络环境中使用
- 定期更新ADB服务
- 监控设备访问日志
- 使用强密码保护Home Assistant

## 🌐 Web管理界面

### 访问地址
- **本地访问**: `http://localhost:3003`
- **网络访问**: `http://[设备IP]:3003`

### 主要功能
- **Dashboard**: 设备状态监控、iSG状态、快速操作
- **Apps**: 应用管理（添加/编辑/删除）、可见性控制
- **Configuration**: ADB连接、Home Assistant、截图、iSG监控配置
- **MQTT**: MQTT broker配置、主题设置、连接测试

### 快速操作
1. **添加应用**: Apps标签 → Add App → 填写名称和包名
2. **测试连接**: Configuration标签 → Test Connection
3. **监控状态**: Dashboard标签 → 查看实时状态
4. **配置MQTT**: MQTT标签 → 设置broker和主题

## 📞 获取帮助

- 📖 详细文档: [README.md](README.md)
- 🌐 Web界面指南: [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)
- 🐛 问题报告: [GitHub Issues](https://github.com/your-repo/android-tv-box/issues)
- 💬 社区讨论: [Home Assistant Community](https://community.home-assistant.io/)

---

**🎉 恭喜！您已成功部署Android TV Box Home Assistant集成！**

现在您可以：
- 通过Home Assistant控制您的Android TV盒子
- 使用Web管理界面轻松配置和管理
- 创建自动化场景
- 监控设备状态
- 享受智能家居体验
