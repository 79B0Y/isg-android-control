#!/bin/bash

# Android TV Box Setup Script for Termux
# Run this script in Termux to set up ADB service
# Note: This script only sets up ADB service on Android
# Home Assistant will be installed in Ubuntu container (see setup_ubuntu.sh)

set -e

echo "Android TV Box Setup Script for Termux"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_error "This script must be run in Termux"
    exit 1
fi

print_status "Setting up Android TV Box ADB service..."
print_status "Note: Home Assistant will be installed in Ubuntu container, not on Android"

# Update package list
print_status "Updating package list..."
pkg update

# Install required packages
print_status "Installing Android tools..."
pkg install -y android-tools

# Check if we have root access
if [ "$(id -u)" = "0" ]; then
    print_status "Running as root, configuring ADB service..."
    
    # Configure ADB TCP service
    print_status "Configuring ADB TCP service on port 5555..."
    setprop service.adb.tcp.port 5555
    
    # Restart ADB service
    print_status "Restarting ADB service..."
    stop adbd
    start adbd
    
    # Wait a moment for service to start
    sleep 2
    
    # Test connection
    print_status "Testing ADB connection..."
    if adb connect 127.0.0.1:5555; then
        print_status "ADB connection successful!"
        
        # Show connected devices
        print_status "Connected devices:"
        adb devices
        
        # Test basic command
        print_status "Testing basic ADB command..."
        device_model=$(adb shell getprop ro.product.model 2>/dev/null || echo "Unknown")
        print_status "Device model: $device_model"
        
    else
        print_error "ADB connection failed!"
        print_error "Please check if ADB debugging is enabled in Developer Options"
        exit 1
    fi
    
else
    print_warning "Not running as root. Please run as root to configure ADB service:"
    echo "su"
    echo "bash $0"
    exit 1
fi

print_status "Android setup completed successfully!"
print_status "ADB service is now running on port 5555"
print_status "You can now proceed with Ubuntu container setup"

echo ""
print_status "Next steps:"
echo "  1. Install proot-distro: pkg install proot-distro"
echo "  2. Install Ubuntu: proot-distro install ubuntu"
echo "  3. Enter Ubuntu: proot-distro login ubuntu"
echo "  4. Run Ubuntu setup script"

print_status "Setup completed! 🎉"
