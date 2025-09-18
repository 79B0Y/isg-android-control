# HACS 安装指南

## 🏪 通过 HACS 安装 Android TV Box Integration

### 前置条件

1. **已安装 HACS**
   - 确保您的 Home Assistant 已安装 HACS (Home Assistant Community Store)
   - 如果未安装，请参考 [HACS 官方安装指南](https://hacs.xyz/docs/installation/installation/)

2. **Android 设备准备**
   - Android 设备已 root
   - 已安装 Termux 应用
   - 已安装 Home Assistant（在 Ubuntu 容器中）

### 安装步骤

#### 方法 1: 通过 HACS 界面安装

1. **打开 HACS**
   - 在 Home Assistant 侧边栏中点击 "HACS"
   - 选择 "Integrations"

2. **添加自定义仓库**
   - 点击右上角的三个点菜单
   - 选择 "Custom repositories"
   - 在 "Repository" 字段输入: `https://github.com/your-username/android-tv-box`
   - 在 "Category" 下拉菜单中选择: `Integration`
   - 点击 "Add"

3. **安装集成**
   - 在 HACS 集成页面搜索 "Android TV Box"
   - 点击 "Android TV Box" 集成
   - 点击 "Download" 按钮
   - 等待下载完成

4. **重启 Home Assistant**
   - 下载完成后，重启 Home Assistant
   - 可以通过 "设置" → "系统" → "重启" 或使用开发者工具

#### 方法 2: 通过 HACS 命令行安装

如果您更喜欢使用命令行：

```bash
# 在 Home Assistant 容器中
cd /config/custom_components
git clone https://github.com/your-username/android-tv-box.git android_tv_box
```

### 配置集成

1. **添加集成**
   - 重启后，进入 "设置" → "设备与服务"
   - 点击 "添加集成"
   - 搜索 "Android TV Box"
   - 点击选择

2. **配置参数**
   - **主机地址**: `127.0.0.1` (默认)
   - **端口**: `5555` (默认)
   - **设备名称**: `Android TV Box` (可自定义)
   - **截图路径**: `/sdcard/isgbackup/screenshot/` (可自定义)
   - **其他设置**: 根据需要调整

3. **完成配置**
   - 点击 "提交" 完成配置
   - 集成将自动创建所有实体

### 验证安装

1. **检查实体**
   - 进入 "设置" → "实体注册表"
   - 搜索 "android_tv_box"
   - 确认所有实体都已创建

2. **测试功能**
   - 检查媒体播放器实体
   - 测试开关控制
   - 查看传感器数据
   - 测试遥控器功能

### 更新集成

通过 HACS 更新非常简单：

1. **检查更新**
   - 打开 HACS
   - 进入 "Integrations"
   - 找到 "Android TV Box"
   - 如果有更新，会显示更新按钮

2. **执行更新**
   - 点击 "Update" 按钮
   - 等待更新完成
   - 重启 Home Assistant

### 卸载集成

如果需要卸载：

1. **通过 HACS 卸载**
   - 在 HACS 中找到 "Android TV Box"
   - 点击 "Remove" 按钮
   - 确认删除

2. **清理配置**
   - 删除 `configuration.yaml` 中的相关配置
   - 重启 Home Assistant

### 故障排除

#### 常见问题

1. **HACS 中找不到集成**
   - 确认仓库 URL 正确
   - 检查网络连接
   - 尝试刷新 HACS 缓存

2. **下载失败**
   - 检查网络连接
   - 确认 GitHub 仓库可访问
   - 尝试手动下载

3. **配置失败**
   - 检查 ADB 连接
   - 确认 Android 设备设置正确
   - 查看 Home Assistant 日志

#### 获取帮助

- **GitHub Issues**: [https://github.com/your-username/android-tv-box/issues](https://github.com/your-username/android-tv-box/issues)
- **HACS 文档**: [https://hacs.xyz/docs/](https://hacs.xyz/docs/)
- **Home Assistant 社区**: [https://community.home-assistant.io/](https://community.home-assistant.io/)

### 注意事项

1. **版本兼容性**
   - 确保 Home Assistant 版本 >= 2023.1.0
   - 检查 HACS 版本是否最新

2. **依赖安装**
   - 集成会自动安装所需依赖
   - 如果遇到依赖问题，请检查 Python 环境

3. **权限设置**
   - 确保 Home Assistant 有足够权限
   - 检查文件系统权限

### 高级配置

#### 自定义配置

您可以在 `configuration.yaml` 中添加高级配置：

```yaml
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  device_name: "My Android TV Box"
  screenshot_path: "/sdcard/screenshots/"
  screenshot_keep_count: 5
  screenshot_interval: 5
  performance_check_interval: 300
  cpu_threshold: 60
  apps:
    Netflix: com.netflix.mediaclient
    YouTube: com.google.android.youtube
    Spotify: com.spotify.music
  visible:
    - Netflix
    - YouTube
    - Spotify
  isg_monitoring: true
  isg_check_interval: 30
```

#### 自动化示例

```yaml
automation:
  - alias: "Android TV Box 自动启动 iSG"
    trigger:
      - platform: state
        entity_id: binary_sensor.android_tv_box_isg_running
        to: 'off'
    action:
      - service: android_tv_box.wake_isg
```

---

## 🎉 完成！

现在您已经成功通过 HACS 安装了 Android TV Box Integration！

- ✅ 集成已安装
- ✅ 实体已创建
- ✅ 功能已就绪
- ✅ 可以开始使用

享受您的智能 Android TV Box 控制体验！
