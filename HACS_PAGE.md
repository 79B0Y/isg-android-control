# Android TV Box Integration

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1.0+-green.svg)
![Maintenance](https://img.shields.io/badge/Maintainer-@your-username-orange.svg)

## 📱 Control Your Android TV Box with Home Assistant

The Android TV Box integration allows you to control and monitor your Android TV Box through Home Assistant using ADB (Android Debug Bridge) commands. It provides comprehensive control over media playback, system settings, device monitoring, and remote control functionality.

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

## 🚀 Quick Installation

### Prerequisites
- Android device with root access
- Termux application installed
- Home Assistant running in Ubuntu container

### HACS Installation
1. Add custom repository: `https://github.com/your-username/android-tv-box`
2. Search for "Android TV Box" in HACS
3. Click Download and restart Home Assistant
4. Add integration through Settings → Devices & Services

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

## ⚙️ Configuration

### Basic Configuration
```yaml
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  device_name: "Android TV Box"
  screenshot_path: "/sdcard/isgbackup/screenshot/"
  screenshot_keep_count: 3
  screenshot_interval: 3
  performance_check_interval: 500
  cpu_threshold: 50
  termux_mode: true
  ubuntu_venv_path: "~/uiauto_env"
  adb_path: "/usr/bin/adb"
```

### Application Configuration
```yaml
android_tv_box:
  apps:
    YouTube: com.google.android.youtube
    Netflix: com.netflix.mediaclient
    Spotify: com.spotify.music
    iSG: com.linknlink.app.device.isg
    # Add more apps as needed
  
  visible:
    - YouTube
    - Netflix
    - Spotify
    - iSG
```

### iSG Monitoring Configuration
```yaml
android_tv_box:
  isg_monitoring: true
  isg_check_interval: 30  # seconds
```

## 🎯 Usage Examples

### Basic Control
```yaml
# Turn on device
service: switch.turn_on
target:
  entity_id: switch.android_tv_box_power

# Launch YouTube
service: select.select_option
target:
  entity_id: select.android_tv_box_app_selector
data:
  option: "YouTube"

# Take screenshot
service: camera.snapshot
target:
  entity_id: camera.android_tv_box_screenshot
```

### Automation Examples
```yaml
# Auto-launch iSG when device turns on
automation:
  - alias: "Launch iSG on device start"
    trigger:
      - platform: state
        entity_id: switch.android_tv_box_power
        to: 'on'
    action:
      - delay: '00:00:10'  # Wait for device to boot
      - service: select.select_option
        target:
          entity_id: select.android_tv_box_app_selector
        data:
          option: "iSG"

# Monitor high CPU usage
automation:
  - alias: "High CPU Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.android_tv_box_cpu_usage
        above: 80
    action:
      - service: notify.persistent_notification
        data:
          message: "Android TV Box CPU usage is high: {{ states('sensor.android_tv_box_cpu_usage') }}%"
```

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

# Set volume
service: android_tv_box.set_volume
data:
  volume: 75

# Wake iSG application
service: android_tv_box.wake_isg

# Restart iSG application
service: android_tv_box.restart_isg
```

## 🛠️ Troubleshooting

### Common Issues

#### ADB Connection Failed
```bash
# Check ADB service status
adb devices

# Restart ADB service
adb kill-server
adb start-server
adb connect 127.0.0.1:5555
```

#### Home Assistant Cannot Start
```bash
# Check configuration
hass --script check_config

# View logs
tail -f /root/.homeassistant/home-assistant.log
```

#### Web Interface Not Accessible
- Check if port 3003 is available
- Verify firewall settings
- Check Home Assistant logs for errors

#### iSG Monitoring Not Working
- Verify iSG package name is correct
- Check ADB connection status
- Review sensor status in Home Assistant

### Debug Mode
Enable debug logging in `configuration.yaml`:
```yaml
logger:
  default: info
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

- **GitHub Issues**: [Report bugs and request features](https://github.com/your-username/android-tv-box/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/your-username/android-tv-box/discussions)
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
