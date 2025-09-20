# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration that controls Android TV boxes through ADB (Android Debug Bridge). The integration runs in a specific environment: Home Assistant in an Ubuntu container (proot-distro) on Android Termux, controlling the local Android device via ADB.

## Commands

### Setup and Deployment
```bash
# Initial Android setup (run on Termux as root)
./setup_android.sh

# Ubuntu container setup (run in proot-distro Ubuntu)
./setup_ubuntu.sh

# Deploy integration to Home Assistant
./deploy.sh

# Prepare release for HACS
./release.sh
```

### Testing
```bash
# Comprehensive ADB connection test
python3 test_adb_connection.py

# Test from Ubuntu container environment
source ~/uiauto_env/bin/activate
python3 test_adb_connection.py
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Manual ADB connection check
adb connect 127.0.0.1:5555
adb devices

# Check Home Assistant container status
docker ps | grep homeassistant

# View Home Assistant logs
docker logs homeassistant -f
```

## Architecture

### Environment Structure
- **Android Host**: Termux application with root access
- **Ubuntu Container**: proot-distro Ubuntu container within Termux (alternative deployment)
- **Home Assistant**: Runs in Docker container (current setup) or Ubuntu container
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
- `aiohttp-cors>=0.7.0` - CORS support for web interface
- `paho-mqtt>=1.6.0` - MQTT support
- `voluptuous>=0.13.0` - Configuration validation

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

## Development Workflow

### Initial Setup Process
1. Run `./setup_android.sh` on Termux (requires root)
2. Install Ubuntu container or ensure Docker is available
3. Run `./setup_ubuntu.sh` in Ubuntu container (if using container deployment)
4. Deploy integration using `./deploy.sh`
5. Test connection with `python3 test_adb_connection.py`

### Configuration Flow
- Integration supports both UI configuration (config_flow.py) and configuration.yaml
- Auto-imports from configuration.yaml on first setup
- Web management interface available at http://localhost:3003

### Release Process
- Update version in manifest.json
- Run `./release.sh` to validate and prepare release
- Create git tag and GitHub release for HACS distribution

## Development Notes

### Environment Requirements
- Android device with root access and ADB TCP service on port 5555
- Home Assistant running in Docker container or Ubuntu container
- Connection is local only (127.0.0.1)

### Performance Considerations
- Screenshot intervals configurable (default 3 seconds)
- Performance monitoring every 500ms with CPU threshold alerts
- Command rate limiting and connection recovery in ADB service

### Platform Integration
All entities support standard Home Assistant features:
- Device registry integration
- Entity registry integration
- Unique ID generation
- Icon and device class assignments