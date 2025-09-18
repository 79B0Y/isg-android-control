#!/bin/bash
# Fix ADB connection issues

set -e

echo "=== ADB Connection Fix Script ==="
echo

# Kill ADB server to clear cached connections
echo "1. Killing ADB server to clear cached connections..."
adb kill-server
echo "✅ ADB server killed"

# Start ADB server
echo "2. Starting ADB server..."
adb start-server
echo "✅ ADB server started"

# Check current devices
echo "3. Checking current devices..."
adb devices
echo

# Connect to the correct device
echo "4. Connecting to correct device (192.168.188.221:5555)..."
if adb connect 192.168.188.221:5555; then
    echo "✅ Connected to 192.168.188.221:5555"
else
    echo "❌ Failed to connect to 192.168.188.221:5555"
    echo "   Please ensure:"
    echo "   1. Android device has ADB debugging enabled"
    echo "   2. Device is on the same network"
    echo "   3. IP address is correct"
    exit 1
fi

# Test connection
echo "5. Testing connection..."
if adb shell echo "Test successful"; then
    echo "✅ Connection test successful"
else
    echo "❌ Connection test failed"
    exit 1
fi

# Show final device list
echo "6. Final device list:"
adb devices

echo
echo "=== ADB Connection Fixed ==="
echo "✅ ADB server restarted"
echo "✅ Connected to 192.168.188.221:5555"
echo "✅ Connection tested successfully"
echo
echo "You can now run the ISG Android Control system:"
echo "  python3 -m isg_android_control.run"
