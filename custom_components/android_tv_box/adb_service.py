"""ADB connection service for Android TV Box integration."""
import asyncio
import logging
import subprocess
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)


class ADBConnectionError(Exception):
    """Exception raised for ADB connection errors."""
    pass


class ADBService:
    """Service for managing ADB connections and executing commands."""

    def __init__(self, host: str, port: int, adb_path: str = "/usr/bin/adb"):
        """Initialize ADB service."""
        self.host = host
        self.port = port
        self.adb_path = adb_path
        self.device_address = f"{host}:{port}"
        self._connected = False
        self._last_command_time = 0
        self._command_delay = 0.1  # Minimum delay between commands

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

    async def disconnect(self):
        """Disconnect from ADB device."""
        try:
            await self._run_command(["disconnect", self.device_address])
            self._connected = False
            _LOGGER.info(f"Disconnected from {self.device_address}")
        except Exception as e:
            _LOGGER.error(f"Error disconnecting from ADB: {e}")

    async def is_connected(self) -> bool:
        """Check if device is connected."""
        try:
            result = await self._run_command(["devices"])
            return self.device_address in result and "device" in result
        except Exception:
            return False

    async def shell_command(self, command: str, timeout: int = 10) -> str:
        """Execute shell command on device."""
        if not self._connected:
            if not await self.connect():
                raise ADBConnectionError("Device not connected")

        # Add delay between commands to avoid overwhelming the device
        current_time = time.time()
        if current_time - self._last_command_time < self._command_delay:
            await asyncio.sleep(self._command_delay - (current_time - self._last_command_time))
        
        self._last_command_time = time.time()

        try:
            cmd = ["-s", self.device_address, "shell"] + command.split()
            result = await self._run_command(cmd, timeout=timeout)
            return result.strip()
        except subprocess.TimeoutExpired:
            _LOGGER.error(f"ADB command timeout: {command}")
            raise ADBConnectionError(f"Command timeout: {command}")
        except Exception as e:
            _LOGGER.error(f"ADB command error: {e}")
            raise ADBConnectionError(f"Command failed: {command}")

    async def _run_command(self, cmd: List[str], timeout: int = 10) -> str:
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
                raise ADBConnectionError(f"Command failed: {error_msg}")
            
            return result
        except asyncio.TimeoutError:
            process.kill()
            raise subprocess.TimeoutExpired(full_cmd, timeout)

    # Media Player Commands
    async def media_play(self) -> bool:
        """Start media playback."""
        try:
            await self.shell_command("input keyevent 126")
            return True
        except Exception as e:
            _LOGGER.error(f"Media play failed: {e}")
            return False

    async def media_pause(self) -> bool:
        """Pause media playback."""
        try:
            await self.shell_command("input keyevent 127")
            return True
        except Exception as e:
            _LOGGER.error(f"Media pause failed: {e}")
            return False

    async def media_stop(self) -> bool:
        """Stop media playback."""
        try:
            await self.shell_command("input keyevent 86")
            return True
        except Exception as e:
            _LOGGER.error(f"Media stop failed: {e}")
            return False

    async def media_play_pause(self) -> bool:
        """Toggle play/pause."""
        try:
            await self.shell_command("input keyevent 85")
            return True
        except Exception as e:
            _LOGGER.error(f"Media play/pause failed: {e}")
            return False

    async def media_next(self) -> bool:
        """Next media item."""
        try:
            await self.shell_command("input keyevent 87")
            return True
        except Exception as e:
            _LOGGER.error(f"Media next failed: {e}")
            return False

    async def media_previous(self) -> bool:
        """Previous media item."""
        try:
            await self.shell_command("input keyevent 88")
            return True
        except Exception as e:
            _LOGGER.error(f"Media previous failed: {e}")
            return False

    # Volume Commands
    async def volume_up(self) -> bool:
        """Increase volume."""
        try:
            await self.shell_command("input keyevent 24")
            return True
        except Exception as e:
            _LOGGER.error(f"Volume up failed: {e}")
            return False

    async def volume_down(self) -> bool:
        """Decrease volume."""
        try:
            await self.shell_command("input keyevent 25")
            return True
        except Exception as e:
            _LOGGER.error(f"Volume down failed: {e}")
            return False

    async def volume_mute(self) -> bool:
        """Toggle mute."""
        try:
            await self.shell_command("input keyevent 164")
            return True
        except Exception as e:
            _LOGGER.error(f"Volume mute failed: {e}")
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        try:
            # Convert percentage to Android volume level (0-15)
            android_volume = int((volume / 100) * 15)
            await self.shell_command(f"service call audio 12 i32 3 i32 {android_volume} i32 0")
            return True
        except Exception as e:
            _LOGGER.error(f"Set volume failed: {e}")
            return False

    async def get_volume(self) -> Optional[int]:
        """Get current volume level."""
        try:
            result = await self.shell_command("cmd media_session volume --stream 3 --get")
            if "volume is" in result:
                # Parse volume from output like "volume is 8 in range [0..15]"
                volume_str = result.split("volume is")[1].split()[0]
                volume = int(volume_str)
                # Convert to percentage
                return int((volume / 15) * 100)
            return None
        except Exception as e:
            _LOGGER.error(f"Get volume failed: {e}")
            return None

    # Power Commands
    async def power_on(self) -> bool:
        """Wake up device."""
        try:
            await self.shell_command("input keyevent 224")
            return True
        except Exception as e:
            _LOGGER.error(f"Power on failed: {e}")
            return False

    async def power_off(self) -> bool:
        """Put device to sleep."""
        try:
            await self.shell_command("input keyevent 26")
            return True
        except Exception as e:
            _LOGGER.error(f"Power off failed: {e}")
            return False

    async def is_powered_on(self) -> bool:
        """Check if device is powered on."""
        try:
            result = await self.shell_command("dumpsys power | grep -E '(mWakefulness|mScreenOn)'")
            return "Awake" in result or "mScreenOn=true" in result
        except Exception as e:
            _LOGGER.error(f"Check power status failed: {e}")
            return False

    # WiFi Commands
    async def wifi_on(self) -> bool:
        """Enable WiFi."""
        try:
            await self.shell_command("settings put global wifi_on 1")
            return True
        except Exception as e:
            _LOGGER.error(f"WiFi on failed: {e}")
            return False

    async def wifi_off(self) -> bool:
        """Disable WiFi."""
        try:
            await self.shell_command("settings put global wifi_on 0")
            return True
        except Exception as e:
            _LOGGER.error(f"WiFi off failed: {e}")
            return False

    async def is_wifi_on(self) -> bool:
        """Check if WiFi is enabled."""
        try:
            result = await self.shell_command("settings get global wifi_on")
            return result.strip() == "1"
        except Exception as e:
            _LOGGER.error(f"Check WiFi status failed: {e}")
            return False

    # Remote Control Commands
    async def key_up(self) -> bool:
        """Send up key."""
        try:
            await self.shell_command("input keyevent 19")
            return True
        except Exception as e:
            _LOGGER.error(f"Key up failed: {e}")
            return False

    async def key_down(self) -> bool:
        """Send down key."""
        try:
            await self.shell_command("input keyevent 20")
            return True
        except Exception as e:
            _LOGGER.error(f"Key down failed: {e}")
            return False

    async def key_left(self) -> bool:
        """Send left key."""
        try:
            await self.shell_command("input keyevent 21")
            return True
        except Exception as e:
            _LOGGER.error(f"Key left failed: {e}")
            return False

    async def key_right(self) -> bool:
        """Send right key."""
        try:
            await self.shell_command("input keyevent 22")
            return True
        except Exception as e:
            _LOGGER.error(f"Key right failed: {e}")
            return False

    async def key_enter(self) -> bool:
        """Send enter key."""
        try:
            await self.shell_command("input keyevent 23")
            return True
        except Exception as e:
            _LOGGER.error(f"Key enter failed: {e}")
            return False

    async def key_back(self) -> bool:
        """Send back key."""
        try:
            await self.shell_command("input keyevent 4")
            return True
        except Exception as e:
            _LOGGER.error(f"Key back failed: {e}")
            return False

    async def key_home(self) -> bool:
        """Send home key."""
        try:
            await self.shell_command("input keyevent 82")
            return True
        except Exception as e:
            _LOGGER.error(f"Key home failed: {e}")
            return False

    # System Commands
    async def take_screenshot(self, filepath: str) -> bool:
        """Take screenshot and save to filepath."""
        try:
            await self.shell_command(f"screencap -p {filepath}")
            return True
        except Exception as e:
            _LOGGER.error(f"Screenshot failed: {e}")
            return False

    async def set_brightness(self, brightness: int) -> bool:
        """Set screen brightness (0-255)."""
        try:
            await self.shell_command(f"settings put system screen_brightness {brightness}")
            return True
        except Exception as e:
            _LOGGER.error(f"Set brightness failed: {e}")
            return False

    async def get_brightness(self) -> Optional[int]:
        """Get current screen brightness."""
        try:
            result = await self.shell_command("settings get system screen_brightness")
            return int(result.strip())
        except Exception as e:
            _LOGGER.error(f"Get brightness failed: {e}")
            return None

    async def get_wifi_info(self) -> Dict[str, Any]:
        """Get WiFi information."""
        try:
            wifi_info = {}
            
            # Get WiFi SSID
            result = await self.shell_command("dumpsys wifi | grep 'SSID:' | head -1")
            if "SSID:" in result:
                wifi_info["ssid"] = result.split("SSID:")[1].strip()
            
            # Get IP address
            result = await self.shell_command("ip addr show wlan0 | grep 'inet '")
            if "inet " in result:
                ip = result.split("inet ")[1].split("/")[0]
                wifi_info["ip_address"] = ip
            
            return wifi_info
        except Exception as e:
            _LOGGER.error(f"Get WiFi info failed: {e}")
            return {}

    async def get_current_app(self) -> Optional[str]:
        """Get current foreground app."""
        try:
            result = await self.shell_command("dumpsys activity activities | grep 'ActivityRecord' | head -1")
            if "ActivityRecord" in result:
                # Extract package name from the output
                parts = result.split()
                for part in parts:
                    if "/" in part and "." in part:
                        return part.split("/")[0]
            return None
        except Exception as e:
            _LOGGER.error(f"Get current app failed: {e}")
            return None

    async def launch_app(self, package_name: str, activity_name: Optional[str] = None) -> bool:
        """Launch an app."""
        try:
            if activity_name:
                await self.shell_command(f"am start {package_name}/{activity_name}")
            else:
                await self.shell_command(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
            return True
        except Exception as e:
            _LOGGER.error(f"Launch app failed: {e}")
            return False

    async def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            result = await self.shell_command("top -d 0.5 -n 1")
            performance = {}
            
            # Parse CPU and memory info from top output
            lines = result.split('\n')
            for line in lines:
                if "CPU:" in line:
                    # Extract CPU usage
                    cpu_parts = line.split()
                    for i, part in enumerate(cpu_parts):
                        if part == "CPU:" and i + 1 < len(cpu_parts):
                            cpu_usage = cpu_parts[i + 1].replace('%', '')
                            try:
                                performance["cpu_usage"] = float(cpu_usage)
                            except ValueError:
                                pass
                
                if "Mem:" in line:
                    # Extract memory info
                    mem_parts = line.split()
                    for i, part in enumerate(mem_parts):
                        if part == "Mem:" and i + 1 < len(mem_parts):
                            try:
                                mem_info = mem_parts[i + 1].split('/')
                                if len(mem_info) == 2:
                                    performance["memory_used"] = int(mem_info[0])
                                    performance["memory_total"] = int(mem_info[1])
                            except (ValueError, IndexError):
                                pass
            
            return performance
        except Exception as e:
            _LOGGER.error(f"Get system performance failed: {e}")
            return {}

    async def kill_process(self, process_id: int) -> bool:
        """Kill a process by ID."""
        try:
            await self.shell_command(f"kill {process_id}")
            return True
        except Exception as e:
            _LOGGER.error(f"Kill process failed: {e}")
            return False

    # iSG Monitoring Commands
    async def is_isg_running(self) -> bool:
        """Check if iSG app is running."""
        try:
            result = await self.shell_command("ps | grep com.linknlink.app.device.isg | grep -v grep")
            return bool(result.strip())
        except Exception as e:
            _LOGGER.error(f"Check iSG running failed: {e}")
            return False

    async def get_isg_process_info(self) -> Dict[str, Any]:
        """Get iSG process information."""
        try:
            result = await self.shell_command("ps | grep com.linknlink.app.device.isg | grep -v grep")
            if result.strip():
                parts = result.strip().split()
                if len(parts) >= 2:
                    return {
                        "pid": int(parts[1]),
                        "running": True,
                        "process_info": result.strip()
                    }
            return {"pid": None, "running": False, "process_info": ""}
        except Exception as e:
            _LOGGER.error(f"Get iSG process info failed: {e}")
            return {"pid": None, "running": False, "process_info": ""}

    async def wake_up_isg(self) -> bool:
        """Wake up iSG app if it's not running."""
        try:
            # First check if it's running
            if await self.is_isg_running():
                _LOGGER.info("iSG is already running")
                return True
            
            # Launch iSG app
            _LOGGER.info("iSG is not running, launching...")
            success = await self.launch_app("com.linknlink.app.device.isg")
            
            if success:
                _LOGGER.info("iSG launched successfully")
                # Wait a moment for the app to start
                await asyncio.sleep(3)
                # Verify it's running
                if await self.is_isg_running():
                    _LOGGER.info("iSG is now running")
                    return True
                else:
                    _LOGGER.warning("iSG launch may have failed")
                    return False
            else:
                _LOGGER.error("Failed to launch iSG")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Wake up iSG failed: {e}")
            return False

    async def restart_isg(self) -> bool:
        """Restart iSG app."""
        try:
            _LOGGER.info("Restarting iSG app...")
            
            # Kill existing iSG processes
            result = await self.shell_command("ps | grep com.linknlink.app.device.isg | grep -v grep")
            if result.strip():
                pids = []
                for line in result.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            pids.append(parts[1])
                
                for pid in pids:
                    try:
                        await self.shell_command(f"kill {pid}")
                        _LOGGER.info(f"Killed iSG process {pid}")
                    except Exception as e:
                        _LOGGER.warning(f"Failed to kill iSG process {pid}: {e}")
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Launch iSG again
            success = await self.launch_app("com.linknlink.app.device.isg")
            
            if success:
                _LOGGER.info("iSG restarted successfully")
                await asyncio.sleep(3)
                return await self.is_isg_running()
            else:
                _LOGGER.error("Failed to restart iSG")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Restart iSG failed: {e}")
            return False
