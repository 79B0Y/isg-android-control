#!/usr/bin/env python3
"""
ADB Connection Diagnostic Script
"""
import asyncio
import sys
import os
import subprocess

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_adb_installed():
    """Check if ADB is installed and accessible"""
    print("1. Checking ADB installation...")
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ ADB installed: {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ ADB command failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("   ❌ ADB not found in PATH")
        return False

def check_adb_devices():
    """Check current ADB devices"""
    print("\n2. Checking ADB devices...")
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        print("   ADB devices output:")
        print(f"   {result.stdout}")
        if result.stderr:
            print(f"   Stderr: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ Failed to check devices: {e}")
        return False

def check_configuration():
    """Check configuration loading"""
    print("\n3. Checking configuration...")
    try:
        from isg_android_control.models.config import Settings
        settings = Settings.load()
        print(f"   ✅ Configuration loaded successfully")
        print(f"   ADB Host: {settings.device.adb_host}")
        print(f"   ADB Port: {settings.device.adb_port}")
        print(f"   ADB Serial: {settings.device.adb_serial}")
        
        if settings.device.adb_host == "192.168.188.221":
            print("   ✅ ADB host is correctly configured")
        else:
            print(f"   ⚠️  ADB host is {settings.device.adb_host}, expected 192.168.188.221")
            
        return True
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return False

async def test_adb_connection():
    """Test ADB connection with loaded configuration"""
    print("\n4. Testing ADB connection...")
    try:
        from isg_android_control.models.config import Settings
        from isg_android_control.core.adb import ADBController
        
        settings = Settings.load()
        adb = ADBController(
            host=settings.device.adb_host,
            port=settings.device.adb_port,
            serial=settings.device.adb_serial,
            has_battery=settings.device.has_battery,
            has_cellular=settings.device.has_cellular,
        )
        
        print(f"   ADBController target: {adb._target()}")
        
        # Test connection
        result = await adb.connect()
        print(f"   ✅ Connection result: {result}")
        
        # Test basic command
        result = await adb._run("shell", "echo", "Diagnostic test")
        print(f"   ✅ Command result: {result}")
        
        return True
    except Exception as e:
        print(f"   ❌ ADB connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_network_connectivity():
    """Check network connectivity to the device"""
    print("\n5. Checking network connectivity...")
    try:
        result = subprocess.run(["ping", "-c", "1", "192.168.188.221"], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ Device is reachable via ping")
            return True
        else:
            print("   ❌ Device is not reachable via ping")
            print(f"   Ping output: {result.stdout}")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ Ping timeout - device may be unreachable")
        return False
    except Exception as e:
        print(f"   ❌ Ping failed: {e}")
        return False

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("\n6. Suggested fixes:")
    print("   If ADB connection fails:")
    print("   1. Run: ./scripts/fix_adb_connection.sh")
    print("   2. Ensure Android device has ADB debugging enabled")
    print("   3. Check if device IP address is correct")
    print("   4. Verify network connectivity")
    print("   5. Restart ADB server: adb kill-server && adb start-server")

async def main():
    """Run all diagnostic checks"""
    print("=== ADB Connection Diagnostic ===")
    print()
    
    checks = [
        check_adb_installed(),
        check_adb_devices(),
        check_configuration(),
        await test_adb_connection(),
        check_network_connectivity()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n=== Diagnostic Summary ===")
    print(f"Passed: {passed}/{total} checks")
    
    if passed == total:
        print("✅ All checks passed! ADB connection should be working.")
    else:
        print("❌ Some checks failed. See suggestions below.")
        suggest_fixes()

if __name__ == "__main__":
    asyncio.run(main())
