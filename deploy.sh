#!/bin/bash

# Android TV Box Home Assistant Integration Deployment Script
# This script helps deploy the integration to your Home Assistant instance

set -e

echo "Android TV Box Integration Deployment Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "custom_components/android_tv_box/manifest.json" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Detect Home Assistant installation
HA_CONFIG_DIR=""
HA_TYPE=""

# Check for different Home Assistant installation types
if [ -d "/config" ]; then
    # Docker/Container installation
    HA_CONFIG_DIR="/config"
    HA_TYPE="container"
    print_status "Detected Home Assistant Container installation"
elif [ -d "$HOME/.homeassistant" ]; then
    # Standard installation
    HA_CONFIG_DIR="$HOME/.homeassistant"
    HA_TYPE="standard"
    print_status "Detected standard Home Assistant installation"
elif [ -d "/usr/share/hassio/homeassistant" ]; then
    # Hass.io installation
    HA_CONFIG_DIR="/usr/share/hassio/homeassistant"
    HA_TYPE="hassio"
    print_status "Detected Hass.io installation"
else
    print_warning "Could not detect Home Assistant installation automatically"
    read -p "Please enter your Home Assistant config directory path: " HA_CONFIG_DIR
    HA_TYPE="custom"
fi

print_status "Using Home Assistant config directory: $HA_CONFIG_DIR"

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    print_status "Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Copy the integration
print_status "Copying Android TV Box integration..."
# Ensure backups directory exists (to avoid HA scanning backups as integrations)
mkdir -p "$CUSTOM_COMPONENTS_DIR/_backups"

# Move any legacy dot-named backups out of the scan path
shopt -s nullglob
for legacy in "$CUSTOM_COMPONENTS_DIR"/android_tv_box.backup.*; do
    if [ -d "$legacy" ]; then
        print_warning "Found legacy backup: $(basename "$legacy"). Moving to _backups/."
        mv "$legacy" "$CUSTOM_COMPONENTS_DIR/_backups/"
    fi
done
shopt -u nullglob

if [ -d "$CUSTOM_COMPONENTS_DIR/android_tv_box" ]; then
    print_warning "Integration already exists. Backing up to _backups/."
    TS=$(date +%Y%m%d_%H%M%S)
    mv "$CUSTOM_COMPONENTS_DIR/android_tv_box" "$CUSTOM_COMPONENTS_DIR/_backups/android_tv_box_$TS"
fi

cp -r "custom_components/android_tv_box" "$CUSTOM_COMPONENTS_DIR/"

print_status "Integration copied successfully!"

# Check if configuration.yaml exists
CONFIG_FILE="$HA_CONFIG_DIR/configuration.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_warning "configuration.yaml not found. Creating basic configuration..."
    cat > "$CONFIG_FILE" << EOF
# Home Assistant Configuration
default_config:

# Android TV Box Integration
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  device_name: "Android TV Box"
  screenshot_path: "/sdcard/isgbackup/screenshot/"
  screenshot_keep_count: 3
  screenshot_interval: 3
  performance_check_interval: 500
  cpu_threshold: 50
  termux_mode: true
  ubuntu_venv_path: "~/uiauto_env"
  adb_path: "/usr/bin/adb"
  apps:
    YouTube: com.google.android.youtube
    Spotify: com.spotify.music
    iSG: com.linknlink.app.device.isg
  visible:
    - YouTube
    - Spotify
    - iSG
  isg_monitoring: true
  isg_check_interval: 30
EOF
    print_status "Basic configuration created"
else
    # Check if android_tv_box is already configured
    if grep -q "android_tv_box:" "$CONFIG_FILE"; then
        print_warning "android_tv_box is already configured in configuration.yaml"
        print_warning "Please manually update your configuration if needed"
    else
        print_status "Adding Android TV Box configuration to configuration.yaml..."
        cat >> "$CONFIG_FILE" << EOF

