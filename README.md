# Android TV Box Integration

[![hacs][hacsbadge]][hacs]
![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1.0+-green.svg)
![Maintenance](https://img.shields.io/badge/Maintainer-@bobo-orange.svg)

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg

The Android TV Box integration allows you to control and monitor your Android TV Box through Home Assistant using ADB (Android Debug Bridge) commands. It provides comprehensive control over media playback, system settings, device monitoring, and remote control functionality.

## 🚀 Features

### 📺 Media Player Entity
- **Playback Control**: Play, pause, stop, next, previous, seek
- **Volume Control**: Set volume level, mute/unmute, volume up/down
- **App Launch**: Launch Android applications directly
- **Status Monitoring**: Real-time display of current app, volume level, and power state

### 🔌 Switch Entities
- **Power Switch**: Turn device on/off remotely
- **WiFi Switch**: Enable/disable WiFi connectivity
- **Status Feedback**: Real-time status updates and control

### 📷 Camera Entity
- **Screen Capture**: Automatic screenshot capture with configurable intervals
- **Image Storage**: Smart storage management with timestamp naming
- **Live View**: View device screen directly in Home Assistant
- **Storage Management**: Automatic cleanup of old screenshots

### 📊 Sensor Entities
- **Performance Monitoring**: CPU usage, memory usage, and system performance
- **Network Status**: WiFi connection status and network information
- **Application Status**: Current foreground application monitoring
- **Device Information**: Device model, Android version, and system details
- **High CPU Warning**: Alerts when CPU usage exceeds threshold

### 🎯 Remote Control Entity
- **Key Commands**: Send various key commands (home, back, menu, etc.)
- **Navigation Control**: Direction keys, confirm, return, and navigation
- **Media Control**: Playback control keys and media navigation
- **System Control**: Home, menu, power, and system-level controls

### 📱 Application Selector
- **App Management**: Configure and manage Android applications
- **One-Click Launch**: Select and launch applications instantly
- **Status Sync**: Real-time display of currently running application
- **Customizable List**: Add, edit, and remove applications as needed

### 🔍 iSG Monitoring
- **Process Monitoring**: Continuous monitoring of iSG application status
- **Auto-Wake**: Automatically wake up iSG when it stops running
- **Status Reporting**: Real-time status feedback and alerts
- **Configurable Intervals**: Customizable check intervals

## 🌐 Web Management Interface

Access the web management interface at `http://localhost:3003` for easy configuration and monitoring:

### Dashboard
- **Device Status**: ADB connection, power state, WiFi status
- **Current Application**: Real-time display of running app
- **iSG Status**: iSG application monitoring status
- **Live Updates**: Automatic status refresh

### Application Management
- **Add Applications**: Add new apps with name and package name
- **Edit Applications**: Modify existing application settings
- **Delete Applications**: Remove unwanted applications
- **Visibility Control**: Control which apps appear in the selector

### Configuration Management
- **ADB Settings**: Host address, port configuration
- **Home Assistant Settings**: HA server configuration
- **Screenshot Settings**: Path, keep count, interval settings
- **iSG Monitoring**: Enable/disable monitoring and set intervals
- **Connection Testing**: Test ADB and MQTT connections

### MQTT Configuration
- **MQTT Broker**: Server address and port settings
- **Authentication**: Username and password configuration
- **Topic Settings**: Base topic and QoS configuration
- **Connection Testing**: Test MQTT broker connectivity

## 📋 Supported Devices

The following Android devices are supported:
- **Android TV Boxes**: All Android TV boxes with ADB enabled
- **Android Phones**: Rooted Android phones and tablets
- **Android Tablets**: Rooted Android tablets
- **Android Set-Top Boxes**: Various Android-based set-top boxes

## ⚙️ Configuration

### Basic Configuration

```yaml
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  name: "Android TV Box"
  screenshot_path: "/sdcard/isgbackup/screenshot/"
  screenshot_keep_count: 3
  screenshot_interval: 3
  performance_check_interval: 500
  cpu_threshold: 50
  termux_mode: true
  ubuntu_venv_path: "~/uiauto_env"
  adb_path: "/usr/bin/adb"
```

> **Note:** Older configuration examples may use `device_name`. The integration still accepts this alias for backward compatibility, but new setups should prefer the standard Home Assistant `name` field.

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

### Entity Configuration

You can disable specific entity types:

```yaml
android_tv_box:
  media_player: true
  switch: true
  camera: true
  sensor: true
  remote: true
  select: true
  binary_sensor: true
```

## 🚀 Installation

### Method 1: HACS (Recommended)

1. **Install HACS** (if not already installed)
   - Follow the [HACS installation guide](https://hacs.xyz/docs/installation/installation/)

2. **Add Custom Repository**
   - Open HACS → Integrations
   - Click the three dots menu → Custom repositories
   - Add repository: `https://github.com/bobo/android-tv-box`
   - Category: Integration

3. **Install Integration**
   - Search for "Android TV Box"
   - Click Download
   - Restart Home Assistant

4. **Configure Integration**
   - Go to Settings → Devices & Services
   - Click Add Integration
   - Search for "Android TV Box" and configure

### Method 2: Manual Installation

1. **Download the integration**
   ```bash
   cd /config/custom_components
   git clone https://github.com/bobo/android-tv-box.git android_tv_box
   ```

2. **Restart Home Assistant**

3. **Add the integration** through the UI

## 🔧 Prerequisites

### Android Device Setup
- **Root Access**: Android device must be rooted
- **ADB Enabled**: Enable Developer Options and USB Debugging
- **Termux**: Install Termux application
- **Network Access**: Ensure network connectivity

### Home Assistant Environment
- **Home Assistant**: Version 2023.1.0 or higher
- **Ubuntu Container**: Home Assistant running in Ubuntu container (proot-distro)
- **Python Dependencies**: Automatically installed via integration

## 📖 Usage Examples

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

### Service Calls

```yaml
# Custom services
service: android_tv_box.take_screenshot
service: android_tv_box.launch_app
data:
  package_name: "com.netflix.mediaclient"

service: android_tv_box.set_brightness
data:
  brightness: 50

service: android_tv_box.set_volume
data:
  volume: 75

service: android_tv_box.wake_isg
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

- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)
- **HACS Installation**: [HACS_INSTALLATION.md](HACS_INSTALLATION.md)
- **Web Interface Guide**: [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)
- **New Features**: [NEW_FEATURES.md](NEW_FEATURES.md)
- **Project Overview**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **GitHub Issues**: [Report bugs and request features](https://github.com/bobo/android-tv-box/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/bobo/android-tv-box/discussions)
- **Home Assistant Community**: [HA Community Forum](https://community.home-assistant.io/)

### FAQ

**Q: Can I use this with non-rooted Android devices?**
A: No, root access is required for ADB functionality and system-level control.

**Q: Does this work with Android TV?**
A: Yes, it works with Android TV boxes and Android TV devices.

**Q: Can I control multiple Android devices?**
A: Currently, the integration supports one device per instance. Multiple instances can be configured for multiple devices.

**Q: Is the web interface secure?**
A: The web interface runs locally and should not be exposed to the internet without proper security measures.

## 🎉 Acknowledgments

- Home Assistant community for the excellent platform
- HACS for making custom integrations accessible
- Android developers for ADB tools
- All contributors and users who help improve this integration

---

**Made with ❤️ for the Home Assistant community**
