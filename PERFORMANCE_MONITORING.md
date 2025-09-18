# Termux Performance Monitoring

This document describes the new direct Termux performance monitoring system that was added to optimize Android device performance monitoring without relying on ADB.

## Overview

The new `TermuxPerformanceMonitor` class provides:

- **Direct system monitoring** using native Linux `top` command instead of ADB
- **Real-time CPU usage tracking** every 500ms
- **Automatic process killing** for processes exceeding 50% CPU usage
- **Smart process protection** to avoid killing critical system processes
- **Comprehensive performance metrics** including memory and load averages

## Key Components

### 1. TermuxPerformanceMonitor Class
- **Location**: `src/isg_android_control/services/performance_monitor.py`
- **Purpose**: Direct system performance monitoring using native Linux commands
- **Key Features**:
  - Runs `top -b -n 1 -o %CPU` every 500ms
  - Tracks CPU usage violations per process
  - Automatically kills processes after 3 consecutive violations (>50% CPU)
  - Protects critical processes (init, systemd, python, adb, etc.)

### 2. Enhanced MonitorService
- **Location**: `src/isg_android_control/services/monitor.py`
- **Changes**: Integrated with TermuxPerformanceMonitor
- **New Methods**:
  - `start_performance_monitoring()`: Start continuous monitoring
  - `stop_performance_monitoring()`: Stop monitoring
  - `get_performance_status()`: Get monitoring status
  - Enhanced `snapshot()`: Returns both ADB and Termux metrics

### 3. New API Endpoints
Added to `src/isg_android_control/api/main.py`:
- `GET /performance`: Current performance metrics
- `GET /performance/status`: Monitoring system status
- `GET /performance/violations`: Current violations and statistics
- `GET /system`: System info (load, memory)
- `POST /performance/start`: Start monitoring
- `POST /performance/stop`: Stop monitoring

## Configuration

### Default Settings
```python
TermuxPerformanceMonitor(
    cpu_threshold=50.0,       # Kill processes using >50% CPU
    monitoring_interval=0.5,  # Check every 500ms
    kill_after_violations=4,  # Kill after 4 consecutive violations (2 seconds)
    enable_auto_kill=True     # Enable automatic process killing
)
```

### Environment Variables
No new environment variables are required. The system automatically detects if it's running in a Termux environment.

## Process Protection

The system protects critical processes from automatic killing:

**Protected Process Names/Commands**:
- `init`, `kernel`, `systemd`
- `termux`, `sshd`, `adb`
- `isg-android-control`
- `python`, `python3`

**Protected Users**:
- `root` processes (unless clearly user applications)

## Performance Metrics

### Process Information
```json
{
  "pid": 1234,
  "user": "user",
  "cpu_percent": 75.5,
  "mem_percent": 1.2,
  "command": "high_cpu_app",
  "service_name": "optional_service_name"
}
```

### System Metrics
```json
{
  "timestamp": "2025-09-18T00:10:42.183764",
  "total_cpu_usage": 45.2,
  "total_memory_usage": 67.8,
  "process_count": 123,
  "high_cpu_process_count": 2,
  "high_cpu_processes": [...],
  "load_average": {
    "1min": 1.23,
    "5min": 2.34,
    "15min": 3.45
  }
}
```

## Automatic Process Management

### Violation Tracking
1. Monitor detects process using >50% CPU
2. Increment violation counter for that PID
3. After 4 consecutive violations (2 seconds), attempt to kill:
   - First try `kill -TERM PID` (graceful)
   - If fails, try `kill -KILL PID` (force)
4. Enhanced logging includes package name, app name, and user information

### Logging
All process kills are logged with:
- PID and command name
- CPU usage percentage
- Kill method used (TERM/KILL)
- Success/failure status

## Integration with Existing System

### Startup
Performance monitoring starts automatically when the FastAPI application starts via the `startup` event handler.

### Monitoring Data
The enhanced `MonitorService.snapshot()` now returns:
```json
{
  "adb": { /* existing ADB metrics */ },
  "performance": {
    "timestamp": "2025-09-18T00:10:42.183764",
    "total_cpu_usage": 45.2,
    "total_memory_usage": 67.8,
    "process_count": 123,
    "high_cpu_process_count": 2,
    "high_cpu_processes": [...]
  },
  "system": {
    "load_average": {"1min": 1.23, "5min": 2.34, "15min": 3.45},
    "monitoring_active": true,
    "cpu_threshold": 50.0,
    "auto_kill_enabled": true,
    "active_violations": 0
  }
}
```

## Home Assistant Integration

### New Sensors
The system now publishes additional sensors to Home Assistant:

1. **Android High CPU Processes**
   - Shows count of processes currently using >50% CPU
   - Updates every monitoring cycle (500ms)

2. **Android Process Monitoring**
   - Shows monitoring status (Active/Inactive)
   - Indicates if the monitoring system is running

3. **Android Process Violations**
   - Shows number of active violations
   - Tracks processes that are approaching kill threshold

### MQTT Topics
- `{base_topic}/performance_status`: System monitoring status
- `{base_topic}/performance_violations`: Current violations data
- `{base_topic}/state_json`: Enhanced with performance metrics

### API Integration
You can also query the monitoring system directly via HTTP:
- `GET /performance/violations`: Get current violation statistics
- `GET /performance/status`: Get monitoring system status

### Backward Compatibility
All existing ADB-based monitoring continues to work unchanged. The new Termux monitoring is additive.

## Testing

### Unit Tests
- **Location**: `tests/test_performance_monitor.py`
- **Coverage**: Process parsing, protection logic, violation tracking
- **Mocking**: Subprocess calls, file system access

### Manual Testing
```bash
# Test basic functionality
PYTHONPATH=src python3 -c "
from src.isg_android_control.services.performance_monitor import TermuxPerformanceMonitor
monitor = TermuxPerformanceMonitor()
print('Monitor created successfully')
"

# Test API endpoints (requires dependencies)
curl http://localhost:8000/performance/status
curl http://localhost:8000/performance
curl http://localhost:8000/system
```

## Benefits

1. **Reduced ADB Overhead**: Direct system calls are faster than ADB commands
2. **Real-time Response**: 500ms monitoring interval vs slower ADB polling
3. **Proactive Management**: Automatic killing of runaway processes
4. **System Protection**: Smart process protection prevents system damage
5. **Comprehensive Metrics**: Combined ADB and native system metrics
6. **Easy Configuration**: Simple threshold and interval settings

## Usage Examples

### Start/Stop Monitoring via API
```bash
# Start monitoring
curl -X POST http://localhost:8000/performance/start

# Check status
curl http://localhost:8000/performance/status

# Stop monitoring
curl -X POST http://localhost:8000/performance/stop
```

### Get Performance Data
```bash
# Current performance snapshot
curl http://localhost:8000/performance

# System information
curl http://localhost:8000/system

# Complete metrics (ADB + performance + system)
curl http://localhost:8000/metrics
```

## Security Considerations

1. **Process Killing**: Only non-protected processes can be automatically killed
2. **User Isolation**: Respects process ownership and system boundaries
3. **Graceful Termination**: Always tries TERM signal before KILL
4. **Logging**: All process management actions are logged for audit

## Future Enhancements

Potential improvements:
- Configurable CPU thresholds via API/config
- Memory usage threshold monitoring
- Process whitelist/blacklist configuration
- Integration with system alerts
- Historical performance data collection