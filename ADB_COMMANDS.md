# ISG Android Control - ADB Commands Reference

This document lists all ADB commands used in the ISG Android Control system for manual testing.

## 📱 Basic Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell echo "test"` | Test basic shell access | `adb shell echo "Hello World"` |
| `adb shell whoami` | Check current user | `adb shell whoami` |

## 🔊 Audio Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys -t 5 audio` | Get audio system info | `adb shell dumpsys -t 5 audio` |
| `adb shell settings get system volume_music_max` | Get max music volume | `adb shell settings get system volume_music_max` |
| `adb shell settings get system volume_music` | Get current music volume | `adb shell settings get system volume_music` |
| `adb shell media volume --stream 3 --set <value>` | Set volume via media | `adb shell media volume --stream 3 --set 5` |
| `adb shell settings put system volume_music <value>` | Set volume via settings | `adb shell settings put system volume_music 5` |

## 📺 Screen Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell settings get system screen_brightness` | Get screen brightness | `adb shell settings get system screen_brightness` |
| `adb shell settings put system screen_brightness <value>` | Set screen brightness | `adb shell settings put system screen_brightness 128` |
| `adb shell dumpsys power` | Get power state | `adb shell dumpsys power` |
| `adb shell dumpsys display` | Get display state | `adb shell dumpsys display` |

## 📱 App Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys activity activities` | Get activity info | `adb shell dumpsys activity activities` |
| `adb shell ps -A` | List all processes | `adb shell ps -A` |
| `adb shell am force-stop <package>` | Force stop app | `adb shell am force-stop com.android.settings` |
| `adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1` | Launch app | `adb shell monkey -p com.android.settings -c android.intent.category.LAUNCHER 1` |

## 📊 System Monitoring Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell cat /proc/meminfo` | Get memory info | `adb shell cat /proc/meminfo` |
| `adb shell top -n 1 -d 1` | Get top processes | `adb shell top -n 1 -d 1` |
| `adb shell dumpsys -t 5 cpuinfo` | Get CPU info | `adb shell dumpsys -t 5 cpuinfo` |

## 🌐 Network Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys -t 10 connectivity` | Get connectivity info | `adb shell dumpsys -t 10 connectivity` |
| `adb shell dumpsys -t 5 wifi` | Get WiFi info | `adb shell dumpsys -t 5 wifi` |

## 💾 Storage Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell df -k /data` | Get data partition usage | `adb shell df -k /data` |
| `adb shell df -k /sdcard` | Get SD card usage | `adb shell df -k /sdcard` |

## 🔋 Battery Commands (if available)

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys -t 5 battery` | Get battery info | `adb shell dumpsys -t 5 battery` |

## 📱 Cellular Commands (if available)

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys -t 5 telephony.registry` | Get cellular info | `adb shell dumpsys -t 5 telephony.registry` |

## 📸 Screenshot Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell screencap -p <path>` | Take screenshot | `adb shell screencap -p /tmp/screenshot.png` |
| `adb pull <remote> <local>` | Pull file from device | `adb pull /tmp/screenshot.png ./screenshot.png` |
| `adb shell rm -f <path>` | Remove file | `adb shell rm -f /tmp/screenshot.png` |

## ⌨️ Input Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell input keyevent <code>` | Send key event | `adb shell input keyevent 3` (Home) |
| `adb shell input keyevent 3` | Home key | `adb shell input keyevent 3` |
| `adb shell input keyevent 4` | Back key | `adb shell input keyevent 4` |
| `adb shell input keyevent 26` | Power key | `adb shell input keyevent 26` |

## 🧠 Memory Info Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `adb shell dumpsys meminfo <package>` | Get app memory usage | `adb shell dumpsys meminfo system` |

## 🧪 Testing Scripts

### Automated Test
```bash
python3 test_all_adb_commands.py
```

### Manual Test
```bash
./manual_adb_test.sh
```

## 🔧 Troubleshooting

### Common Issues

1. **"more than one device/emulator"**
   - Solution: Use `adb -s <device_id> <command>`
   - Example: `adb -s 192.168.188.221:5555 shell echo "test"`

2. **"device not found"**
   - Solution: Check connection with `adb devices`
   - Reconnect with `adb connect <ip>:5555`

3. **Permission denied**
   - Solution: Ensure ADB debugging is enabled
   - Check device authorization

4. **Command timeout**
   - Solution: Increase timeout or check device performance
   - Some commands may take longer on slower devices

### Key Event Codes

| Code | Key | Description |
|------|-----|-------------|
| 3 | Home | Home button |
| 4 | Back | Back button |
| 26 | Power | Power button |
| 24 | Volume Up | Volume up |
| 25 | Volume Down | Volume down |
| 82 | Menu | Menu button |
| 187 | Recent Apps | Recent apps |

### Volume Stream Types

| Stream | Code | Description |
|--------|------|-------------|
| STREAM_MUSIC | 3 | Music, media, games |
| STREAM_RING | 2 | Phone ring |
| STREAM_ALARM | 4 | Alarms |
| STREAM_NOTIFICATION | 5 | Notifications |
| STREAM_SYSTEM | 1 | System sounds |

## 📋 Test Checklist

- [ ] Basic shell access works
- [ ] Audio commands return valid data
- [ ] Screen brightness can be read/written
- [ ] App commands work (launch/stop)
- [ ] System monitoring returns data
- [ ] Network commands work
- [ ] Storage commands work
- [ ] Screenshot commands work
- [ ] Input commands work
- [ ] Memory info commands work

## 🎯 Success Criteria

All commands should:
1. Execute without errors
2. Return expected data format
3. Complete within reasonable timeout
4. Not cause device instability

If any command fails, check:
1. ADB connection status
2. Device permissions
3. Command syntax
4. Device compatibility
