# Android TV Box Integration for Home Assistant

This integration allows you to control your Android TV Box through Home Assistant using ADB (Android Debug Bridge) commands. It provides comprehensive control over media playback, system settings, and device monitoring.

## Features

### Media Player Entity
- **Playback Control**: Play, pause, stop, next, previous
- **Volume Control**: Set volume level, mute/unmute, volume up/down
- **App Launch**: Launch Android applications
- **Status Monitoring**: Current app, volume level, power state

### Switch Entities
- **Power Switch**: Turn device on/off
- **WiFi Switch**: Enable/disable WiFi connectivity

### Camera Entity
- **Screen Capture**: Automatic screenshot capture every 3 seconds
- **Image Storage**: Keeps last 3 screenshots with timestamp naming
- **Live View**: View device screen in Home Assistant

### Sensor Entities
- **Brightness Sensor**: Current screen brightness level
- **WiFi SSID Sensor**: Connected WiFi network name
- **IP Address Sensor**: Device IP address
- **Current App Sensor**: Foreground application
- **CPU Usage Sensor**: System CPU utilization
- **Memory Usage Sensor**: RAM usage in MB
- **High CPU Warning Sensor**: Alerts when CPU usage exceeds threshold

### Remote Entity
- **Navigation Control**: Up, down, left, right, enter, back, home
- **Media Control**: Play, pause, stop, next, previous
- **Volume Control**: Volume up, down, mute
- **Power Control**: Power on/off

### Custom Services
- **Take Screenshot**: Manual screenshot capture
- **Launch App**: Start specific Android applications
- **Set Brightness**: Adjust screen brightness (0-255)
- **Set Volume**: Set volume level (0-100%)
- **Kill Process**: Terminate running processes
- **Wake iSG**: Wake up iSG application
- **Restart iSG**: Restart iSG application

