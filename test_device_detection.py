#!/usr/bin/env python3
"""
Test device detection and connection
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to the project directory
os.chdir(current_dir)

async def test_device_detection():
    """Test device detection functionality"""
    print("=== Testing Device Detection ===")
    
    try:
        from isg_android_control.core.adb import ADBController
        
        # Create ADBController
        print("1. Creating ADBController...")
        adb = ADBController(host="127.0.0.1", port=5555)
        print(f"   Host: {adb.host}")
        print(f"   Port: {adb.port}")
        
        # Test device detection
        print("\n2. Testing device detection...")
        devices = await adb._get_available_devices()
        print(f"   Available devices: {devices}")
        
        best_device = await adb._find_best_device()
        print(f"   Best device: {best_device}")
        
        # Test connection
        print("\n3. Testing connection...")
        try:
            result = await adb.connect()
            print(f"   ✅ Connection result: {result}")
            print(f"   Target after connection: {adb._target()}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
        
        # Test basic command
        print("\n4. Testing basic command...")
        try:
            result = await adb._run("shell", "echo", "device_detection_test")
            print(f"   ✅ Command result: {result.strip()}")
        except Exception as e:
            print(f"   ❌ Command failed: {e}")
            return False
        
        # Test audio command
        print("\n5. Testing audio command...")
        try:
            result = await adb._run("shell", "dumpsys", "audio")
            print(f"   ✅ Audio command successful (length: {len(result)} chars)")
        except Exception as e:
            print(f"   ❌ Audio command failed: {e}")
            return False
        
        print("\n✅ All tests passed! Device detection is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    
    print("ISG Android Control - Device Detection Test")
    print("=" * 50)
    
    success = asyncio.run(test_device_detection())
    
    if success:
        print("\n🎉 Device detection test successful!")
        print("You can now run the full system with:")
        print("  python3 start_system.py")
    else:
        print("\n❌ Device detection test failed.")
        print("Please check:")
        print("  1. ADB devices: adb devices")
        print("  2. ADB connection: adb connect 127.0.0.1")
        print("  3. Check if multiple devices are connected")
