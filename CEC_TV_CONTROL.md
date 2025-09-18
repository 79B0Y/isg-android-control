# CEC TV Control System

This document describes the CEC (Consumer Electronics Control) TV control system that allows your Android box in Termux to control your TV through HDMI-CEC with full Home Assistant integration.

## Overview

The CEC TV Control System provides:

- **Complete TV control** via HDMI-CEC from Termux/Ubuntu environment
- **Resource-optimized** design for minimal impact on Android box performance
- **Home Assistant integration** with auto-discovery of TV controls as Android TV device
- **Comprehensive API** for programmatic TV control
- **Multiple CEC backends** supporting cec-client, cec-ctl, and direct device access

## Features

### TV Control Functions
- **Power control**: On, Off, Toggle
- **Volume control**: Up, Down, Mute
- **Navigation**: Up, Down, Left, Right, Select, Back, Home, Menu
- **Input switching**: HDMI 1-4 selection
- **Device scanning**: Automatic detection of CEC devices
- **Status monitoring**: Real-time TV and CEC device status

### Home Assistant Integration
- **Media Player entity**: Full TV control in HA interface
- **Individual button entities**: Granular control buttons
- **Status sensors**: TV connection and device count sensors
- **Auto-discovery**: Automatic entity creation under "Android TV (CEC)" device
- **MQTT control**: Command TV via MQTT messages

## Architecture

### Core Components

#### CECController (`cec_controller.py`)
- **Lightweight CEC client wrapper** supporting multiple backends
- **Command queuing** with sequential execution to prevent conflicts
- **Device scanning** and status monitoring
- **Resource optimization** with connection caching and command batching

#### CECHAIntegration (`cec_ha.py`)
- **Home Assistant auto-discovery** for TV control entities
- **MQTT command handling** for TV control via HA
- **State publishing** for real-time status updates
- **Media player integration** with source selection

#### Monitor Service Integration
- **Unified monitoring** with performance, app watchdog, and CEC
- **Comprehensive metrics** including CEC status and TV information
- **API endpoints** for manual control and status checking

### Resource Optimization

**Termux-Friendly Design**:
- **Minimal CPU usage**: Async command processing with queuing
- **Low memory footprint**: Efficient caching and state management
- **Reduced I/O**: Batched commands with configurable delays
- **Connection management**: On-demand device access

**Performance Features**:
- **Command queuing**: Sequential execution prevents CEC conflicts
- **Cache management**: 30-second TTL for device information
- **Error handling**: Graceful degradation with fallback mechanisms
- **Background processing**: Non-blocking command execution

## Configuration

### CEC Backend Detection
The system automatically detects available CEC tools:

1. **cec-client** (preferred): Full-featured CEC control
2. **cec-ctl**: Kernel-based CEC interface
3. **Direct device access**: Via `/dev/cec*` devices
4. **Mock mode**: For testing without CEC hardware

### Installation Requirements

**For full CEC functionality, install CEC tools in the proot Ubuntu environment:**
```bash
# Option 1: Install cec-client (recommended)
sudo apt update
sudo apt install cec-utils libcec6

# Option 2: Use kernel CEC tools (if available)
sudo apt install v4l-utils  # Contains cec-ctl

# Option 3: Compile from source (if needed)
# git clone https://github.com/Pulse-Eight/libcec.git
# cd libcec && mkdir build && cd build
# cmake .. && make && sudo make install
```

**No additional configuration required** - the system auto-detects and configures CEC connectivity.

## API Endpoints

### CEC Status and Control
```bash
# Get CEC controller status
curl http://localhost:8000/cec/status

# Scan for CEC devices
curl http://localhost:8000/cec/devices

# Get available commands
curl http://localhost:8000/cec/commands

# Send custom CEC command
curl -X POST http://localhost:8000/cec/command/power_toggle
```

