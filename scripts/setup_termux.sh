#!/bin/bash
# Setup script for Termux environment

set -e

echo "=== ISG Android Control - Termux Setup ==="
echo

# Check if running in Termux
if [ -z "$PREFIX" ] || [[ "$PREFIX" != *"com.termux"* ]]; then
    echo "❌ This script should be run in Termux environment"
    echo "   Please install Termux and run this script from there"
    exit 1
fi

echo "✅ Running in Termux environment"
echo "   PREFIX: $PREFIX"
echo

# Check if ADB is available
if ! command -v adb &> /dev/null; then
    echo "❌ ADB not found. Installing..."
    pkg update
    pkg install -y android-tools
    echo "✅ ADB installed"
else
    echo "✅ ADB already installed"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    pkg install -y python
    echo "✅ Python3 installed"
else
    echo "✅ Python3 already installed"
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing..."
    pkg install -y python-pip
    echo "✅ pip3 installed"
else
    echo "✅ pip3 already installed"
fi

echo
echo "=== Configuration ==="

# Get device IP
echo "Please enter your Android device IP address:"
read -p "IP (e.g., 192.168.188.221): " DEVICE_IP

if [ -z "$DEVICE_IP" ]; then
    echo "❌ IP address is required"
    exit 1
fi

# Update device configuration
CONFIG_FILE="configs/device.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo "Updating device configuration..."
    sed -i "s/adb_host: .*/adb_host: $DEVICE_IP/" "$CONFIG_FILE"
    echo "✅ Updated $CONFIG_FILE with IP: $DEVICE_IP"
else
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

echo
echo "=== Testing ADB Connection ==="

# Test ADB connection
echo "Testing ADB connection to $DEVICE_IP:5555..."
if adb connect "$DEVICE_IP:5555"; then
    echo "✅ ADB connection successful"
    
    # Test basic command
    if adb shell echo "Test successful"; then
        echo "✅ ADB shell command working"
    else
        echo "❌ ADB shell command failed"
    fi
else
    echo "❌ ADB connection failed"
    echo "   Please ensure:"
    echo "   1. Android device has ADB debugging enabled"
    echo "   2. Device is on the same network"
    echo "   3. IP address is correct"
    exit 1
fi

echo
echo "=== Testing System Commands ==="

# Test top command
echo "Testing top command..."
if top -b -n 1 &> /dev/null; then
    echo "✅ top command working"
elif top -n 1 &> /dev/null; then
    echo "✅ top command working (alternative syntax)"
else
    echo "⚠️  top command not working - performance monitoring may be limited"
fi

# Test proc filesystem
if [ -f "/proc/loadavg" ]; then
    echo "✅ /proc/loadavg available"
else
    echo "⚠️  /proc/loadavg not available - load average monitoring disabled"
fi

if [ -f "/proc/meminfo" ]; then
    echo "✅ /proc/meminfo available"
else
    echo "⚠️  /proc/meminfo not available - memory monitoring disabled"
fi

echo
echo "=== Setup Complete ==="
echo "✅ Termux environment configured"
echo "✅ ADB connection established"
echo "✅ Device configuration updated"
echo
echo "You can now run the ISG Android Control system:"
echo "  python3 -m isg_android_control.run"
echo
echo "Or start the API server:"
echo "  python3 -m isg_android_control.api.main"
