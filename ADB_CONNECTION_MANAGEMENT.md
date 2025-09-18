# ADB On-Demand Connection Management

This document describes the optimized ADB connection management system that connects only when needed and automatically disconnects after periods of inactivity.

## Overview

The new connection management system provides:

- **On-demand connections**: ADB connects only when commands need to be executed
- **Automatic disconnection**: Connections close after configurable inactivity periods
- **Connection state tracking**: Monitor connection status and activity
- **Backward compatibility**: Existing code continues to work unchanged
- **Improved resource efficiency**: Reduces persistent connections and resource usage

## Key Changes

### 1. ADBController Enhancements
- **Location**: `src/isg_android_control/core/adb.py`
- **New Parameters**:
  - `connection_timeout: float = 300.0` - Auto-disconnect after 5 minutes of inactivity
- **New Methods**:
  - `ensure_connected()`: Establish connection if needed
  - `disconnect()`: Manually disconnect
  - `is_connected()`: Check connection status
  - `get_connection_info()`: Get detailed connection information

### 2. Connection Lifecycle
```python
# Before: Persistent connection
await adb.connect()  # Connect at startup
# Connection stays open forever

# After: On-demand connection
await adb.screenshot()  # Automatically connects when needed
# Connection auto-disconnects after 5 minutes of inactivity
```

### 3. API Integration Changes
- **Startup**: No automatic ADB connection at application startup
- **Shutdown**: Graceful ADB disconnection when application stops
- **New Endpoints**:
  - `GET /adb/status` - Connection status and info
  - `POST /adb/connect` - Manual connection
  - `POST /adb/disconnect` - Manual disconnection

## Configuration

### Default Settings
```python
ADBController(
    host="127.0.0.1",
    port=5555,
    connection_timeout=300.0  # 5 minutes
)
```

### Environment Variables
No new environment variables are required. The connection timeout can be configured when creating the ADBController instance.

## Connection Management Flow

### Automatic Connection
1. User calls ADB method (e.g., `screenshot()`, `list_packages()`)
2. `_run()` method calls `ensure_connected()`
3. If not connected, `_connect_internal()` establishes connection
4. Activity timestamp updated, auto-disconnect timer started
5. Command executes normally

### Activity Tracking
- Every successful ADB command updates the last activity timestamp
- Auto-disconnect timer resets with each activity
- Connection remains active while commands are being executed

### Auto-Disconnect
1. After `connection_timeout` seconds of inactivity
2. Background task checks if connection is still inactive
3. If inactive, calls `disconnect()` to close connection
4. Connection state reset to disconnected

### Manual Control
```python
# Manual connection
await adb.connect()

# Check status
if adb.is_connected():
    print("ADB is connected")

# Get detailed info
info = adb.get_connection_info()
print(f"Last activity: {info['last_activity']}")

# Manual disconnect
await adb.disconnect()
```

## API Endpoints

### Connection Status
```bash
# Get connection information
curl http://localhost:8000/adb/status

# Response:
{
  "connected": true,
  "host": "127.0.0.1",
  "port": 5555,
  "serial": null,
  "last_activity": "2025-09-18T00:24:08.785869",
  "connection_timeout": 300.0
}
```

### Manual Connection Management
```bash
# Connect manually
curl -X POST http://localhost:8000/adb/connect

# Disconnect manually
curl -X POST http://localhost:8000/adb/disconnect

# Check status
curl http://localhost:8000/adb/status
```

## Benefits

### Resource Efficiency
- **Reduced connections**: No persistent ADB connections when idle
- **Lower resource usage**: ADB daemon doesn't maintain unused connections
- **Network efficiency**: TCP connections closed when not needed

### Improved Reliability
- **Fresh connections**: Each activity gets a fresh, validated connection
- **Connection recovery**: Automatic reconnection on communication failures
- **State consistency**: Clear connection state tracking

### User Experience
- **Transparent operation**: Existing code works without changes
- **Fast response**: Connection establishment is fast enough for responsive UI
- **Flexible control**: Manual connection management available when needed

## Migration Guide

### Existing Code (No Changes Required)
```python
# This continues to work exactly the same
adb = ADBController()
await adb.connect()  # Still works (but now uses on-demand system)

# All existing methods work unchanged
screenshot = await adb.screenshot()
apps = await adb.list_packages()
await adb.nav("home")
```

### New Optional Features
```python
# Check connection status
if adb.is_connected():
    print("Currently connected")

# Get activity info
info = adb.get_connection_info()
print(f"Last used: {info['last_activity']}")

# Manual disconnect (optional)
await adb.disconnect()
```

### Configuration Changes
```python
# Optional: Configure connection timeout
adb = ADBController(
    host="192.168.1.100",
    port=5555,
    connection_timeout=120.0  # 2 minutes instead of 5
)
```

## Troubleshooting

### Connection Issues
- **Frequent disconnects**: Increase `connection_timeout` value
- **Slow responses**: Check ADB daemon status and device connectivity
- **Connection failures**: Verify device IP/port and ADB server status

### Monitoring
```bash
# Check connection status via API
curl http://localhost:8000/adb/status

# Monitor logs for connection activity
tail -f var/log/isg-android-control.log | grep ADB
```

### Common Patterns
```python
# For long-running operations, connection stays active
await adb.screenshot()  # Connects
await adb.list_packages()  # Reuses connection
await adb.nav("home")  # Still connected
# Auto-disconnects after 5 minutes of inactivity

# For periodic tasks
while True:
    await adb.screenshot()  # Connects on-demand
    await asyncio.sleep(600)  # 10 minutes
    # ADB disconnects during sleep, reconnects for next screenshot
```

## Performance Impact

### Connection Overhead
- **Connection time**: ~100-500ms for initial connection
- **Reconnection**: Rare due to activity-based timeouts
- **Memory usage**: Reduced due to fewer persistent connections

### Optimization Strategies
- **Batch operations**: Group multiple ADB commands together
- **Appropriate timeouts**: Set timeout based on usage patterns
- **Manual control**: Use manual connection for high-frequency operations

## Future Enhancements

Potential improvements:
- **Connection pooling**: Multiple ADB connections for high concurrency
- **Smart timeouts**: Dynamic timeout adjustment based on usage patterns
- **Connection health checks**: Periodic validation of existing connections
- **Metrics collection**: Detailed connection usage analytics