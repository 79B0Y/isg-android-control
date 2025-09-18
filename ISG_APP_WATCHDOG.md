# ISG App Watchdog System

This document describes the ISG app monitoring and auto-restart system that ensures the `com.linknlink.app.device.isg` application is always running on the Android device.

## Overview

The ISG App Watchdog provides:

- **Periodic monitoring**: Checks if ISG app is running every 5 minutes
- **Automatic restart**: Restarts the app if it's not detected running
- **Smart retry logic**: Multiple restart attempts with delays
- **Health monitoring**: Detailed app status and memory usage tracking
- **Manual control**: API endpoints for manual restart and monitoring control

## Key Features

### 1. Efficient Process Detection
- Uses `adb shell ps -A` command for fast process checking
- Verifies actual process name to avoid false positives
- Minimal resource usage with targeted monitoring

### 2. Intelligent Restart Strategy
```python
# Restart process:
1. Force-stop the app: am force-stop com.linknlink.app.device.isg
2. Wait 2 seconds for complete shutdown
3. Launch app: monkey -p com.linknlink.app.device.isg -c android.intent.category.LAUNCHER 1
4. Verify the app actually started
```

### 3. Configuration
- **Check interval**: 300 seconds (5 minutes)
- **Restart attempts**: 3 attempts per detection cycle
- **Restart delay**: 10 seconds between attempts
- **Cooldown period**: 2 minutes minimum between restart cycles

## Architecture

### Core Components

#### AppWatchdog Class (`app_watchdog.py`)
- **Generic app monitoring framework**
- Supports multiple target packages
- Configurable check intervals and retry logic
- Extensible for monitoring other critical apps

#### ISGAppWatchdog Class
- **Specialized for ISG app monitoring**
- Predefined configuration optimized for ISG app
- Extended health checking with memory usage
- ISG-specific restart verification

#### MonitorService Integration
- **Seamless integration** with existing monitoring infrastructure
- Combined metrics with performance and system monitoring
- Automatic startup/shutdown with main application

### Data Flow
1. **Startup**: Watchdog starts automatically with the main application
2. **Monitoring Loop**: Every 5 minutes, check if ISG app is running
3. **Detection**: Use ADB `ps` command to verify process existence
4. **Restart Logic**: If not running, attempt restart with retries
5. **Verification**: Confirm app successfully restarted
6. **Metrics**: Update restart counts and failure tracking

## Configuration

### Default Settings
```python
ISGAppWatchdog(
    target_packages={"com.linknlink.app.device.isg"},
    check_interval=300.0,  # 5 minutes
    restart_attempts=3,
    restart_delay=10.0     # 10 seconds between attempts
)
```

### Environment Variables
No additional environment variables required. The watchdog uses existing ADB configuration.

## API Endpoints

### Monitoring Status
```bash
# Get watchdog status and ISG app health
curl http://localhost:8000/watchdog/status

# Response:
{
  "monitoring": true,
  "check_interval": 300.0,
  "target_packages": ["com.linknlink.app.device.isg"],
  "restart_counts": {"com.linknlink.app.device.isg": 2},
  "last_restart_times": {"com.linknlink.app.device.isg": "2025-09-18T01:23:45.123456"},
  "consecutive_failures": {"com.linknlink.app.device.isg": 0},
  "isg_app_health": {
    "package": "com.linknlink.app.device.isg",
    "is_running": true,
    "restart_count": 2,
    "is_foreground": false,
    "memory_mb": "145"
  }
}
```

### ISG App Status
```bash
# Get detailed ISG app information
curl http://localhost:8000/watchdog/isg

# Response:
{
  "package": "com.linknlink.app.device.isg",
  "is_running": true,
  "restart_count": 2,
  "last_restart": "2025-09-18T01:23:45.123456",
  "consecutive_failures": 0,
  "is_foreground": false,
  "memory_mb": "145"
}
```

### Manual Control
```bash
# Manually restart ISG app
curl -X POST http://localhost:8000/watchdog/isg/restart

# Start/stop watchdog monitoring
curl -X POST http://localhost:8000/watchdog/start
curl -X POST http://localhost:8000/watchdog/stop

# Check overall monitoring status
curl http://localhost:8000/metrics
```

## Integration with Existing Systems

### Monitor Service Integration
The watchdog is seamlessly integrated with the existing `MonitorService`:

```python
# Automatic startup
monitor = MonitorService(adb, enable_app_watchdog=True)
await monitor.start_app_watchdog()

# Comprehensive metrics
metrics = await monitor.snapshot()
# Contains: adb, performance, system, app_watchdog, isg_app sections
```

