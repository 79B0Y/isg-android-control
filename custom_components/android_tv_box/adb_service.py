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
            cmd = ["-s", self.device_address, "shell", "sh", "-c", command]
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
            # Also use svc to improve reliability across Android versions
            try:
                await self.shell_command("svc wifi enable")
            except Exception:
                pass
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
            wifi_info = {"ssid": "Unknown", "ip_address": "Unknown"}
            
            # Get WiFi SSID with better parsing
            try:
                result = await self.shell_command("dumpsys wifi | grep 'SSID:' | head -1")
                if "SSID:" in result:
                    ssid_part = result.split("SSID:")[1].strip()
                    # Remove quotes and extra formatting
                    import re
                    ssid_match = re.search(r'"([^"]+)"', ssid_part)
                    if ssid_match:
                        wifi_info["ssid"] = ssid_match.group(1)
                    else:
                        # Fallback: take first word after SSID:
                        wifi_info["ssid"] = ssid_part.split(',')[0].strip().strip('"')
            except Exception as e:
                _LOGGER.debug(f"SSID extraction failed: {e}")
            
            # Get IP address with multiple interface support
            try:
                # Try wlan0 first
                result = await self.shell_command("ip addr show wlan0 | grep 'inet ' | head -1")
                if "inet " not in result:
                    # Try other wireless interfaces
                    result = await self.shell_command("ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1")
                
                if "inet " in result:
                    import re
                    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result)
                    if ip_match:
                        wifi_info["ip_address"] = ip_match.group(1)
            except Exception as e:
                _LOGGER.debug(f"IP address extraction failed: {e}")
            
            return wifi_info
        except Exception as e:
            _LOGGER.error(f"Get WiFi info failed: {e}")
            return {"ssid": "Unknown", "ip_address": "Unknown"}

    async def reboot_device(self) -> bool:
        """Reboot Android device via ADB."""
        try:
            # Using shell reboot allows us to reuse shell_command mechanics
            await self.shell_command("reboot")
            self._connected = False
            return True
        except Exception as e:
            _LOGGER.error(f"Reboot failed: {e}")
            return False

    async def get_playback_state(self) -> Optional[str]:
        """Get media playback state using dumpsys media_session.

        Tries to mirror the logic of an awk-based filter that scans the
        Sessions Stack for active sessions and extracts symbolic state names
        like PLAYING/PAUSED. Falls back to numeric codes when needed.

        Returns: 'playing', 'paused', 'stopped', 'idle' or None.
        """
        try:
            # Get current foreground app to prefer its session if present
            try:
                current_pkg = await self.get_current_app()
            except Exception:
                current_pkg = None

            raw = await self.shell_command("dumpsys media_session", timeout=8)
            lines = raw.split("\n")

            in_stack = False
            active = False
            # We parse sequentially; once we locate an active session with a
            # PlaybackState line, we extract and return the first match.
            import re
            # 1) Prefer session block near the current foreground package
            if current_pkg:
                try:
                    import re
                    # Search for the line index that mentions the package
                    pkg_indices = [i for i, ln in enumerate(lines) if current_pkg in ln or re.search(rf"package[= ]{re.escape(current_pkg)}\b", ln)]
                    for idx in pkg_indices:
                        # Look ahead within a small window for active flag and PlaybackState
                        window = lines[idx:idx+30]
                        active = any("active=true" in w.replace(" ", "") for w in window)
                        if not active:
                            continue
                        sym = None
                        num = None
                        for w in window:
                            if "state=PlaybackState" not in w:
                                continue
                            # Symbolic formats
                            m_sym_paren = re.search(r"state=([A-Z_]+)\((\d+)\)", w)
                            m_sym_state = re.search(r"state=STATE_([A-Z_]+)", w)
                            m_sym_plain = re.search(r"PlaybackState\s*\{\s*state=([A-Z_]+)\b", w)
                            if m_sym_paren:
                                sym = m_sym_paren.group(1).upper()
                            elif m_sym_state:
                                sym = m_sym_state.group(1).upper()
                            elif m_sym_plain:
                                sym = m_sym_plain.group(1).upper()
                            # Numeric fallback
                            m_num = re.search(r"state=(\d+)", w)
                            if m_num:
                                num = int(m_num.group(1))
                            if sym or num is not None:
                                mapped = self._map_playback_symbol_or_code(sym, num)
                                if mapped:
                                    return mapped
                        # If we didn't find state in this window, continue to next candidate
                except Exception:
                    pass

            # 2) Fallback: scan Sessions Stack for the first active session
            for line in lines:
                if not in_stack and "Sessions Stack" in line:
                    in_stack = True
                    active = False
                    continue

                if not in_stack:
                    continue

                # Track activity flag within the stack block
                if "active=" in line:
                    try:
                        active = "active=true" in line.replace(" ", "")
                    except Exception:
                        active = False

                # Only consider PlaybackState lines when active
                if "state=PlaybackState" in line and active:
                    # Recognize several formats
                    m_sym_paren = re.search(r"state=([A-Z_]+)\((\d+)\)", line)
                    m_sym_state = re.search(r"state=STATE_([A-Z_]+)", line)
                    m_sym_plain = re.search(r"PlaybackState\s*\{\s*state=([A-Z_]+)\b", line)
                    symbol = None
                    code = None
                    if m_sym_paren:
                        symbol = m_sym_paren.group(1).upper()
                        code = int(m_sym_paren.group(2))
                    elif m_sym_state:
                        symbol = m_sym_state.group(1).upper()
                    elif m_sym_plain:
                        symbol = m_sym_plain.group(1).upper()
                    else:
                        m_num = re.search(r"state=(\d+)", line)
                        if m_num:
                            code = int(m_num.group(1))
                    mapped = self._map_playback_symbol_or_code(symbol, code)
                    if mapped:
                        return mapped
                    # If we reached here but couldn't map, continue scanning

            return None
        except Exception as e:
            _LOGGER.debug(f"Get playback state failed: {e}")
            return None

    def _map_playback_symbol_or_code(self, symbol: Optional[str], code: Optional[int]) -> Optional[str]:
        """Map symbolic or numeric playback state to our canonical strings."""
        try:
            if symbol:
                s = symbol.upper()
                if s in ("PLAYING", "STATE_PLAYING"):
                    return "playing"
                if s in ("PAUSED", "STATE_PAUSED"):
                    return "paused"
                if s in ("STOPPED", "STATE_STOPPED"):
                    return "stopped"
                if s in ("NONE", "IDLE", "STATE_NONE", "STATE_IDLE"):
                    return "idle"
            if code is not None:
                if code == 3:
                    return "playing"
                if code == 2:
                    return "paused"
                if code == 1:
                    return "stopped"
                if code == 0:
                    return "idle"
        except Exception:
            pass
        return None

    async def get_current_app(self) -> Optional[str]:
        """Get current foreground app."""
        try:
            # Try multiple methods to get current app
            result = await self.shell_command("dumpsys activity activities | grep 'ActivityRecord' | head -1")
            if "ActivityRecord" in result:
                # Extract package name from the output
                import re
                # Look for package name pattern (com.example.app format)
                package_match = re.search(r'([a-zA-Z0-9_.]+)/[a-zA-Z0-9_.]+', result)
                if package_match:
                    return package_match.group(1)
                
                # Fallback: original parsing method
                parts = result.split()
                for part in parts:
                    if "/" in part and "." in part and not part.startswith("{"):
                        return part.split("/")[0]
            
            # Alternative method using top activity
            try:
                result = await self.shell_command("dumpsys activity top | grep 'ACTIVITY' | head -1")
                if "ACTIVITY" in result:
                    import re
                    package_match = re.search(r'([a-zA-Z0-9_.]+)/[a-zA-Z0-9_.]+', result)
                    if package_match:
                        return package_match.group(1)
            except Exception:
                pass
            
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

    async def force_stop_app(self, package_name: str) -> bool:
        """Force-stop an app by package name."""
        try:
            await self.shell_command(f"am force-stop {package_name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Force stop app failed: {e}")
            return False

    async def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics from top command."""
        try:
            # Initialize performance data
            performance = {
                "cpu_usage_percent": 0.0,
                "memory_usage_percent": 0.0,
                "memory_total_mb": 0,
                "memory_used_mb": 0,
                "highest_cpu_process": None,
                "highest_cpu_pid": None,
                "highest_cpu_percent": 0.0,
                "highest_cpu_service": None
            }
            
            # Get top output
            result = await self.shell_command("top -d 0.5 -n 1", timeout=5)
            lines = result.split('\n')
            
            # Parse CPU usage - Android device format: "400%cpu  98%user   0%nice 207%sys  79%idle"
            for line in lines:
                if "%cpu" in line.lower() and "%user" in line:
                    import re
                    # Extract user and sys percentages
                    user_match = re.search(r'(\d+)%user', line)
                    sys_match = re.search(r'(\d+)%sys', line)
                    
                    if user_match and sys_match:
                        user_cpu = float(user_match.group(1))
                        sys_cpu = float(sys_match.group(1))
                        # This device shows cumulative values for all cores, estimate total cores
                        total_cores = 4  # Typical for Android devices
                        total_cpu = (user_cpu + sys_cpu) / total_cores
                        performance["cpu_usage_percent"] = round(total_cpu, 1)
                    break
            
            # Parse Memory usage - Android format: "Mem:  4006164K total,  3660916K used,   345248K free"
            for line in lines:
                if "Mem:" in line and "total" in line:
                    import re
                    # Extract memory values in KB
                    total_match = re.search(r'(\d+)K total', line)
                    used_match = re.search(r'(\d+)K used', line)
                    
                    if total_match and used_match:
                        total_kb = float(total_match.group(1))
                        used_kb = float(used_match.group(1))
                        total_mb = round(total_kb / 1024, 1)
                        used_mb = round(used_kb / 1024, 1)
                        usage_percent = round((used_kb / total_kb) * 100, 1)
                        
                        performance["memory_total_mb"] = total_mb
                        performance["memory_used_mb"] = used_mb
                        performance["memory_usage_percent"] = usage_percent
                    break
            
            # Parse highest CPU process from process list
            process_started = False
            for line in lines:
                # Skip header lines until we reach the process list
                if "PID USER" in line and "%CPU" in line:
                    process_started = True
                    continue
                
                if process_started and line.strip():
                    import re
                    # Clean ANSI escape sequences
                    clean_line = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', line)
                    parts = clean_line.split()
                    
                    if len(parts) >= 11:
                        try:
                            pid = parts[0]
                            cpu_str = parts[8]  # %CPU column (after S column)
                            command = parts[-1] if len(parts) > 10 else "unknown"
                            
                            # Handle CPU percentage
                            cpu_percent = 0.0
                            if cpu_str.replace('.', '').isdigit():
                                cpu_percent = float(cpu_str)
                            
                            if cpu_percent > performance["highest_cpu_percent"]:
                                performance["highest_cpu_pid"] = pid
                                performance["highest_cpu_percent"] = round(cpu_percent, 1)
                                performance["highest_cpu_process"] = command
                            
                            # Only check first few processes (they are sorted by CPU usage)
                            if performance["highest_cpu_percent"] > 0:
                                break
                                
                        except (ValueError, IndexError):
                            continue
            
            # Get service name for highest CPU process if PID is available
            if performance["highest_cpu_pid"]:
                try:
                    service_name = await self._get_service_name_by_pid(performance["highest_cpu_pid"])
                    performance["highest_cpu_service"] = service_name
                except Exception as e:
                    _LOGGER.debug(f"Failed to get service name for PID {performance['highest_cpu_pid']}: {e}")
            
            return performance
            
        except Exception as e:
            _LOGGER.error(f"Get system performance failed: {e}")
            return {
                "cpu_usage_percent": 0.0,
                "memory_usage_percent": 0.0,
                "memory_total_mb": 0,
                "memory_used_mb": 0,
                "highest_cpu_process": None,
                "highest_cpu_pid": None,
                "highest_cpu_percent": 0.0,
                "highest_cpu_service": None
            }

    async def _get_service_name_by_pid(self, pid: str) -> Optional[str]:
        """Get service name by process ID."""
        try:
            # Try to get process info from /proc/PID/cmdline
            result = await self.shell_command(f"cat /proc/{pid}/cmdline")
            if result and result.strip():
                # cmdline contains null-separated command line arguments
                cmdline = result.replace('\x00', ' ').strip()
                if cmdline:
                    # Extract the main command/service name
                    service_name = cmdline.split()[0]
                    # Get just the filename without path
                    if '/' in service_name:
                        service_name = service_name.split('/')[-1]
                    return service_name
            
            # Fallback: try ps command
            result = await self.shell_command(f"ps -p {pid} -o comm=")
            if result and result.strip():
                return result.strip()
            
            # Another fallback: try ps aux
            result = await self.shell_command(f"ps aux | grep {pid} | grep -v grep | head -1")
            if result and result.strip():
                parts = result.split()
                if len(parts) >= 11:
                    # The command is usually in the last column
                    command = parts[10]
                    if '/' in command:
                        command = command.split('/')[-1]
                    return command
            
            return None
            
        except Exception as e:
            _LOGGER.debug(f"Failed to get service name for PID {pid}: {e}")
            return None

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
