#!/bin/bash

# Ubuntu Container Setup Script for Android TV Box Integration
# Run this script in Ubuntu container (proot-distro)
# Note: Home Assistant should already be installed in the container

set -e

echo "Ubuntu Container Setup for Android TV Box Integration"
echo "====================================================="

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

# Check if running in Ubuntu container
if [ ! -f "/etc/os-release" ] || ! grep -q "Ubuntu" /etc/os-release; then
    print_error "This script must be run in Ubuntu container"
    print_error "Please run: proot-distro login ubuntu"
    exit 1
fi

print_status "Setting up Ubuntu container for Android TV Box integration..."

# Update package list
print_status "Updating package list..."
apt update

# Install system dependencies
print_status "Installing system dependencies..."
apt install -y \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    build-essential \
    python3-pip \
    adb \
    curl \
    wget \
    git \
    vim \
    htop

# Create Python virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "$HOME/uiauto_env" ]; then
    python3 -m venv ~/uiauto_env
    print_status "Virtual environment created at ~/uiauto_env"
else
    print_warning "Virtual environment already exists at ~/uiauto_env"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source ~/uiauto_env/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies (excluding Home Assistant as it's already installed)
print_status "Installing Python dependencies..."
print_status "Note: Home Assistant is already installed, skipping..."
pip install uiautomator2 aiohttp aiohttp-cors paho-mqtt voluptuous

# Test ADB connection
print_status "Testing ADB connection to Android device..."
if adb connect 127.0.0.1:5555; then
    print_status "ADB connection successful!"
    
    # Show connected devices
    print_status "Connected devices:"
    adb devices
    
    # Test basic command
    print_status "Testing basic ADB command..."
    device_model=$(adb shell getprop ro.product.model 2>/dev/null || echo "Unknown")
    print_status "Device model: $device_model"
    
    # Initialize uiautomator2
    print_status "Initializing uiautomator2..."
    python3 -m uiautomator2 init
    
else
    print_error "ADB connection failed!"
    print_error "Please ensure Android ADB service is running"
    print_error "Run the Android setup script first"
    exit 1
fi

# Create Home Assistant directory structure
print_status "Creating Home Assistant directory structure..."
mkdir -p ~/.homeassistant/custom_components
mkdir -p ~/.homeassistant/www

# Create basic Home Assistant configuration if it doesn't exist
if [ ! -f ~/.homeassistant/configuration.yaml ]; then
    print_status "Creating basic Home Assistant configuration..."
    cat > ~/.homeassistant/configuration.yaml << EOF
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
    print_warning "Home Assistant configuration already exists"
fi

# Create startup script
print_status "Creating Home Assistant startup script..."
cat > ~/start_homeassistant.sh << 'EOF'
#!/bin/bash
# Home Assistant startup script for Android TV Box

echo "Starting Home Assistant with Android TV Box integration..."

# Activate virtual environment
source ~/uiauto_env/bin/activate

# Start Home Assistant
hass --config ~/.homeassistant
EOF

chmod +x ~/start_homeassistant.sh

# Create environment activation script
print_status "Creating environment activation script..."
cat > ~/activate_env.sh << 'EOF'
#!/bin/bash
# Activate Android TV Box environment

echo "Activating Android TV Box environment..."

# Activate virtual environment
source ~/uiauto_env/bin/activate

# Connect to ADB
echo "Connecting to ADB..."
adb connect 127.0.0.1:5555

echo "Environment activated!"
echo "You can now run Home Assistant with: ./start_homeassistant.sh"
EOF

chmod +x ~/activate_env.sh

# Create test script
print_status "Creating test script..."
cat > ~/test_integration.py << 'EOF'
#!/usr/bin/env python3
"""Test Android TV Box integration."""

import asyncio
import sys
import os

# Add the custom component to Python path
sys.path.insert(0, os.path.join(os.path.expanduser('~'), '.homeassistant', 'custom_components'))

try:
    from android_tv_box.adb_service import ADBService
    
    async def test_connection():
        """Test ADB connection."""
        print("Testing Android TV Box ADB Connection...")
        
        adb_service = ADBService("127.0.0.1", 5555)
        
        try:
            if await adb_service.connect():
                print("✓ Connected successfully")
                
                # Test basic commands
                is_on = await adb_service.is_powered_on()
                print(f"✓ Device powered on: {is_on}")
                
                volume = await adb_service.get_volume()
                print(f"✓ Current volume: {volume}%")
                
                brightness = await adb_service.get_brightness()
                print(f"✓ Current brightness: {brightness}")
                
                print("✓ All tests passed!")
                return True
            else:
                print("✗ Connection failed")
                return False
                
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return False
        finally:
            await adb_service.disconnect()
    
    if __name__ == "__main__":
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please ensure the Android TV Box integration is installed")
    sys.exit(1)
EOF

chmod +x ~/test_integration.py

print_status "Ubuntu container setup completed successfully!"
print_status "Environment created at: ~/uiauto_env"
print_status "Home Assistant config: ~/.homeassistant/"

echo ""
print_status "Available scripts:"
echo "  - ~/activate_env.sh      : Activate environment"
echo "  - ~/start_homeassistant.sh: Start Home Assistant"
echo "  - ~/test_integration.py   : Test integration"

echo ""
print_status "Next steps:"
echo "  1. Copy the Android TV Box integration to ~/.homeassistant/custom_components/"
echo "  2. Run: ./activate_env.sh"
echo "  3. Run: ./start_homeassistant.sh"
echo "  4. Test with: python3 test_integration.py"

print_status "Setup completed! 🎉"
