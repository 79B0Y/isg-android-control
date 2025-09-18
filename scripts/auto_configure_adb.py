#!/usr/bin/env python3
"""
Auto-configure ADB host based on environment detection
"""
import os
import yaml
import subprocess
from pathlib import Path

def detect_android_environment():
    """Detect if we're running in an Android environment"""
    android_indicators = [
        "/system/build.prop",
        "/data/data/com.termux",
        "/data/data/com.android.shell",
        "/system/etc/hosts"
    ]
    
    for indicator in android_indicators:
        if os.path.exists(indicator):
            return True
    
    # Check environment variables
    android_env_vars = ["ANDROID_ROOT", "ANDROID_DATA", "TERMUX_PREFIX"]
    for var in android_env_vars:
        if os.environ.get(var):
            return True
    
    return False

def get_adb_devices():
    """Get list of ADB devices"""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = []
            for line in lines:
                if line.strip() and '\t' in line:
                    device_id, status = line.split('\t', 1)
                    if status.strip() == 'device':
                        devices.append(device_id)
            return devices
        return []
    except Exception:
        return []

def determine_adb_host():
    """Determine the best ADB host configuration"""
    if detect_android_environment():
        print("✅ Android environment detected")
        
        # Check what devices are available
        devices = get_adb_devices()
        print(f"Available ADB devices: {devices}")
        
        if not devices:
            print("⚠️  No ADB devices found. You may need to:")
            print("   1. Enable ADB debugging on your Android device")
            print("   2. Run: adb connect 127.0.0.1")
            return "127.0.0.1"
        
        # Check if localhost device is available
        localhost_devices = [d for d in devices if d.startswith(('127.0.0.1', 'localhost', 'emulator'))]
        if localhost_devices:
            print(f"✅ Found localhost device: {localhost_devices[0]}")
            return "127.0.0.1"
        else:
            print(f"⚠️  No localhost device found. Using first available device: {devices[0]}")
            # Extract host from device ID
            if ':' in devices[0]:
                return devices[0].split(':')[0]
            return "127.0.0.1"
    else:
        print("❌ Not in Android environment")
        return "127.0.0.1"

def update_device_config(adb_host):
    """Update device.yaml with the determined ADB host"""
    config_file = Path("configs/device.yaml")
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update ADB host
        old_host = config.get('adb_host', 'unknown')
        config['adb_host'] = adb_host
        
        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Updated ADB host: {old_host} → {adb_host}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False

def main():
    """Main function"""
    print("=== ADB Auto-Configuration ===")
    
    # Determine best ADB host
    adb_host = determine_adb_host()
    
    # Update configuration
    if update_device_config(adb_host):
        print(f"\n✅ Configuration updated successfully")
        print(f"   ADB Host: {adb_host}")
        print(f"   Config file: configs/device.yaml")
        
        print(f"\n📋 Next steps:")
        print(f"   1. Test connection: python3 test_localhost_adb.py")
        print(f"   2. Run system: python3 -m isg_android_control.run")
    else:
        print(f"\n❌ Configuration update failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