### TV Control Shortcuts
```bash
# Power control
curl -X POST http://localhost:8000/tv/power        # Toggle
curl -X POST http://localhost:8000/tv/power/on     # Turn on
curl -X POST http://localhost:8000/tv/power/off    # Turn off

# Volume control
curl -X POST http://localhost:8000/tv/volume/up
curl -X POST http://localhost:8000/tv/volume/down
curl -X POST http://localhost:8000/tv/volume/mute

# Navigation
curl -X POST http://localhost:8000/tv/nav/up
curl -X POST http://localhost:8000/tv/nav/down
curl -X POST http://localhost:8000/tv/nav/left
curl -X POST http://localhost:8000/tv/nav/right
curl -X POST http://localhost:8000/tv/select
curl -X POST http://localhost:8000/tv/back
curl -X POST http://localhost:8000/tv/home
curl -X POST http://localhost:8000/tv/menu

# Input switching
curl -X POST http://localhost:8000/tv/input/hdmi1
curl -X POST http://localhost:8000/tv/input/hdmi2
curl -X POST http://localhost:8000/tv/input/hdmi3
curl -X POST http://localhost:8000/tv/input/hdmi4
```

## Home Assistant Integration

### Automatic Discovery
When CEC is enabled, the following entities are automatically created in Home Assistant:

#### Media Player Entity
- **Entity ID**: `media_player.android_tv_cec`
- **Features**: Power, Volume, Source Selection
- **Device Class**: TV
- **Sources**: HDMI 1, HDMI 2, HDMI 3, HDMI 4

#### Button Entities
```yaml
# Power Controls
button.tv_power_toggle
button.tv_power_on
button.tv_power_off

# Volume Controls
button.tv_volume_up
button.tv_volume_down
button.tv_mute

# Navigation Controls
button.tv_navigate_up
button.tv_navigate_down
button.tv_navigate_left
button.tv_navigate_right
button.tv_select_ok
button.tv_back
button.tv_home
button.tv_menu

# Input Controls
button.tv_hdmi_1
button.tv_hdmi_2
button.tv_hdmi_3
button.tv_hdmi_4
```

#### Sensor Entities
```yaml
# Status Sensors
sensor.tv_cec_status      # Connection status
sensor.cec_devices_count  # Number of detected devices
```

### MQTT Topics

#### Command Topics
```bash
# Media player commands
isg/android/cec/tv/command
  - Payloads: turn_on, turn_off, volume_up, volume_down, volume_mute

# Source selection
isg/android/cec/tv/select_source
  - Payloads: "HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"

# Individual button commands
isg/android/cec/button/{button_name}
  - Examples: isg/android/cec/button/power_toggle
```

#### State Topics
```bash
# TV state
isg/android/cec/tv/state
  - JSON: {"state": "on", "source": "HDMI 1", ...}

# Sensor states
isg/android/cec/sensor/tv_status
isg/android/cec/sensor/cec_devices

# Availability
isg/android/cec/availability
  - Payloads: online, offline
```

### Home Assistant Configuration

**No manual configuration required!** Entities are auto-discovered.

**Optional**: Create dashboard cards:
```yaml
# Example Lovelace card for TV control
type: entities
title: TV Control
entities:
  - media_player.android_tv_cec
  - button.tv_power_toggle
  - button.tv_volume_up
  - button.tv_volume_down
  - button.tv_mute
  - sensor.tv_cec_status
```

## CEC Commands Reference

### Power Commands
```python
'power_on': '04'        # Turn device on
'power_off': '36'       # Turn device off
'power_toggle': '6B'    # Toggle power state
```

### Navigation Commands
```python
'up': '44 01'           # Navigate up
'down': '44 02'         # Navigate down
'left': '44 03'         # Navigate left
'right': '44 04'        # Navigate right
'select': '44 00'       # Select/OK button
'back': '44 0D'         # Back button
'home': '44 09'         # Home button
'menu': '44 09'         # Menu button
```

### Volume Commands
```python
'volume_up': '44 41'    # Volume up
'volume_down': '44 42'  # Volume down
'mute': '44 43'         # Mute toggle
```

### Input Commands
```python
'input_hdmi1': '82 10 00'  # Switch to HDMI 1
'input_hdmi2': '82 20 00'  # Switch to HDMI 2
'input_hdmi3': '82 30 00'  # Switch to HDMI 3
'input_hdmi4': '82 40 00'  # Switch to HDMI 4
```

## Troubleshooting