# Android TV Box Integration
android_tv_box:
  host: "127.0.0.1"
  port: 5555
  device_name: "Android TV Box"
  screenshot_path: "/sdcard/isgbackup/screenshot/"
  screenshot_keep_count: 3
  screenshot_interval: 3
  performance_check_interval: 500
  cpu_threshold: 50
  termux_mode: true
  ubuntu_venv_path: "~/uiauto_env"
  adb_path: "/usr/bin/adb"
  apps:
    YouTube: com.google.android.youtube
    Spotify: com.spotify.music
    iSG: com.linknlink.app.device.isg
  visible:
    - YouTube
    - Spotify
    - iSG
  isg_monitoring: true
  isg_check_interval: 30
EOF
        print_status "Configuration added to configuration.yaml"
    fi
fi

# Create setup instructions
SETUP_FILE="$HA_CONFIG_DIR/android_tv_box_setup.md"
cat > "$SETUP_FILE" << EOF
# Android TV Box Setup Instructions

## Prerequisites

1. **Android Device with Root Access**
2. **Termux App** installed on Android
3. **Home Assistant** running in Ubuntu container via proot-distro

## Android Setup (Termux)

\`\`\`bash
# Install Android tools
pkg update
pkg install android-tools

# Exit termux user and configure ADB as root
exit
su
setprop service.adb.tcp.port 5555
stop adbd
start adbd
adb connect 127.0.0.1:5555
exit
\`\`\`

## Ubuntu Container Setup

\`\`\`bash
# Install proot-distro and Ubuntu
pkg install proot-distro
proot-distro install ubuntu

# Enter Ubuntu container
proot-distro login ubuntu

# Install system dependencies
apt update && apt install -y \\
  libxml2-dev libxslt1-dev python3-dev \\
  build-essential python3-pip adb curl wget

# Create Python virtual environment
python3 -m venv ~/uiauto_env
source ~/uiauto_env/bin/activate
pip install --upgrade pip
pip install uiautomator2 homeassistant

# Test ADB connection
adb connect 127.0.0.1:5555
adb devices
\`\`\`

## Testing

Run the test script to verify everything is working:

\`\`\`bash
python3 test_adb_connection.py
\`\`\`

## Restart Home Assistant

After completing the setup, restart Home Assistant to load the new integration.

## Troubleshooting

- Check ADB connection: \`adb devices\`
- Check Home Assistant logs for errors
- Ensure all dependencies are installed
- Verify ADB service is running on Android device

For more information, see the README.md file in the integration directory.
EOF

print_status "Setup instructions created: $SETUP_FILE"

# Check for required dependencies
print_status "Checking dependencies..."

# Check if adb is available
if command -v adb &> /dev/null; then
    print_status "ADB is available: $(which adb)"
else
    print_warning "ADB not found in PATH. Make sure it's installed and accessible."
fi

# Check if Python is available
if command -v python3 &> /dev/null; then
    print_status "Python3 is available: $(python3 --version)"
else
    print_warning "Python3 not found. Make sure it's installed."
fi

# Check if pip is available
if command -v pip3 &> /dev/null; then
    print_status "pip3 is available: $(pip3 --version)"
else
    print_warning "pip3 not found. Make sure it's installed."
fi

print_status "Deployment completed successfully!"
print_status "Next steps:"
echo "  1. Complete the Android and Ubuntu setup as described in $SETUP_FILE"
echo "  2. Test the connection using: python3 test_adb_connection.py"
echo "  3. Restart Home Assistant"
echo "  4. Check the integration in Home Assistant UI"

print_status "Integration files:"
echo "  - Integration: $CUSTOM_COMPONENTS_DIR/android_tv_box/"
echo "  - Configuration: $CONFIG_FILE"
echo "  - Setup guide: $SETUP_FILE"
echo "  - Test script: test_adb_connection.py"

echo ""
print_status "Deployment completed! 🎉"
