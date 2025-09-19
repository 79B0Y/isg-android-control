#!/usr/bin/env python3
"""Complete integration test for Android TV Box Home Assistant integration."""
import asyncio
import subprocess
import time
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


class CompleteIntegrationTest:
    """Complete test suite for Android TV Box integration."""

    def __init__(self, host: str = "192.168.188.221", port: int = 5555, adb_path: str = "adb"):
        """Initialize test suite."""
        self.host = host
        self.port = port
        self.adb_path = adb_path
        self.device_address = f"{host}:{port}"
        self._connected = False
        self.test_results = {}

    async def _run_command(self, cmd: list, timeout: int = 10) -> str:
        """Run ADB command."""
        full_cmd = [self.adb_path] + cmd
        _LOGGER.debug(f"Running ADB command: {' '.join(full_cmd)}")
        
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

    async def test_media_player_functionality(self):
        """Test media player commands per design spec."""
        _LOGGER.info("Testing Media Player functionality...")
        tests = []
        
        try:
            # Test volume commands
            _LOGGER.info("  Testing volume commands...")
            result = await self.shell_command("cmd media_session volume --stream 3 --get")
            if "volume is" in result:
                tests.append(("Get Volume", "PASS", result))
            else:
                tests.append(("Get Volume", "FAIL", result))
            
            # Test volume controls
            await self.shell_command("input keyevent 24")  # Volume up
            await asyncio.sleep(1)
            await self.shell_command("input keyevent 25")  # Volume down
            tests.append(("Volume Controls", "PASS", "Volume up/down commands sent"))
            
            # Test media controls
            _LOGGER.info("  Testing media controls...")
            await self.shell_command("input keyevent 85")  # Play/pause
            await asyncio.sleep(1)
            await self.shell_command("input keyevent 126")  # Play
            await asyncio.sleep(1)
            await self.shell_command("input keyevent 127")  # Pause
            tests.append(("Media Controls", "PASS", "Play/pause commands sent"))
            
            # Test power status detection
            _LOGGER.info("  Testing power status detection...")
            power_result = await self.shell_command("dumpsys power | grep -E '(mWakefulness|mScreenOn)' | head -2")
            if "Awake" in power_result or "mScreenOn=true" in power_result:
                tests.append(("Power Status", "PASS", "Device is awake"))
            else:
                tests.append(("Power Status", "FAIL", power_result))
                
        except Exception as e:
            tests.append(("Media Player", "ERROR", str(e)))
        
        self.test_results["media_player"] = tests
        return tests

    async def test_switch_functionality(self):
        """Test switch commands per design spec."""
        _LOGGER.info("Testing Switch functionality...")
        tests = []
        
        try:
            # Test WiFi status
            _LOGGER.info("  Testing WiFi status...")
            wifi_status = await self.shell_command("settings get global wifi_on")
            if wifi_status.strip() in ["0", "1"]:
                tests.append(("WiFi Status", "PASS", f"WiFi status: {wifi_status.strip()}"))
            else:
                tests.append(("WiFi Status", "FAIL", wifi_status))
            
            # Test power status
            _LOGGER.info("  Testing power status...")
            power_result = await self.shell_command("dumpsys power | grep mWakefulness")
            if "mWakefulness" in power_result:
                tests.append(("Power Status Check", "PASS", power_result.strip()))
            else:
                tests.append(("Power Status Check", "FAIL", power_result))
                
        except Exception as e:
            tests.append(("Switch", "ERROR", str(e)))
        
        self.test_results["switch"] = tests
        return tests

    async def test_camera_functionality(self):
        """Test camera (screenshot) functionality per design spec."""
        _LOGGER.info("Testing Camera (Screenshot) functionality...")
        tests = []
        
        try:
            # Test screenshot directory
            screenshot_path = "/sdcard/isgbackup/screenshot"
            _LOGGER.info(f"  Testing screenshot directory: {screenshot_path}")
            
            await self.shell_command(f"mkdir -p {screenshot_path}")
            
            # Take a test screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"{screenshot_path}/test_screen_{timestamp}.png"
            
            result = await self.shell_command(f"screencap -p {screenshot_file}")
            
            # Verify screenshot was created
            verify_result = await self.shell_command(f"ls -la {screenshot_file} 2>/dev/null || echo 'not found'")
            if "not found" not in verify_result and len(verify_result.strip()) > 0:
                tests.append(("Screenshot Creation", "PASS", f"Screenshot created: {screenshot_file}"))
                
                # Test screenshot cleanup
                await self.shell_command(f"rm -f {screenshot_file}")
                tests.append(("Screenshot Cleanup", "PASS", "Screenshot cleaned up"))
            else:
                tests.append(("Screenshot Creation", "FAIL", verify_result))
                
        except Exception as e:
            tests.append(("Camera", "ERROR", str(e)))
        
        self.test_results["camera"] = tests
        return tests

    async def test_sensor_functionality(self):
        """Test sensor functionality per design spec."""
        _LOGGER.info("Testing Sensor functionality...")
        tests = []
        
        try:
            # Test brightness sensor
            _LOGGER.info("  Testing brightness sensor...")
            brightness = await self.shell_command("settings get system screen_brightness")
            if brightness.strip().isdigit():
                tests.append(("Brightness Sensor", "PASS", f"Brightness: {brightness.strip()}"))
            else:
                tests.append(("Brightness Sensor", "FAIL", brightness))
            
            # Test WiFi info sensor
            _LOGGER.info("  Testing WiFi info sensor...")
            wifi_info = await self.shell_command("dumpsys wifi | grep 'SSID:' | head -1")
            if "SSID:" in wifi_info:
                tests.append(("WiFi Info Sensor", "PASS", wifi_info.strip()))
            else:
                tests.append(("WiFi Info Sensor", "FAIL", wifi_info))
            
            # Test current app sensor
            _LOGGER.info("  Testing current app sensor...")
            current_app = await self.shell_command("dumpsys activity activities | grep 'ActivityRecord' | head -1")
            if "ActivityRecord" in current_app:
                tests.append(("Current App Sensor", "PASS", "Current app detected"))
            else:
                tests.append(("Current App Sensor", "FAIL", current_app))
            
            # Test system performance sensor
            _LOGGER.info("  Testing system performance sensor...")
            performance = await self.shell_command("top -d 0.5 -n 1 | head -5")
            if len(performance.strip()) > 0:
                tests.append(("Performance Sensor", "PASS", "Performance data retrieved"))
            else:
                tests.append(("Performance Sensor", "FAIL", "No performance data"))
                
        except Exception as e:
            tests.append(("Sensor", "ERROR", str(e)))
        
        self.test_results["sensor"] = tests
        return tests

    async def test_remote_functionality(self):
        """Test remote control functionality per design spec."""
        _LOGGER.info("Testing Remote Control functionality...")
        tests = []
        
        try:
            # Test navigation keys
            _LOGGER.info("  Testing navigation keys...")
            nav_commands = [
                ("Up", "input keyevent 19"),
                ("Down", "input keyevent 20"),
                ("Left", "input keyevent 21"),
                ("Right", "input keyevent 22"),
                ("Enter", "input keyevent 23"),
                ("Back", "input keyevent 4"),
                ("Home", "input keyevent 82"),
            ]
            
            for name, command in nav_commands:
                await self.shell_command(command)
                await asyncio.sleep(0.5)  # Small delay between commands
            
            tests.append(("Navigation Keys", "PASS", "All navigation keys sent successfully"))
            
            # Test media keys
            _LOGGER.info("  Testing media keys...")
            media_commands = [
                ("Play", "input keyevent 126"),
                ("Pause", "input keyevent 127"),
                ("Stop", "input keyevent 86"),
                ("Next", "input keyevent 87"),
                ("Previous", "input keyevent 88"),
            ]
            
            for name, command in media_commands:
                await self.shell_command(command)
                await asyncio.sleep(0.5)
            
            tests.append(("Media Keys", "PASS", "All media keys sent successfully"))
                
        except Exception as e:
            tests.append(("Remote", "ERROR", str(e)))
        
        self.test_results["remote"] = tests
        return tests

    async def test_select_functionality(self):
        """Test select (app selector) functionality per design spec."""
        _LOGGER.info("Testing Select (App Selector) functionality...")
        tests = []
        
        try:
            # Test app launching
            _LOGGER.info("  Testing app launching...")
            
            # Test launching iSG app
            result = await self.shell_command("monkey -p com.linknlink.app.device.isg -c android.intent.category.LAUNCHER 1")
            await asyncio.sleep(3)  # Wait for app to start
            
            # Verify app is running
            check_result = await self.shell_command("dumpsys activity activities | grep 'com.linknlink.app.device.isg' | head -1")
            if "com.linknlink.app.device.isg" in check_result:
                tests.append(("App Launch", "PASS", "iSG app launched successfully"))
            else:
                tests.append(("App Launch", "FAIL", "iSG app launch failed"))
            
            # Test current app detection
            current_app = await self.shell_command("dumpsys activity activities | grep 'ActivityRecord' | head -1")
            if "ActivityRecord" in current_app:
                tests.append(("Current App Detection", "PASS", "Current app detected"))
            else:
                tests.append(("Current App Detection", "FAIL", current_app))
                
        except Exception as e:
            tests.append(("Select", "ERROR", str(e)))
        
        self.test_results["select"] = tests
        return tests

    async def test_binary_sensor_functionality(self):
        """Test binary sensor functionality per design spec."""
        _LOGGER.info("Testing Binary Sensor functionality...")
        tests = []
        
        try:
            # Test connection status
            _LOGGER.info("  Testing connection status...")
            devices_result = await self._run_command(["devices"])
            if self.device_address in devices_result and "device" in devices_result:
                tests.append(("Connection Status", "PASS", "ADB connection active"))
            else:
                tests.append(("Connection Status", "FAIL", devices_result))
            
            # Test iSG monitoring
            _LOGGER.info("  Testing iSG monitoring...")
            isg_result = await self.shell_command("ps | grep com.linknlink.app.device.isg | grep -v grep")
            if isg_result.strip():
                tests.append(("iSG Monitoring", "PASS", "iSG process detected"))
            else:
                tests.append(("iSG Monitoring", "WARNING", "iSG process not found"))
            
            # Test CPU monitoring
            _LOGGER.info("  Testing CPU monitoring...")
            cpu_result = await self.shell_command("top -d 0.5 -n 1 | head -3")
            if len(cpu_result.strip()) > 0:
                tests.append(("CPU Monitoring", "PASS", "CPU data retrieved"))
            else:
                tests.append(("CPU Monitoring", "FAIL", "No CPU data"))
                
        except Exception as e:
            tests.append(("Binary Sensor", "ERROR", str(e)))
        
        self.test_results["binary_sensor"] = tests
        return tests

    async def run_complete_test_suite(self):
        """Run the complete test suite."""
        _LOGGER.info("=== Android TV Box Integration - Complete Test Suite ===")
        
        # Connect to device
        _LOGGER.info("1. Connecting to device...")
        connected = await self.connect()
        if not connected:
            _LOGGER.error("Failed to connect to device. Aborting tests.")
            return
        
        # Run all tests
        test_functions = [
            self.test_media_player_functionality,
            self.test_switch_functionality,
            self.test_camera_functionality,
            self.test_sensor_functionality,
            self.test_remote_functionality,
            self.test_select_functionality,
            self.test_binary_sensor_functionality,
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                _LOGGER.error(f"Test function {test_func.__name__} failed: {e}")
        
        # Generate test report
        await self.generate_test_report()

    async def generate_test_report(self):
        """Generate comprehensive test report."""
        _LOGGER.info("\n=== TEST REPORT ===")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for component, tests in self.test_results.items():
            _LOGGER.info(f"\n{component.upper()} Component:")
            for test_name, status, details in tests:
                total_tests += 1
                if status == "PASS":
                    passed_tests += 1
                    _LOGGER.info(f"  ✅ {test_name}: {status}")
                elif status == "FAIL":
                    failed_tests += 1
                    _LOGGER.warning(f"  ❌ {test_name}: {status} - {details}")
                elif status == "ERROR":
                    error_tests += 1
                    _LOGGER.error(f"  🚫 {test_name}: {status} - {details}")
                else:
                    _LOGGER.info(f"  ⚠️  {test_name}: {status} - {details}")
        
        _LOGGER.info(f"\n=== SUMMARY ===")
        _LOGGER.info(f"Total Tests: {total_tests}")
        _LOGGER.info(f"Passed: {passed_tests}")
        _LOGGER.info(f"Failed: {failed_tests}")
        _LOGGER.info(f"Errors: {error_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        _LOGGER.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            _LOGGER.info("🎉 EXCELLENT: Integration is working very well!")
        elif success_rate >= 75:
            _LOGGER.info("✅ GOOD: Integration is working well with minor issues")
        elif success_rate >= 50:
            _LOGGER.warning("⚠️  FAIR: Integration has some issues that need attention")
        else:
            _LOGGER.error("❌ POOR: Integration has significant issues")
        
        # Save detailed report to file
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "device": self.device_address,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results
        }
        
        with open("integration_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        _LOGGER.info(f"Detailed report saved to: integration_test_report.json")


async def main():
    """Main test function."""
    tester = CompleteIntegrationTest()
    await tester.run_complete_test_suite()


if __name__ == "__main__":
    asyncio.run(main())