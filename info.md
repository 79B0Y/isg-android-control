# Android TV Box Integration

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1.0+-green.svg)
![Maintenance](https://img.shields.io/badge/Maintainer-@bobo-orange.svg)

## 📱 Control Your Android TV Box with Home Assistant

Transform your Android TV Box into a smart, controllable device through Home Assistant. This integration provides comprehensive control over media playback, system settings, device monitoring, and remote control functionality using ADB (Android Debug Bridge).

## ✨ Key Features

### 🎮 Complete Device Control
- **Media Player**: Full playback control with volume management
- **Power Management**: Remote power on/off and WiFi control
- **Screen Capture**: Live device screenshots with automatic storage
- **Remote Control**: Send any Android key commands
- **App Launcher**: One-click application launching
- **Performance Monitoring**: Real-time CPU, memory, and system stats

### 🔍 Smart Monitoring
- **iSG Watchdog**: Automatic monitoring and wake-up of iSG application
- **Performance Alerts**: High CPU usage notifications
- **Network Status**: WiFi connection monitoring
- **Application Tracking**: Current app detection and status

### 🌐 Web Management Interface
Access a beautiful web interface at `http://localhost:3003` for:
- **Dashboard**: Real-time device status and monitoring
- **App Management**: Add, edit, and configure applications
- **Settings**: Configure ADB, HA, and MQTT settings
- **Connection Testing**: Test ADB and MQTT connectivity

## 🚀 Quick Start

### Prerequisites
- Android device with root access
- Termux application installed
- Home Assistant running in Ubuntu container

### Installation via HACS
1. Add custom repository: `https://github.com/bobo/android-tv-box`
2. Search for "Android TV Box" in HACS
3. Click Download and restart Home Assistant
4. Add integration through Settings → Devices & Services

### Basic Configuration
```yaml
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  name: "Android TV Box"
  apps:
    YouTube: com.google.android.youtube
    Netflix: com.netflix.mediaclient
    iSG: com.linknlink.app.device.isg
  isg_monitoring: true
```

> 兼容性提示：旧版本配置中的 `device_name` 仍可使用，但建议改用标准的 `name` 字段。

## 📊 Supported Entities

| Entity Type | Description | Example |
|-------------|-------------|---------|
| **Media Player** | Playback control, volume, app launch | `media_player.android_tv_box` |
| **Switch** | Power and WiFi control | `switch.android_tv_box_power` |
| **Camera** | Live screenshots | `camera.android_tv_box_screenshot` |
| **Sensor** | Performance and status monitoring | `sensor.android_tv_box_cpu_usage` |
| **Remote** | Key command sending | `remote.android_tv_box_remote` |
| **Select** | Application launcher | `select.android_tv_box_app_selector` |
| **Binary Sensor** | iSG monitoring | `binary_sensor.android_tv_box_isg_running` |

## 🎯 Use Cases

### Smart Home Automation
- **Morning Routine**: Auto-launch news app when device turns on
- **Evening Control**: Dim screen and launch entertainment apps
- **Power Management**: Schedule device power on/off
- **Performance Monitoring**: Alert when device needs attention

### Media Control
- **Voice Control**: "Hey Google, play YouTube on Android TV Box"
- **Scene Control**: Create scenes for different viewing modes
- **Remote Management**: Control device from anywhere in your home
- **App Management**: Quick access to favorite applications

### Monitoring & Maintenance
- **Health Monitoring**: Track device performance over time
- **Automatic Recovery**: Auto-restart failed applications
- **Screenshot Logging**: Visual device status monitoring
- **Network Management**: Monitor and control WiFi connectivity

## 🔧 Advanced Features

### Custom Services
```yaml
# Take screenshot
service: android_tv_box.take_screenshot

# Launch specific app
service: android_tv_box.launch_app
data:
  package_name: "com.netflix.mediaclient"

# Set brightness
service: android_tv_box.set_brightness
data:
  brightness: 50

# Wake iSG application
service: android_tv_box.wake_isg
```

### Automation Examples
```yaml
# Auto-launch iSG when device starts
automation:
  - alias: "Launch iSG on startup"
    trigger:
      - platform: state
        entity_id: switch.android_tv_box_power
        to: 'on'
    action:
      - delay: '00:00:10'
      - service: select.select_option
        target:
          entity_id: select.android_tv_box_app_selector
        data:
          option: "iSG"

# High CPU alert
automation:
  - alias: "High CPU Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.android_tv_box_cpu_usage
        above: 80
    action:
      - service: notify.persistent_notification
        data:
          message: "Android TV Box CPU usage is high!"
```

## 🛠️ Troubleshooting

### Common Issues
- **ADB Connection**: Ensure ADB is enabled and device is rooted
- **Port Conflicts**: Check if port 5555 is available
- **Permission Issues**: Verify root access and file permissions
- **Network Problems**: Test network connectivity and firewall settings

### Debug Mode
Enable debug logging for troubleshooting:
```yaml
logger:
  logs:
    custom_components.android_tv_box: debug
```

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - 5-minute setup guide
- **[HACS Installation](HACS_INSTALLATION.md)** - Detailed HACS setup
- **[Web Interface Guide](WEB_INTERFACE_GUIDE.md)** - Web management interface
- **[New Features](NEW_FEATURES.md)** - Latest features and updates
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute

## 🤝 Community & Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/bobo/android-tv-box/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/bobo/android-tv-box/discussions)
- **Home Assistant Community**: [HA Community Forum](https://community.home-assistant.io/)

## 🎉 Why Choose This Integration?

### ✅ Comprehensive Control
- Complete device control through Home Assistant
- Real-time monitoring and status updates
- Automated maintenance and recovery

### ✅ Easy to Use
- Simple HACS installation
- Intuitive web management interface
- Clear documentation and examples

### ✅ Highly Configurable
- Customizable application lists
- Flexible monitoring settings
- Advanced automation capabilities

### ✅ Reliable & Stable
- Robust error handling
- Automatic reconnection
- Performance optimization

---

**Transform your Android TV Box into a smart, controllable device with Home Assistant!**

*Made with ❤️ for the Home Assistant community*
