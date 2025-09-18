# Android TV Box Home Assistant Integration - 快速开始指南

## 🚀 5分钟快速部署

### 前置条件
- Android设备（已root）
- Termux应用
- 网络连接

### 步骤1: Android端设置 (2分钟)

1. **打开Termux应用**
2. **运行设置脚本**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/your-repo/android-tv-box/main/setup_android.sh | bash
   ```
   或者手动运行：
   ```bash
   pkg update
   pkg install android-tools
   exit
   su
   setprop service.adb.tcp.port 5555
   stop adbd && start adbd
   adb connect 127.0.0.1:5555
   exit
   ```

### 步骤2: Ubuntu容器设置 (2分钟)

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

## 🎯 快速使用

### 基本控制
- **媒体播放**: 使用Home Assistant媒体播放器卡片
- **电源控制**: 使用电源开关
- **音量调节**: 使用音量滑块
- **屏幕查看**: 使用摄像头实体

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

## 📞 获取帮助

- 📖 详细文档: [README.md](README.md)
- 🐛 问题报告: [GitHub Issues](https://github.com/your-repo/android-tv-box/issues)
- 💬 社区讨论: [Home Assistant Community](https://community.home-assistant.io/)

---

**🎉 恭喜！您已成功部署Android TV Box Home Assistant集成！**

现在您可以：
- 通过Home Assistant控制您的Android TV盒子
- 创建自动化场景
- 监控设备状态
- 享受智能家居体验