### Web Management Interface
- **Port**: 3003 (accessible at http://localhost:3003)
- **Application Management**: Add, edit, delete applications
- **Configuration Management**: Configure ADB, Home Assistant, MQTT settings
- **Real-time Status**: Monitor device and iSG status
- **Connection Testing**: Test ADB and MQTT connections
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites

1. **Android Device with Root Access**
2. **Termux App** installed on Android
3. **Home Assistant** running in Ubuntu container via proot-distro

### Step 1: Android Setup (Termux)

```bash
# Install Android tools
pkg update
pkg install android-tools

# Exit termux user and configure ADB as root
exit
su
setprop service.adb.tcp.port 5555
stop adbd
start adbd
adb connect 127.0.0.1:5555
exit
```

### Step 2: Ubuntu Container Setup

```bash
# Install proot-distro and Ubuntu
pkg install proot-distro
proot-distro install ubuntu

# Enter Ubuntu container
proot-distro login ubuntu

# Install system dependencies
apt update && apt install -y \
  libxml2-dev libxslt1-dev python3-dev \
  build-essential python3-pip adb curl wget

# Create Python virtual environment
python3 -m venv ~/uiauto_env
source ~/uiauto_env/bin/activate
pip install --upgrade pip
pip install uiautomator2 homeassistant

# Test ADB connection
adb connect 127.0.0.1:5555
adb devices
```

### Step 3: Home Assistant Integration

1. Copy this integration to your Home Assistant custom components directory:
   ```bash
   cp -r custom_components/android_tv_box ~/.homeassistant/custom_components/
   ```

2. Add to your `configuration.yaml`:
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

3. Restart Home Assistant

## Configuration

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `host` | `127.0.0.1` | ADB host address |
| `port` | `5555` | ADB port |
| `device_name` | `Android TV Box` | Device name in Home Assistant |
| `screenshot_path` | `/sdcard/isgbackup/screenshot/` | Screenshot storage path |
| `screenshot_keep_count` | `3` | Number of screenshots to keep |
| `screenshot_interval` | `3` | Screenshot interval in seconds |
| `performance_check_interval` | `500` | Performance check interval in ms |
| `cpu_threshold` | `50` | CPU usage threshold for warnings |
| `termux_mode` | `true` | Enable Termux-specific optimizations |
| `ubuntu_venv_path` | `~/uiauto_env` | Python virtual environment path |
| `adb_path` | `/usr/bin/adb` | ADB binary path |
| `apps` | See below | Application configuration |
| `visible` | See below | Visible applications in select entity |
| `isg_monitoring` | `true` | Enable iSG monitoring |
| `isg_check_interval` | `30` | iSG check interval in seconds |

### Application Configuration

Configure available applications for the select entity:

```yaml
android_tv_box:
  # ... other options ...
  apps:
    Home Assistant: io.homeassistant.companion.android
    YouTube: com.google.android.youtube
    Spotify: com.spotify.music
    iSG: com.linknlink.app.device.isg
    # Add more apps as needed
  
  # Optional: limit the dropdown options shown in HA
  # If omitted or empty, all keys from 'apps' will be shown.
  visible:
    - Home Assistant
    - YouTube
    - Spotify
    - iSG
```

### Entity Configuration

You can disable specific entity types by setting them to `false`:

```yaml
android_tv_box:
  # ... other options ...
  media_player: true
  switch: true
  camera: true
  sensor: true
  remote: true
  select: true
  binary_sensor: true
```

## Usage

### Media Player Control

The media player entity provides standard Home Assistant media player controls:

- **Play/Pause**: Use the play/pause button in the media player card
- **Volume**: Adjust volume using the volume slider
- **App Launch**: Use the "Play Media" service to launch apps:
  ```yaml
  service: media_player.play_media
  target:
    entity_id: media_player.android_tv_box
  data:
    media_content_type: app
    media_content_id: com.example.app
  ```

### Switch Controls

- **Power Switch**: Turn the Android device on/off
- **WiFi Switch**: Enable/disable WiFi connectivity

### Camera View

The camera entity provides a live view of your Android device screen. Screenshots are automatically taken every 3 seconds and the last 3 images are kept.

### Sensor Monitoring

Monitor various aspects of your Android device:

- **Brightness**: Current screen brightness (0-255)
- **WiFi SSID**: Connected network name
- **IP Address**: Device IP address
- **Current App**: Foreground application package name
- **CPU Usage**: System CPU utilization percentage
- **Memory Usage**: RAM usage in MB
- **High CPU Warning**: Alerts when CPU usage exceeds threshold

### Remote Control

Use the remote entity to send key commands:

```yaml
service: remote.send_command
target:
  entity_id: remote.android_tv_box
data:
  command: ["up", "down", "left", "right", "enter"]
```

Available commands:
- Navigation: `up`, `down`, `left`, `right`, `enter`, `ok`, `back`, `home`
- Media: `play`, `pause`, `stop`, `next`, `previous`
- Volume: `volume_up`, `volume_down`, `volume_mute`
- Power: `power_on`, `power_off`

### App Selector

Use the select entity to launch applications:

```yaml
service: select.select_option
target:
  entity_id: select.android_tv_box_app_selector
data:
  option: "YouTube"
```

The select entity will show only the applications configured in the `visible` list.

### iSG Monitoring

The binary sensor monitors iSG application status:

- **iSG Running Sensor**: Shows if iSG is currently running
- **Auto Wake-up**: Automatically launches iSG if it's not running
- **Status Attributes**: Provides detailed monitoring information

Monitor iSG status:
```yaml
# Check iSG status
state: binary_sensor.android_tv_box_isg_running

# Attributes include:
# - wake_attempted: Whether auto wake-up was attempted
# - monitoring_enabled: Whether monitoring is enabled
# - check_interval: Monitoring check interval
```

### Custom Services

#### Take Screenshot
```yaml
service: android_tv_box.take_screenshot
data:
  filename: "custom_screenshot.png"  # Optional
  keep_count: 5  # Optional, default: 3
```

#### Launch App
```yaml
service: android_tv_box.launch_app
data:
  package_name: "com.example.app"
  activity_name: "com.example.app.MainActivity"  # Optional
```

#### Set Brightness
```yaml
service: android_tv_box.set_brightness
data:
  brightness: 128  # 0-255
```

#### Set Volume
```yaml
service: android_tv_box.set_volume
data:
  volume: 75  # 0-100%
```

#### Kill Process
```yaml
service: android_tv_box.kill_process
data:
  process_id: 1234
```

#### Wake iSG
```yaml
service: android_tv_box.wake_isg
```

#### Restart iSG
```yaml
service: android_tv_box.restart_isg
```

## Web Management Interface

### Accessing the Interface
1. **Start Home Assistant** with the Android TV Box integration
2. **Open browser** and navigate to `http://localhost:3003`
3. **Login** (if authentication is enabled)

### Dashboard Tab
- **Device Status**: Real-time power, WiFi, and app status
- **iSG Status**: Monitor iSG application state
- **Quick Actions**: Refresh status, wake iSG, restart iSG
- **Connection Status**: ADB connection indicator

### Apps Tab
- **View Applications**: See all configured applications
- **Add Applications**: Add new apps with name and package
- **Edit Applications**: Modify existing app configurations
- **Delete Applications**: Remove unwanted applications
- **Visibility Control**: Show/hide apps in Home Assistant

### Configuration Tab
- **ADB Connection**: Configure host, port, device name
- **Home Assistant**: Configure HA host, port, token
- **Screenshot Settings**: Configure screenshot path and intervals
- **iSG Monitoring**: Enable/disable monitoring and set intervals
- **Connection Testing**: Test ADB connection before saving

### MQTT Tab
- **Broker Configuration**: Set MQTT broker host, port, credentials
- **Topic Configuration**: Configure base topics and subtopics
- **Advanced Settings**: QoS, retain, keep-alive settings
- **Connection Testing**: Test MQTT connection

### Web Interface Features
- **Real-time Updates**: Status updates every 30 seconds
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Toast Notifications**: Success/error feedback for all actions
- **Modal Dialogs**: Clean interface for adding/editing apps
- **Loading Indicators**: Visual feedback during operations
- **Error Handling**: Graceful error handling with user feedback

## Troubleshooting

### ADB Connection Issues

1. **Check ADB service status**:
   ```bash
   adb devices
   ```

2. **Restart ADB service**:
   ```bash
   su
   stop adbd
   start adbd
   ```

3. **Check firewall settings** (if applicable)

### Permission Issues

1. **Ensure root access** for ADB configuration
2. **Check file permissions** for screenshot directory
3. **Verify ADB binary** is executable

### Performance Issues

1. **Adjust screenshot interval** if device is slow
2. **Reduce sensor update frequency** for better performance
3. **Monitor CPU usage** and adjust threshold if needed

### Common Error Messages

- **"Device not connected"**: Check ADB connection and restart service
- **"Command timeout"**: Increase timeout values or check device responsiveness
- **"Permission denied"**: Ensure proper root access and file permissions

## Advanced Configuration

### Custom ADB Commands

You can extend the integration by adding custom ADB commands in the `adb_service.py` file:

```python
async def custom_command(self, parameter: str) -> bool:
    """Custom ADB command."""
    try:
        await self.shell_command(f"your_custom_command {parameter}")
        return True
    except Exception as e:
        _LOGGER.error(f"Custom command failed: {e}")
        return False
```

### Automation Examples

#### Auto-adjust brightness based on time
```yaml
automation:
  - alias: "Adjust brightness for evening"
    trigger:
      platform: time
      at: "18:00:00"
    action:
      service: android_tv_box.set_brightness
      data:
        brightness: 100

  - alias: "Adjust brightness for night"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: android_tv_box.set_brightness
      data:
        brightness: 50
```

#### Monitor high CPU usage
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

## Security Considerations

- **Localhost Only**: ADB connection is restricted to localhost (127.0.0.1)
- **Container Isolation**: Ubuntu container provides additional security layer
- **Command Validation**: All ADB commands are validated before execution
- **Access Logging**: ADB operations are logged for monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Home Assistant logs
3. Create an issue on GitHub with detailed information

## Changelog

### Version 1.0.0
- Initial release
- Media player entity with full playback control
- Switch entities for power and WiFi
- Camera entity with automatic screenshots
- Comprehensive sensor monitoring
- Remote control entity
- Custom services for advanced control
- Termux/Ubuntu container support
