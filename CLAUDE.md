# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration that controls Android TV boxes through ADB (Android Debug Bridge). The integration runs in a specific environment: Home Assistant in an Ubuntu container (proot-distro) on Android Termux, controlling the local Android device via ADB.

## Commands

### Testing
```bash
# Test ADB connection
python3 test_adb_connection.py

# Test from Ubuntu container environment
source ~/uiauto_env/bin/activate
python3 test_adb_connection.py
```

### Deployment
```bash
# Deploy to Home Assistant
./deploy.sh

# Setup Android environment
./setup_android.sh

# Setup Ubuntu container environment
./setup_ubuntu.sh
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Check ADB connection manually
adb connect 127.0.0.1:5555
adb devices
```

## Architecture

### Environment Structure
- **Android Host**: Termux application with root access
- **Ubuntu Container**: proot-distro Ubuntu container within Termux
- **Home Assistant**: Runs inside Ubuntu container
- **ADB Connection**: 127.0.0.1:5555 (local TCP connection)

### Component Structure
```
custom_components/android_tv_box/
├── __init__.py              # Main component setup
├── manifest.json            # Integration metadata
├── config_flow.py          # Configuration UI flow
├── adb_service.py          # Core ADB connection service
├── media_player.py         # Media player entity
├── switch.py               # Power/WiFi switches
├── camera.py               # Screenshot camera entity
├── sensor.py               # Performance/status sensors
├── remote.py               # Remote control entity
├── select.py               # App selector entity
├── binary_sensor.py        # Binary status sensors
├── services.py             # Custom services
├── web_server.py           # Web management interface
├── helpers.py              # Utility functions
└── web/                    # Web interface assets
```

### Key Dependencies
- `uiautomator2>=2.16.23` - Android UI automation
- `aiohttp>=3.8.0` - Web server for management interface
- `paho-mqtt>=1.6.0` - MQTT support

### ADB Service Architecture
The `ADBService` class in `adb_service.py` handles all ADB operations:
- Connection management to 127.0.0.1:5555
- Command execution with error handling
- Rate limiting and connection recovery
- Shell command abstraction

### Entity Types
- **Media Player**: Playback control, volume, app launching
- **Switch**: Power on/off, WiFi enable/disable
- **Camera**: Screenshot capture with configurable intervals
- **Sensors**: CPU usage, memory, current app, network status
- **Remote**: Key commands (home, back, navigation, media controls)
- **Select**: App selector for one-click app launching
- **Binary Sensors**: Connection status, high CPU warnings

## Configuration

### Basic Configuration (configuration.yaml)
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

### Application Management
Apps are configured in configuration.yaml with package names:
```yaml
android_tv_box:
  apps:
    YouTube: com.google.android.youtube
    Netflix: com.netflix.mediaclient
    iSG: com.linknlink.app.device.isg
  visible:
    - YouTube
    - Netflix
    - iSG
```

### Web Management Interface
Available at `http://localhost:3003` when Home Assistant is running. Provides:
- Device status monitoring
- Application management
- Configuration updates
- Connection testing

## Development Notes

### ADB Connection Requirements
- Android device must be rooted
- ADB TCP service must be running on port 5555
- Connection is local only (127.0.0.1)

### Performance Considerations
- Screenshot intervals are configurable (default 3 seconds)
- Performance monitoring runs every 500ms by default
- CPU threshold monitoring with configurable alerts
- Command rate limiting in ADB service

### Error Handling
- ADB connection recovery mechanisms
- Graceful degradation when ADB unavailable
- Extensive logging for debugging

### Platform Integration
All entities support standard Home Assistant features:
- Device registry integration
- Entity registry integration
- Unique ID generation
- Icon and device class assignments