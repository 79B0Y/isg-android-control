#!/bin/bash
# Manual ADB Commands Test Script
# Run this script to test all ADB commands used in ISG Android Control

set -e

echo "=== ISG Android Control - Manual ADB Commands Test ==="
echo

# Check if ADB is available
if ! command -v adb &> /dev/null; then
    echo "❌ ADB not found. Please install ADB first."
    exit 1
fi

# Check ADB connection
echo "1. Checking ADB connection..."
adb devices
echo

# Test basic commands
echo "2. Testing Basic Commands:"
echo "   📱 Basic shell access:"
adb shell echo "test"
adb shell whoami
echo

# Test audio commands
echo "3. Testing Audio Commands:"
echo "   🔊 Audio system info:"
adb shell dumpsys -t 5 audio | head -20
echo
echo "   🔊 Volume settings:"
adb shell settings get system volume_music_max
adb shell settings get system volume_music
echo

# Test screen commands
echo "4. Testing Screen Commands:"
echo "   📺 Screen brightness:"
adb shell settings get system screen_brightness
echo
echo "   📺 Power state:"
adb shell dumpsys power | grep -E "(Display Power|mHoldingDisplaySuspendBlocker)"
echo
echo "   📺 Display state:"
adb shell dumpsys display | grep "mScreenState="
echo

# Test app commands
echo "5. Testing App Commands:"
echo "   📱 Activity info:"
adb shell dumpsys activity activities | head -10
echo
echo "   📱 Process list:"
adb shell ps -A | head -10
echo

# Test system monitoring
echo "6. Testing System Monitoring:"
echo "   📊 Memory info:"
adb shell cat /proc/meminfo | head -10
echo
echo "   📊 CPU info:"
adb shell dumpsys -t 5 cpuinfo | head -10
echo
echo "   📊 Top processes:"
adb shell top -n 1 -d 1 | head -10
echo

# Test network commands
echo "7. Testing Network Commands:"
echo "   🌐 Connectivity:"
adb shell dumpsys -t 10 connectivity | head -10
echo
echo "   🌐 WiFi:"
adb shell dumpsys -t 5 wifi | head -10
echo

# Test storage commands
echo "8. Testing Storage Commands:"
echo "   💾 Data partition:"
adb shell df -k /data
echo
echo "   💾 SD card:"
adb shell df -k /sdcard
echo

# Test battery commands (if available)
echo "9. Testing Battery Commands (if available):"
adb shell dumpsys -t 5 battery | head -10
echo

# Test cellular commands (if available)
echo "10. Testing Cellular Commands (if available):"
adb shell dumpsys -t 5 telephony.registry | head -10
echo

# Test screenshot commands
echo "11. Testing Screenshot Commands:"
echo "   📸 Taking screenshot:"
adb shell screencap -p /tmp/test_screenshot.png
echo "   📸 Pulling screenshot:"
adb pull /tmp/test_screenshot.png ./test_screenshot.png
echo "   📸 Cleaning up:"
adb shell rm -f /tmp/test_screenshot.png
echo

# Test input commands
echo "12. Testing Input Commands:"
echo "   ⌨️ Home key:"
adb shell input keyevent 3
echo "   ⌨️ Back key:"
adb shell input keyevent 4
echo

# Test app management commands
echo "13. Testing App Management Commands:"
echo "   📱 Force stop settings:"
adb shell am force-stop com.android.settings
echo "   📱 Launch settings:"
adb shell monkey -p com.android.settings -c android.intent.category.LAUNCHER 1
echo

# Test memory info commands
echo "14. Testing Memory Info Commands:"
echo "   🧠 System memory:"
adb shell dumpsys meminfo system | head -10
echo

echo "✅ All ADB commands tested manually!"
echo
echo "📋 Summary:"
echo "   - Basic shell access: ✅"
echo "   - Audio commands: ✅"
echo "   - Screen commands: ✅"
echo "   - App commands: ✅"
echo "   - System monitoring: ✅"
echo "   - Network commands: ✅"
echo "   - Storage commands: ✅"
echo "   - Battery commands: ✅"
echo "   - Cellular commands: ✅"
echo "   - Screenshot commands: ✅"
echo "   - Input commands: ✅"
echo "   - App management: ✅"
echo "   - Memory info: ✅"
echo
echo "🎉 All ADB commands are working! The system should be ready to run."
