#!/usr/bin/env python3
"""Test script for Android TV Box ADB connection."""

import asyncio
import sys
import os

# Add the custom component to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from android_tv_box.adb_service import ADBService


async def test_adb_connection():
    """Test ADB connection and basic commands."""
    print("Testing Android TV Box ADB Connection...")
    
    # Initialize ADB service
    adb_service = ADBService(
        host="127.0.0.1",
        port=5555,
        adb_path="/usr/bin/adb"
    )
    
    try:
        # Test connection
        print("1. Testing connection...")
        if await adb_service.connect():
            print("   ✓ Connected successfully")
        else:
            print("   ✗ Connection failed")
            return False
        
        # Test device status
        print("2. Testing device status...")
        is_connected = await adb_service.is_connected()
        print(f"   Device connected: {is_connected}")
        
        # Test power status
        print("3. Testing power status...")
        is_on = await adb_service.is_powered_on()
        print(f"   Device powered on: {is_on}")
        
        # Test WiFi status
        print("4. Testing WiFi status...")
        wifi_on = await adb_service.is_wifi_on()
        print(f"   WiFi enabled: {wifi_on}")
        
        # Test volume
        print("5. Testing volume...")
        volume = await adb_service.get_volume()
        print(f"   Current volume: {volume}%")
        
        # Test brightness
        print("6. Testing brightness...")
        brightness = await adb_service.get_brightness()
        print(f"   Current brightness: {brightness}")
        
        # Test current app
        print("7. Testing current app...")
        current_app = await adb_service.get_current_app()
        print(f"   Current app: {current_app}")
        
        # Test WiFi info
        print("8. Testing WiFi info...")
        wifi_info = await adb_service.get_wifi_info()
        print(f"   WiFi info: {wifi_info}")
        
        # Test system performance
        print("9. Testing system performance...")
        performance = await adb_service.get_system_performance()
        print(f"   Performance: {performance}")
        
        # Test screenshot
        print("10. Testing screenshot...")
        screenshot_path = "/sdcard/isgbackup/screenshot/test_screenshot.png"
        await adb_service.shell_command(f"mkdir -p /sdcard/isgbackup/screenshot/")
        screenshot_success = await adb_service.take_screenshot(screenshot_path)
        print(f"   Screenshot taken: {screenshot_success}")
        
        # Test iSG monitoring
        print("11. Testing iSG monitoring...")
        isg_running = await adb_service.is_isg_running()
        print(f"   iSG running: {isg_running}")
        
        if not isg_running:
            print("   Attempting to wake up iSG...")
            wake_success = await adb_service.wake_up_isg()
            print(f"   iSG wake up: {wake_success}")
        
        # Test app launch
        print("12. Testing app launch...")
        launch_success = await adb_service.launch_app("com.linknlink.app.device.isg")
        print(f"   App launch: {launch_success}")
        
        print("\n✓ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return False
    
    finally:
        # Disconnect
        await adb_service.disconnect()
        print("Disconnected from ADB")


async def test_media_commands():
    """Test media control commands."""
    print("\nTesting Media Control Commands...")
    
    adb_service = ADBService("127.0.0.1", 5555)
    
    try:
        await adb_service.connect()
        
        print("Testing media commands (these will affect your device):")
        
        # Test volume commands
        print("1. Testing volume up...")
        await adb_service.volume_up()
        await asyncio.sleep(1)
        
        print("2. Testing volume down...")
        await adb_service.volume_down()
        await asyncio.sleep(1)
        
        # Test navigation commands
        print("3. Testing navigation keys...")
        await adb_service.key_up()
        await asyncio.sleep(0.5)
        await adb_service.key_down()
        await asyncio.sleep(0.5)
        await adb_service.key_left()
        await asyncio.sleep(0.5)
        await adb_service.key_right()
        
        print("✓ Media commands test completed!")
        
    except Exception as e:
        print(f"✗ Media commands test failed: {e}")
    
    finally:
        await adb_service.disconnect()


if __name__ == "__main__":
    print("Android TV Box ADB Connection Test")
    print("=" * 40)
    
    # Run basic connection test
    success = asyncio.run(test_adb_connection())
    
    if success:
        # Ask user if they want to test media commands
        response = input("\nDo you want to test media control commands? (y/n): ")
        if response.lower() == 'y':
            asyncio.run(test_media_commands())
    
    print("\nTest completed!")
