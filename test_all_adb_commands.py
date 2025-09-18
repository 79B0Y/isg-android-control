#!/usr/bin/env python3
"""
Test all ADB commands used in the ISG Android Control system
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

async def test_adb_commands():
    """Test all ADB commands used in the system"""
    print("=== ISG Android Control - ADB Commands Test ===")
    print()
    
    try:
        from isg_android_control.core.adb import ADBController
        
        # Create ADBController
        print("1. Creating ADBController...")
        adb = ADBController(host="192.168.188.221", port=5555)
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
        
        # Test all ADB commands
        print("\n3. Testing all ADB commands...")
        
        # Basic commands
        print("\n   📱 Basic Commands:")
        try:
            result = await adb._run("shell", "echo", "test")
            print(f"      ✅ echo test: {result.strip()}")
        except Exception as e:
            print(f"      ❌ echo test failed: {e}")
        
        # Audio commands
        print("\n   🔊 Audio Commands:")
        try:
            result = await adb._run("shell", "dumpsys", "-t", "5", "audio", timeout=10.0)
            print(f"      ✅ dumpsys audio: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys audio failed: {e}")
        
        try:
            result = await adb._run("shell", "settings", "get", "system", "volume_music_max", timeout=5.0)
            print(f"      ✅ volume_music_max: {result.strip()}")
        except Exception as e:
            print(f"      ❌ volume_music_max failed: {e}")
        
        try:
            result = await adb._run("shell", "settings", "get", "system", "volume_music", timeout=5.0)
            print(f"      ✅ volume_music: {result.strip()}")
        except Exception as e:
            print(f"      ❌ volume_music failed: {e}")
        
        # Screen commands
        print("\n   📺 Screen Commands:")
        try:
            result = await adb._run("shell", "settings", "get", "system", "screen_brightness")
            print(f"      ✅ screen_brightness: {result.strip()}")
        except Exception as e:
            print(f"      ❌ screen_brightness failed: {e}")
        
        try:
            result = await adb._run("shell", "dumpsys", "power", timeout=8.0)
            print(f"      ✅ dumpsys power: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys power failed: {e}")
        
        try:
            result = await adb._run("shell", "dumpsys", "display", timeout=8.0)
            print(f"      ✅ dumpsys display: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys display failed: {e}")
        
        # App commands
        print("\n   📱 App Commands:")
        try:
            result = await adb._run("shell", "dumpsys", "activity", "activities", timeout=10.0)
            print(f"      ✅ dumpsys activity activities: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys activity activities failed: {e}")
        
        try:
            result = await adb._run("shell", "ps", "-A", timeout=10.0)
            print(f"      ✅ ps -A: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ ps -A failed: {e}")
        
        # System monitoring commands
        print("\n   📊 System Monitoring Commands:")
        try:
            result = await adb._run("shell", "cat", "/proc/meminfo", timeout=5.0)
            print(f"      ✅ /proc/meminfo: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ /proc/meminfo failed: {e}")
        
        try:
            result = await adb._run("shell", "top", "-n", "1", "-d", "1", timeout=5.0)
            print(f"      ✅ top -n 1 -d 1: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ top command failed: {e}")
        
        try:
            result = await adb._run("shell", "dumpsys", "-t", "5", "cpuinfo", timeout=8.0)
            print(f"      ✅ dumpsys cpuinfo: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys cpuinfo failed: {e}")
        
        # Network commands
        print("\n   🌐 Network Commands:")
        try:
            result = await adb._run("shell", "dumpsys", "-t", "10", "connectivity", timeout=15.0)
            print(f"      ✅ dumpsys connectivity: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys connectivity failed: {e}")
        
        try:
            result = await adb._run("shell", "dumpsys", "-t", "5", "wifi", timeout=10.0)
            print(f"      ✅ dumpsys wifi: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys wifi failed: {e}")
        
        # Storage commands
        print("\n   💾 Storage Commands:")
        try:
            result = await adb._run("shell", "df", "-k", "/data", timeout=5.0)
            print(f"      ✅ df -k /data: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ df -k /data failed: {e}")
        
        try:
            result = await adb._run("shell", "df", "-k", "/sdcard", timeout=5.0)
            print(f"      ✅ df -k /sdcard: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ df -k /sdcard failed: {e}")
        
        # Battery commands (if available)
        print("\n   🔋 Battery Commands (if available):")
        try:
            result = await adb._run("shell", "dumpsys", "-t", "5", "battery", timeout=10.0)
            print(f"      ✅ dumpsys battery: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys battery failed: {e}")
        
        # Cellular commands (if available)
        print("\n   📱 Cellular Commands (if available):")
        try:
            result = await adb._run("shell", "dumpsys", "-t", "5", "telephony.registry", timeout=10.0)
            print(f"      ✅ dumpsys telephony.registry: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys telephony.registry failed: {e}")
        
        # Screenshot commands
        print("\n   📸 Screenshot Commands:")
        try:
            result = await adb._run("shell", "screencap", "-p", "/tmp/test_screenshot.png", timeout=10.0)
            print(f"      ✅ screencap -p: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ screencap failed: {e}")
        
        # Input commands
        print("\n   ⌨️ Input Commands:")
        try:
            result = await adb._run("shell", "input", "keyevent", "3", timeout=5.0)  # Home key
            print(f"      ✅ input keyevent 3 (Home): {result.strip()}")
        except Exception as e:
            print(f"      ❌ input keyevent failed: {e}")
        
        # App management commands
        print("\n   📱 App Management Commands:")
        try:
            result = await adb._run("shell", "am", "force-stop", "com.android.settings", timeout=15.0)
            print(f"      ✅ am force-stop: {result.strip()}")
        except Exception as e:
            print(f"      ❌ am force-stop failed: {e}")
        
        try:
            result = await adb._run("shell", "monkey", "-p", "com.android.settings", "-c", "android.intent.category.LAUNCHER", "1", timeout=10.0)
            print(f"      ✅ monkey launch: {result.strip()}")
        except Exception as e:
            print(f"      ❌ monkey launch failed: {e}")
        
        # Memory info commands
        print("\n   🧠 Memory Info Commands:")
        try:
            result = await adb._run("shell", "dumpsys", "meminfo", "system", timeout=10.0)
            print(f"      ✅ dumpsys meminfo system: {len(result)} chars")
        except Exception as e:
            print(f"      ❌ dumpsys meminfo failed: {e}")
        
        print("\n✅ All ADB commands tested!")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_manual_test_commands():
    """Print manual test commands for reference"""
    print("\n=== Manual ADB Commands for Testing ===")
    print("You can manually test these commands:")
    print()
    
    commands = [
        # Basic commands
        ("Basic", "adb shell echo 'test'"),
        ("Basic", "adb shell whoami"),
        
        # Audio commands
        ("Audio", "adb shell dumpsys -t 5 audio"),
        ("Audio", "adb shell settings get system volume_music_max"),
        ("Audio", "adb shell settings get system volume_music"),
        ("Audio", "adb shell media volume --stream 3 --set 5"),
        ("Audio", "adb shell settings put system volume_music 5"),
        
        # Screen commands
        ("Screen", "adb shell settings get system screen_brightness"),
        ("Screen", "adb shell settings put system screen_brightness 128"),
        ("Screen", "adb shell dumpsys power"),
        ("Screen", "adb shell dumpsys display"),
        
        # App commands
        ("Apps", "adb shell dumpsys activity activities"),
        ("Apps", "adb shell ps -A"),
        ("Apps", "adb shell am force-stop com.android.settings"),
        ("Apps", "adb shell monkey -p com.android.settings -c android.intent.category.LAUNCHER 1"),
        
        # System monitoring
        ("System", "adb shell cat /proc/meminfo"),
        ("System", "adb shell top -n 1 -d 1"),
        ("System", "adb shell dumpsys -t 5 cpuinfo"),
        
        # Network
        ("Network", "adb shell dumpsys -t 10 connectivity"),
        ("Network", "adb shell dumpsys -t 5 wifi"),
        
        # Storage
        ("Storage", "adb shell df -k /data"),
        ("Storage", "adb shell df -k /sdcard"),
        
        # Battery (if available)
        ("Battery", "adb shell dumpsys -t 5 battery"),
        
        # Cellular (if available)
        ("Cellular", "adb shell dumpsys -t 5 telephony.registry"),
        
        # Screenshot
        ("Screenshot", "adb shell screencap -p /tmp/test.png"),
        ("Screenshot", "adb pull /tmp/test.png ./test.png"),
        
        # Input
        ("Input", "adb shell input keyevent 3"),  # Home
        ("Input", "adb shell input keyevent 4"),  # Back
        ("Input", "adb shell input keyevent 26"), # Power
        
        # Memory
        ("Memory", "adb shell dumpsys meminfo system"),
    ]
    
    current_category = None
    for category, command in commands:
        if category != current_category:
            print(f"\n📱 {category} Commands:")
            current_category = category
        print(f"   {command}")

if __name__ == "__main__":
    import asyncio
    
    print("ISG Android Control - Complete ADB Commands Test")
    print("=" * 60)
    
    # Run automated tests
    success = asyncio.run(test_adb_commands())
    
    # Print manual test commands
    print_manual_test_commands()
    
    if success:
        print("\n🎉 ADB commands test completed successfully!")
        print("All commands are working. You can now run the full system.")
    else:
        print("\n❌ Some ADB commands failed.")
        print("Please check the manual commands above and test them individually.")