### MQTT/Home Assistant Integration
ISG app status can be published to Home Assistant via MQTT:

```python
# App health data available in metrics
isg_status = metrics['isg_app']
is_running = isg_status['is_running']
restart_count = isg_status['restart_count']
```

## Restart Logic and Error Handling

### Process Detection
```python
async def check_app_running(package: str) -> bool:
    # Use 'ps -A' for comprehensive process list
    output = await adb._run("shell", "ps", "-A")

    # Parse process list looking for exact package match
    for line in output.split('\n'):
        if package in line:
            parts = line.split()
            process_name = parts[8]  # COMMAND column
            if process_name == package or process_name.endswith(f":{package}"):
                return True
    return False
```

### Restart Process
```python
async def restart_app(package: str) -> bool:
    # 1. Force stop the app
    await adb._run("shell", "am", "force-stop", package)
    await asyncio.sleep(2.0)  # Wait for shutdown

    # 2. Launch using monkey (more reliable than am start)
    await adb._run("shell", "monkey", "-p", package,
                   "-c", "android.intent.category.LAUNCHER", "1")

    # 3. Verify restart
    await asyncio.sleep(5.0)
    return await check_app_running(package)
```

### Error Handling
- **ADB Connection Failures**: Graceful handling with logging
- **App Launch Failures**: Multiple retry attempts with exponential backoff
- **Consecutive Failures**: Tracking and alerting for persistent issues
- **Cooldown Logic**: Prevents excessive restart attempts

## Monitoring and Alerting

### Restart Tracking
- **Restart counts**: Total number of restarts per app
- **Last restart time**: Timestamp of most recent restart
- **Consecutive failures**: Count of failed restart attempts
- **Success rate**: Historical restart success metrics

### Health Metrics
```python
{
  "package": "com.linknlink.app.device.isg",
  "is_running": true,
  "restart_count": 5,
  "last_restart": "2025-09-18T01:23:45.123456",
  "consecutive_failures": 0,
  "is_foreground": false,  # Whether app is in foreground
  "memory_mb": "145"       # Memory usage in MB
}
```

### Logging
```
INFO: Starting app watchdog (interval=5.0min, packages=['com.linknlink.app.device.isg'])
WARNING: App com.linknlink.app.device.isg is not running, attempting restart
INFO: Successfully restarted app: com.linknlink.app.device.isg
INFO: App com.linknlink.app.device.isg successfully restarted and verified running
ERROR: Failed to restart app com.linknlink.app.device.isg after 3 attempts
```

## Performance Impact

### Resource Usage
- **CPU**: Minimal impact with 5-minute intervals
- **Memory**: <1MB additional memory usage
- **Network**: Uses existing ADB connection (on-demand)
- **Battery**: Negligible impact on device battery

### Optimization Features
- **On-demand ADB**: Leverages optimized connection management
- **Efficient commands**: Uses lightweight `ps` instead of heavy dumpsys
- **Smart intervals**: 5-minute checks balance responsiveness vs. efficiency
- **Failure backoff**: Reduces checking frequency during persistent failures

## Troubleshooting

### Common Issues

#### App Not Detected Running
```bash
# Check if package name is correct
curl http://localhost:8000/watchdog/isg

# Verify ADB connection
curl http://localhost:8000/adb/status

# Check logs
curl http://localhost:8000/logs
```

#### Restart Failures
```bash
# Manual restart test
curl -X POST http://localhost:8000/watchdog/isg/restart

# Check app installation
curl http://localhost:8000/apps/installed

# Verify app permissions
adb shell pm list packages | grep isg
```

#### High Restart Frequency
- Check app stability and crash logs
- Verify device resources (memory, storage)
- Review app dependencies and requirements

### Monitoring Commands
```bash
# Real-time status monitoring
watch -n 30 'curl -s http://localhost:8000/watchdog/status | jq'

# Log monitoring
tail -f var/log/isg-android-control.log | grep -i watchdog

# Historical restart data
curl http://localhost:8000/metrics | jq '.app_watchdog'
```

## Future Enhancements

Potential improvements:
- **Multiple app support**: Monitor additional critical apps
- **Smart intervals**: Dynamic checking based on app stability
- **Crash detection**: Analyze logcat for app crash patterns
- **Resource monitoring**: App-specific CPU/memory thresholds
- **Integration alerts**: Home Assistant notifications for failures
- **Recovery strategies**: Different restart methods for different failure types