### CEC Not Working

#### Check CEC Hardware
```bash
# Verify CEC devices
ls -la /dev/cec*

# Check for CEC tools
which cec-client
which cec-ctl
```

#### Check TV Settings
1. **Enable CEC on TV**: Usually in Settings → General → External Device Manager
2. **Enable HDMI Control**: May be called "Anynet+", "Bravia Sync", "Simplink", etc.
3. **Set device name**: Configure Android box name in TV CEC settings

#### Check Connection
```bash
# Test CEC status
curl http://localhost:8000/cec/status

# Scan for devices
curl http://localhost:8000/cec/devices

# Check logs
tail -f var/log/isg-android-control.log | grep -i cec
```

### Common Issues

#### No CEC Devices Found
- **Check HDMI connection**: Ensure Android box is connected via HDMI
- **Verify CEC support**: Not all HDMI ports support CEC
- **TV compatibility**: Some older TVs have limited CEC support
- **Cable quality**: Poor HDMI cables may not carry CEC signals

#### Commands Not Working
- **Command conflicts**: CEC commands are queued to prevent conflicts
- **TV responsiveness**: Some TVs respond slowly to CEC commands
- **Device addressing**: Verify TV is detected as device 0

#### Home Assistant Integration Issues
```bash
# Check MQTT connectivity
curl http://localhost:8000/cec/status

# Verify discovery publication
# Look for entities in HA Developer Tools → States
# Filter by "android_tv_cec" or "tv_"

# Check MQTT logs
tail -f var/log/isg-android-control.log | grep -i mqtt
```

### Performance Optimization

#### For Low-Resource Systems
```python
# Adjust CEC controller settings
CECController(
    physical_address="1.0.0.0",
    device_name="ISG Android Controller"
)

# Reduce command frequency if needed
# Commands are automatically queued with 100ms delay
```

#### Monitor Resource Usage
```bash
# Check CPU usage
curl http://localhost:8000/performance

# Monitor memory
curl http://localhost:8000/system

# CEC-specific status
curl http://localhost:8000/cec/status
```

## Advanced Usage

### Custom CEC Commands
```bash
# Send raw CEC command
curl -X POST http://localhost:8000/cec/command/custom \
  -H "Content-Type: application/json" \
  -d '{"code": "44 09", "target": "0"}'
```

### Integration Examples

#### Home Assistant Automation
```yaml
# Turn on TV when Android box wakes up
automation:
  - alias: "Turn on TV with Android Box"
    trigger:
      platform: state
      entity_id: media_player.android_tv_cec
      to: 'on'
    action:
      service: media_player.turn_on
      entity_id: media_player.android_tv_cec
```

#### Python Script
```python
import requests

# Control TV via API
def control_tv(action):
    response = requests.post(f"http://localhost:8000/tv/{action}")
    return response.json()

# Examples
control_tv("power/on")
control_tv("volume/up")
control_tv("input/hdmi2")
```

## Development and Customization

### Adding New Commands
Edit `cec_controller.py` to add new CEC commands:

```python
# Add to CEC_COMMANDS dictionary
'custom_command': CECCommand('custom_command', 'XX YY', 'Description', '0')
```

### Extending HA Integration
Modify `cec_ha.py` to add new entity types or customize discovery.

### Performance Monitoring
The CEC system integrates with existing performance monitoring:

```bash
# Get comprehensive metrics including CEC
curl http://localhost:8000/metrics

# Response includes:
# - cec: CEC controller status
# - performance: System performance
# - adb: Android device metrics
```

## Security Considerations

1. **Network access**: API endpoints are available on the local network
2. **MQTT security**: Use MQTT authentication if needed
3. **CEC limitations**: CEC control is limited to connected devices
4. **Resource limits**: Command queuing prevents system overload

## Future Enhancements

Potential improvements:
- **Advanced CEC features**: Audio return channel (ARC) support
- **Multi-device control**: Support for multiple HDMI-CEC devices
- **Custom sequences**: Macro commands for complex operations
- **Enhanced discovery**: Better device type detection and naming
- **Voice control**: Integration with voice assistants
- **Mobile app**: Direct control from mobile devices