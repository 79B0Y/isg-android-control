#!/usr/bin/env python3
"""
Test ADB connection in Android box environment
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

async def test_adb_connection():
    """Test ADB connection"""
    print("=== Testing ADB Connection in Android Box ===")
    
    try:
        from isg_android_control.core.adb import ADBController
        
        # Create ADBController with localhost config
        print("1. Creating ADBController...")
        adb = ADBController(host="127.0.0.1", port=5555)
        print(f"   Host: {adb.host}")
        print(f"   Port: {adb.port}")
        print(f"   Target: {adb._target()}")
        
        # Test connection
        print("\n2. Testing connection...")
        try:
            result = await adb.connect()
            print(f"   ✅ Connection result: {result}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
        
        # Test basic command
        print("\n3. Testing basic command...")
        try:
            result = await adb._run("shell", "echo", "Android box test")
            print(f"   ✅ Command result: {result.strip()}")
        except Exception as e:
            print(f"   ❌ Command failed: {e}")
            return False
        
        # Test audio command (the one that was failing)
        print("\n4. Testing audio command...")
        try:
            result = await adb._run("shell", "dumpsys", "audio")
            print(f"   ✅ Audio command successful (length: {len(result)} chars)")
            # Show first few lines
            lines = result.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"      {line}")
        except Exception as e:
            print(f"   ❌ Audio command failed: {e}")
            return False
        
        # Test settings command
        print("\n5. Testing settings command...")
        try:
            result = await adb._run("shell", "settings", "get", "system", "screen_brightness")
            print(f"   ✅ Settings command result: {result.strip()}")
        except Exception as e:
            print(f"   ❌ Settings command failed: {e}")
            return False
        
        print("\n✅ All tests passed! ADB connection is working in Android box environment.")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check Android box environment"""
    print("=== Environment Check ===")
    
    # Check for Android-specific files
    android_files = [
        "/system/build.prop",
        "/data/data/com.termux",
        "/data/data/com.android.shell"
    ]
    
    found_android = False
    for file_path in android_files:
        if os.path.exists(file_path):
            print(f"✅ Found Android file: {file_path}")
            found_android = True
    
    if not found_android:
        print("⚠️  No Android-specific files found. This might not be an Android box environment.")
    
    # Check environment variables
    android_env_vars = ["ANDROID_ROOT", "ANDROID_DATA", "TERMUX_PREFIX"]
    for var in android_env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    return found_android

if __name__ == "__main__":
    import asyncio
    
    print("ISG Android Control - Android Box ADB Test")
    print("=" * 50)
    
    # Check environment
    is_android = check_environment()
    
    # Test ADB connection
    success = asyncio.run(test_adb_connection())
    
    if success:
        print("\n🎉 ADB connection test successful!")
        print("You can now run the full system with:")
        print("  python3 start_system.py")
    else:
        print("\n❌ ADB connection test failed.")
        print("Please check:")
        print("  1. ADB debugging is enabled on your Android device")
        print("  2. Run: adb connect 127.0.0.1")
        print("  3. Check: adb devices")
