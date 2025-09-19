#!/usr/bin/env python3
"""Standalone ADB connection test for Android TV Box integration."""
import asyncio
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


class SimpleADBService:
    """Simplified ADB service for testing without Home Assistant dependencies."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5555, adb_path: str = "adb"):
        """Initialize ADB service."""
        self.host = host
        self.port = port
        self.adb_path = adb_path
        self.device_address = f"{host}:{port}"
        self._connected = False

    async def _run_command(self, cmd: list, timeout: int = 10) -> str:
        """Run ADB command."""
        full_cmd = [self.adb_path] + cmd
        _LOGGER.info(f"Running ADB command: {' '.join(full_cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            result = stdout.decode('utf-8', errors='ignore')
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                _LOGGER.error(f"ADB command failed: {error_msg}")
                return error_msg
            
            return result
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"Command timeout: {' '.join(full_cmd)}")

    async def connect(self) -> bool:
        """Connect to ADB device."""
        try:
            # Connect to device
            result = await self._run_command(["connect", self.device_address])
            if "connected" in result.lower() or "already connected" in result.lower():
                self._connected = True
                _LOGGER.info(f"Connected to Android device at {self.device_address}")
                return True
            else:
                _LOGGER.error(f"Failed to connect to {self.device_address}: {result}")
                return False
        except Exception as e:
            _LOGGER.error(f"ADB connection error: {e}")
            return False

    async def shell_command(self, command: str, timeout: int = 10) -> str:
        """Execute shell command on device."""
        if not self._connected:
            if not await self.connect():
                raise Exception("Device not connected")

        try:
            cmd = ["-s", self.device_address, "shell"] + command.split()
            result = await self._run_command(cmd, timeout=timeout)
            return result.strip()
        except Exception as e:
            _LOGGER.error(f"ADB command error: {e}")
            raise Exception(f"Command failed: {command}")

    async def is_connected(self) -> bool:
        """Check if device is connected."""
        try:
            result = await self._run_command(["devices"])
            return self.device_address in result and "device" in result
        except Exception:
            return False

    # Test methods for basic functionality
    async def test_basic_commands(self):
        """Test basic ADB commands."""
        tests = [
            ("Device property", "getprop ro.product.model"),
            ("Current time", "date"),
            ("WiFi status", "settings get global wifi_on"),
            ("Screen brightness", "settings get system screen_brightness"),
            ("Battery info", "dumpsys battery | grep level"),
            ("Current app", "dumpsys activity activities | grep 'ActivityRecord' | head -1"),
        ]
        
        results = {}
        for test_name, command in tests:
            try:
                _LOGGER.info(f"Testing: {test_name}")
                result = await self.shell_command(command)
                results[test_name] = result
                _LOGGER.info(f"  Result: {result}")
            except Exception as e:
                _LOGGER.error(f"  Failed: {e}")
                results[test_name] = f"ERROR: {e}"
        
        return results

    async def test_media_commands(self):
        """Test media control commands."""
        tests = [
            ("Volume up", "input keyevent 24"),
            ("Volume down", "input keyevent 25"),
            ("Home key", "input keyevent 82"),
            ("Back key", "input keyevent 4"),
        ]
        
        results = {}
        for test_name, command in tests:
            try:
                _LOGGER.info(f"Testing: {test_name}")
                result = await self.shell_command(command)
                results[test_name] = "SUCCESS"
                _LOGGER.info(f"  Success")
                await asyncio.sleep(1)  # Small delay between commands
            except Exception as e:
                _LOGGER.error(f"  Failed: {e}")
                results[test_name] = f"ERROR: {e}"
        
        return results

    async def test_system_info(self):
        """Test system information commands."""
        tests = [
            ("CPU info", "top -d 0.5 -n 1 | head -10"),
            ("Memory info", "cat /proc/meminfo | head -5"),
            ("WiFi info", "dumpsys wifi | grep 'SSID:' | head -1"),
            ("Power status", "dumpsys power | grep -E '(mWakefulness|mScreenOn)' | head -2"),
        ]
        
        results = {}
        for test_name, command in tests:
            try:
                _LOGGER.info(f"Testing: {test_name}")
                result = await self.shell_command(command)
                results[test_name] = result
                _LOGGER.info(f"  Result: {result[:100]}...")
            except Exception as e:
                _LOGGER.error(f"  Failed: {e}")
                results[test_name] = f"ERROR: {e}"
        
        return results


async def main():
    """Main test function."""
    _LOGGER.info("=== Android TV Box ADB Connection Test ===")
    
    # Initialize ADB service with the actual device IP
    adb = SimpleADBService(host="192.168.188.221", port=5555)
    
    # Test connection
    _LOGGER.info("\n1. Testing ADB connection...")
    connected = await adb.connect()
    if not connected:
        _LOGGER.error("Failed to connect to ADB. Please ensure:")
        _LOGGER.error("  - ADB TCP service is running on port 5555")
        _LOGGER.error("  - Device is accessible at 127.0.0.1:5555")
        return
    
    # Test if device is listed
    _LOGGER.info("\n2. Checking device status...")
    is_connected = await adb.is_connected()
    _LOGGER.info(f"Device connected: {is_connected}")
    
    # Test basic commands
    _LOGGER.info("\n3. Testing basic commands...")
    basic_results = await adb.test_basic_commands()
    
    # Test media commands
    _LOGGER.info("\n4. Testing media commands...")
    media_results = await adb.test_media_commands()
    
    # Test system info
    _LOGGER.info("\n5. Testing system information...")
    system_results = await adb.test_system_info()
    
    # Summary
    _LOGGER.info("\n=== Test Summary ===")
    all_results = {**basic_results, **media_results, **system_results}
    
    success_count = sum(1 for result in all_results.values() if not result.startswith("ERROR"))
    total_count = len(all_results)
    
    _LOGGER.info(f"Tests passed: {success_count}/{total_count}")
    
    if success_count == total_count:
        _LOGGER.info("✅ All tests passed! ADB connection is working correctly.")
    else:
        _LOGGER.warning("⚠️  Some tests failed. Check the logs above for details.")
        
    # Display failed tests
    failed_tests = [name for name, result in all_results.items() if result.startswith("ERROR")]
    if failed_tests:
        _LOGGER.warning(f"Failed tests: {', '.join(failed_tests)}")


if __name__ == "__main__":
    asyncio.run(main())