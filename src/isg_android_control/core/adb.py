from __future__ import annotations

import asyncio
import tempfile
import os
from typing import List, Optional, Dict, Any
import re
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ADBError(Exception):
    """Custom exception for ADB-related errors."""
    pass


class ADBTimeoutError(ADBError):
    """Exception raised when ADB commands timeout."""
    pass


class ADBConnectionError(ADBError):
    """Exception raised when ADB connection fails."""
    pass


class ADBController:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        serial: Optional[str] = None,
        has_battery: bool = False,
        has_cellular: bool = False,
        connection_timeout: float = 300.0  # 5 minutes default
    ) -> None:
        self.host = host
        self.port = port
        self.serial = serial
        self.has_battery = has_battery
        self.has_cellular = has_cellular
        self.connection_timeout = connection_timeout

        # Connection state management
        self._connected = False
        self._connection_lock = asyncio.Lock()
        self._last_activity: Optional[datetime] = None
        self._disconnect_task: Optional[asyncio.Task] = None

    def _target(self) -> List[str]:
        if self.serial:
            return ["-s", self.serial]
        # For localhost connections in Android box environment, 
        # try without -s parameter first if it's 127.0.0.1
        if self.host == "127.0.0.1" or self.host == "localhost":
            return []  # Let ADB auto-select the device
        return ["-s", f"{self.host}:{self.port}"]

    def _update_activity(self) -> None:
        """Update last activity timestamp and reset disconnect timer."""
        self._last_activity = datetime.now()

        # Cancel existing disconnect task and schedule a new one
        if self._disconnect_task and not self._disconnect_task.done():
            self._disconnect_task.cancel()

        if self._connected:
            self._disconnect_task = asyncio.create_task(self._auto_disconnect())

    async def _auto_disconnect(self) -> None:
        """Automatically disconnect after inactivity timeout."""
        try:
            await asyncio.sleep(self.connection_timeout)

            # Check if we're still inactive
            if (self._last_activity and
                datetime.now() - self._last_activity >= timedelta(seconds=self.connection_timeout)):
                logger.info("Auto-disconnecting ADB after %ds of inactivity", self.connection_timeout)
                await self.disconnect()
        except asyncio.CancelledError:
            # Task was cancelled, which is normal when activity occurs
            pass
        except Exception as e:
            logger.error("Error in auto-disconnect: %s", e)

    async def disconnect(self) -> None:
        """Disconnect from ADB device."""
        async with self._connection_lock:
            if not self._connected:
                return

            try:
                # If using host:port connection, explicitly disconnect
                target = self.serial or f"{self.host}:{self.port}"
                if ":" in target:
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            "adb", "disconnect", target,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

                        if proc.returncode == 0:
                            logger.info("ADB disconnected from %s", target)
                        else:
                            logger.warning("ADB disconnect returned code %d: %s",
                                         proc.returncode, stderr.decode())
                    except Exception as e:
                        logger.debug("Error disconnecting from %s: %s", target, e)

                self._connected = False
                self._last_activity = None

                # Cancel disconnect task
                if self._disconnect_task and not self._disconnect_task.done():
                    self._disconnect_task.cancel()
                    self._disconnect_task = None

            except Exception as e:
                logger.error("Error during disconnect: %s", e)

    async def ensure_connected(self) -> None:
        """Ensure ADB connection is established on-demand."""
        async with self._connection_lock:
            if self._connected:
                self._update_activity()
                return

            # Establish connection
            await self._connect_internal()
            self._connected = True
            self._update_activity()

    async def _connect_internal(self) -> str:
        """Internal connection logic (same as original connect method)."""
        # If an explicit serial is provided, try to ensure it's ready.
        # If the serial looks like host:port, attempt a direct `adb connect`.
        if self.serial:
            logger.info("Using ADB serial: %s", self.serial)
            # Ensure adb server is up to avoid concurrent startup races
            try:
                proc = await asyncio.create_subprocess_exec(
                    "adb", "start-server",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=8.0)
            except Exception as e:
                logger.debug("adb start-server failed/ignored: %s", e)

            # If serial is a host:port, try to connect explicitly
            if ":" in self.serial:
                try:
                    proc2 = await asyncio.create_subprocess_exec(
                        "adb", "connect", self.serial,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await asyncio.wait_for(proc2.communicate(), timeout=8.0)
                except Exception as e:
                    logger.debug("adb connect %s failed/ignored: %s", self.serial, e)

            # Wait for device best-effort
            try:
                await self._run_without_ensure("wait-for-device", timeout=12.0)
            except Exception as e:
                logger.debug("wait-for-device for %s not ready yet: %s", self.serial, e)
            return "Using serial connection"

        # Use host:port pattern for connection
        target = f"{self.host}:{self.port}"
        logger.info("Connecting to ADB at %s", target)

        # For localhost connections in Android box environment, 
        # skip explicit connect as device may already be available
        if self.host == "127.0.0.1" or self.host == "localhost":
            logger.info("Skipping explicit connect for localhost - checking device availability")
            try:
                # Just check if device is available
                await self._run_without_ensure("shell", "echo", "connection_test", timeout=5.0)
                logger.info("Localhost device is available")
                return "Using localhost device"
            except Exception as e:
                logger.debug("Localhost device not immediately available, trying explicit connect: %s", e)
                # Fall through to explicit connect

        try:
            # Run host-level connect WITHOUT selecting a transport
            proc = await asyncio.create_subprocess_exec(
                "adb", "connect", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB buffer limit
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=12.0)
            result = stdout.decode('utf-8', errors='replace').strip()

            if ("connected" in result.lower()) or ("already connected" in result.lower()):
                logger.info("ADB connected to %s", target)
            else:
                logger.warning("ADB connect returned: %s", result)

            # Best-effort wait for device readiness
            try:
                await self._run_without_ensure("wait-for-device", timeout=8.0)
            except Exception as e:
                logger.debug("wait-for-device not ready yet after connect: %s", e)

            return result

        except asyncio.TimeoutError:
            logger.error("ADB connect to %s timed out", target)
            raise ADBConnectionError(f"Connect timeout to {target}")
        except Exception as e:
            logger.error("Unexpected error during ADB connect to %s: %s", target, e)
            raise ADBConnectionError(f"Connect failed: {e}") from e

    async def _run_without_ensure(self, *args: str, timeout: float = 15.0) -> str:
        """Execute ADB command without ensuring connection (used internally)."""
        cmd = ["adb", *self._target(), *args]
        cmd_str = " ".join(cmd)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB buffer limit
            )
        except OSError as e:
            logger.error("Failed to start ADB process: %s", e)
            raise ADBConnectionError(f"Failed to start ADB: {e}") from e

        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("ADB command timed out after %ss: %s", timeout, cmd_str)
            proc.kill()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.error("Failed to kill timed out ADB process: %s", cmd_str)
            raise ADBTimeoutError(f"ADB command timed out: {cmd_str}")
        except Exception as e:
            logger.error("Unexpected error during ADB execution: %s", e)
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            raise ADBError(f"ADB execution failed: {e}") from e

        if proc.returncode != 0:
            stderr_text = err.decode('utf-8', errors='replace').strip()
            stdout_text = out.decode('utf-8', errors='replace').strip()

            # Check for various error conditions
            lower_err = stderr_text.lower()
            if ("device offline" in lower_err) or ("device not found" in lower_err):
                raise ADBConnectionError(f"Device connection failed: {stderr_text}")
            elif "permission denied" in stderr_text.lower():
                logger.error("ADB permission denied: %s", stderr_text)
                raise ADBError(f"Permission denied: {stderr_text}")
            else:
                logger.error("ADB command failed (exit %d): %s -> stderr: %s, stdout: %s",
                           proc.returncode, cmd_str, stderr_text, stdout_text)
                raise ADBError(f"ADB failed (exit {proc.returncode}): {stderr_text or stdout_text}")

        return out.decode('utf-8', errors='replace')

    async def _run(self, *args: str, timeout: float = 15.0, _retry: bool = True) -> str:
        """Execute ADB command with on-demand connection and improved error handling.

        Automatically ensures connection before running commands, and handles
        connection errors with retry logic.
        """
        # Ensure we're connected before running the command
        await self.ensure_connected()

        try:
            # Use the internal method to actually run the command
            result = await self._run_without_ensure(*args, timeout=timeout)
            # Update activity after successful command
            self._update_activity()
            return result

        except ADBConnectionError as e:
            # Handle connection failures with retry logic
            if _retry:
                logger.warning("Connection failed, attempting reconnect: %s", e)
                try:
                    # Force disconnect and reconnect
                    self._connected = False
                    await self.ensure_connected()
                    # Retry the command once
                    result = await self._run_without_ensure(*args, timeout=timeout)
                    self._update_activity()
                    return result
                except Exception as retry_e:
                    logger.error("Reconnect and retry failed: %s", retry_e)
                    raise e from retry_e
            else:
                raise e

    async def connect(self) -> str:
        """Backward-compatible connect method (now uses on-demand connection)."""
        await self.ensure_connected()
        target = self.serial or f"{self.host}:{self.port}"
        return f"Connected to {target}"

    def is_connected(self) -> bool:
        """Check if ADB is currently connected."""
        return self._connected

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status information."""
        return {
            'connected': self._connected,
            'host': self.host,
            'port': self.port,
            'serial': self.serial,
            'last_activity': self._last_activity.isoformat() if self._last_activity else None,
            'connection_timeout': self.connection_timeout
        }

    async def keyevent(self, code: int) -> None:
        await self._run("shell", "input", "keyevent", str(code))

    async def nav(self, action: str) -> None:
        mapping = {
            "up": 19, "down": 20, "left": 21, "right": 22,
            "center": 23, "ok": 23, "enter": 66,
            "back": 4, "home": 3,
        }
        code = mapping.get(action.lower())
        if code is None:
            raise ValueError(f"unsupported nav action: {action}")
        await self.keyevent(code)

    async def volume(self, direction: str) -> None:
        mapping = {"up": 24, "down": 25, "mute": 164}
        code = mapping.get(direction.lower())
        if code is None:
            raise ValueError("volume direction must be up/down/mute")
        await self.keyevent(code)

    async def audio_music_info(self) -> dict:
        """Return current/max for STREAM_MUSIC by parsing dumpsys audio with improved parsing."""
        try:
            # Use dumpsys with timeout flag for better reliability
            out = await self._run("shell", "dumpsys", "-t", "5", "audio", timeout=10.0)
        except Exception:
            # Fallback without timeout flag
            out = await self._run("shell", "dumpsys", "audio", timeout=10.0)
        
        cur = None
        maxv = None
        lines = out.splitlines()
        
        # Find STREAM_MUSIC section and parse using improved logic
        in_music_block = False
        for line in lines:
            line = line.strip()
            
            # Start of STREAM_MUSIC block
            if "- STREAM_MUSIC:" in line:
                in_music_block = True
                continue
            
            # End of block (next stream starts)
            if in_music_block and line.startswith("- STREAM_") and "STREAM_MUSIC" not in line:
                break
                
            if in_music_block:
                # Look for Max value
                if "Max:" in line:
                    try:
                        maxv = int(line.split("Max:")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                # Look for streamVolume (preferred) or Current values
                if "streamVolume:" in line:
                    try:
                        cur = int(line.split("streamVolume:")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "Current:" in line:
                    # Try to extract speaker or default volume
                    if "(speaker):" in line:
                        m = re.search(r'\(speaker\):\s*(\d+)', line)
                        if m:
                            cur = int(m.group(1))
                    elif "(default):" in line:
                        m = re.search(r'\(default\):\s*(\d+)', line)
                        if m:
                            cur = int(m.group(1))
                    else:
                        # Fallback pattern
                        m = re.search(r'Current:[^0-9]*(\d+)', line)
                        if m:
                            cur = int(m.group(1))
        
        # If we still don't have max value, try alternative method
        if maxv is None:
            try:
                # Try to get max volume from system settings
                max_out = await self._run("shell", "settings", "get", "system", "volume_music_max", timeout=5.0)
                if max_out.strip().isdigit():
                    maxv = int(max_out.strip())
            except Exception:
                pass
        
        # If still no max value, use a reasonable default based on Android standards
        if maxv is None:
            maxv = 15  # Most Android devices use 15 as max volume steps
        
        return {"current": cur, "max": maxv}

    async def audio_full_info(self) -> dict:
        """Get comprehensive audio information including all volume streams and ringer mode."""
        try:
            # Use dumpsys with timeout flag for better reliability
            out = await self._run("shell", "dumpsys", "-t", "5", "audio", timeout=10.0)
        except Exception:
            # Fallback without timeout flag
            out = await self._run("shell", "dumpsys", "audio", timeout=10.0)
        
        result = {
            "music": {"current": None, "max": None, "percent": None},
            "ring": {"current": None, "max": None, "percent": None},
            "alarm": {"current": None, "max": None, "percent": None},
            "ringer_mode": "UNKNOWN"
        }
        
        lines = out.splitlines()
        current_stream = None
        
        # Parse each stream section
        for line in lines:
            line = line.strip()
            
            # Detect stream sections
            if "- STREAM_MUSIC:" in line:
                current_stream = "music"
                continue
            elif "- STREAM_RING:" in line:
                current_stream = "ring"
                continue
            elif "- STREAM_ALARM:" in line:
                current_stream = "alarm"
                continue
            elif line.startswith("- STREAM_") and current_stream:
                current_stream = None
                continue
            
            # Parse ringer mode
            if "Ringer mode:" in line:
                # Look for next lines with mode info
                continue
            if current_stream is None and "- mode (internal) =" in line:
                try:
                    mode = line.split("=")[1].strip()
                    result["ringer_mode"] = mode
                except (ValueError, IndexError):
                    pass
            
            # Parse stream data
            if current_stream and current_stream in result:
                stream_data = result[current_stream]
                
                # Look for Max value
                if "Max:" in line:
                    try:
                        stream_data["max"] = int(line.split("Max:")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                # Look for current volume (streamVolume preferred)
                if "streamVolume:" in line:
                    try:
                        stream_data["current"] = int(line.split("streamVolume:")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "Current:" in line:
                    # Try to extract speaker or default volume
                    if "(speaker):" in line:
                        m = re.search(r'\(speaker\):\s*(\d+)', line)
                        if m:
                            stream_data["current"] = int(m.group(1))
                    elif "(default):" in line:
                        m = re.search(r'\(default\):\s*(\d+)', line)
                        if m:
                            stream_data["current"] = int(m.group(1))
                    else:
                        # Fallback pattern
                        m = re.search(r'Current:[^0-9]*(\d+)', line)
                        if m:
                            stream_data["current"] = int(m.group(1))
        
        # Calculate percentages with improved logic
        for stream_name, stream_data in result.items():
            if stream_name != "ringer_mode" and stream_data["max"] and stream_data["current"] is not None:
                # Ensure we have valid values
                current = stream_data["current"]
                max_val = stream_data["max"]
                
                if max_val > 0:
                    # Calculate percentage with proper bounds checking
                    percent = round(current / max_val * 100, 1)
                    # Ensure percentage is within 0-100 range
                    stream_data["percent"] = max(0, min(100, percent))
                else:
                    stream_data["percent"] = 0
        
        return result

    async def set_volume_percent(self, percent: int) -> None:
        """Set STREAM_MUSIC volume by percent with media_session-first logic.

        Strategy (aligned with tests/adb_volume_pct.py):
        1) Query max/current via dumpsys audio.
        2) Convert percent (clamped 0..100) to index using round(pct*max/100).
        3) Primary: cmd media_session volume --show --stream 3 --set <index>.
           Fallback: media volume --stream 3 --set <index>.
           Last resort: settings put system volume_music <index>.
        4) Verify; if not exact, nudge using keyevents up/down to reach target.
        """

        # Clamp percent to [0, 100]
        try:
            pct = max(0, min(100, int(round(float(percent)))))
        except Exception:
            raise ValueError(f"Invalid percent value: {percent!r}")

        info = await self.audio_music_info()
        cur = info.get("current")
        maxv = info.get("max")

        if not maxv or maxv <= 0:
            # Without max value, approximate with a few keyevents in desired direction
            steps = 5
            direction = "up" if pct >= 50 else "down"
            logger.info("No max volume detected; approximating %d steps %s", steps, direction)
            for _ in range(steps):
                await self.volume(direction)
            return

        target = max(0, min(maxv, round(pct * maxv / 100)))

        # Try media_session first, then media volume, then settings
        try:
            await self._run(
                "shell", "cmd", "media_session", "volume", "--show", "--stream", "3", "--set", str(target)
            )
            logger.debug("Volume set via media_session")
        except Exception as e1:
            logger.debug("media_session volume failed: %s", e1)
            try:
                await self._run("shell", "media", "volume", "--stream", "3", "--set", str(target))
                logger.debug("Volume set via media volume")
            except Exception as e2:
                logger.debug("media volume failed: %s", e2)
                try:
                    await self._run("shell", "settings", "put", "system", "volume_music", str(target))
                    logger.debug("Volume set via settings put")
                except Exception as e3:
                    logger.debug("settings put failed: %s", e3)
                    # Fall back to keyevents if all direct methods failed
                    if cur is None:
                        steps = 5
                        direction = "up" if pct >= 50 else "down"
                        logger.info("Fallback to keyevents: %d steps %s", steps, direction)
                        for _ in range(steps):
                            await self.volume(direction)
                        return

        # Verify and nudge if needed
        info2 = await self.audio_music_info()
        cur2 = info2.get("current")
        if isinstance(cur2, int) and cur2 != target:
            delta = target - cur2
            cmd = "up" if delta > 0 else "down"
            logger.info("Nudging volume via keyevents (%d steps %s)", abs(delta), cmd)
            for _ in range(abs(delta)):
                await self.volume(cmd)
    
    async def set_volume_index(self, index: int) -> None:
        """Set STREAM_MUSIC volume by absolute index using media_session-first logic."""
        info = await self.audio_music_info()
        maxv = info.get("max")
        cur = info.get("current")

        try:
            idx = int(round(float(index)))
        except Exception:
            raise ValueError(f"Invalid volume index: {index!r}")

        if maxv is not None and maxv >= 0:
            idx = max(0, min(maxv, idx))

        # Primary: media_session; Fallbacks: media, settings
        try:
            await self._run(
                "shell", "cmd", "media_session", "volume", "--show", "--stream", "3", "--set", str(idx)
            )
            logger.debug("Volume set via media_session")
        except Exception as e1:
            logger.debug("media_session volume failed: %s", e1)
            try:
                await self._run("shell", "media", "volume", "--stream", "3", "--set", str(idx))
                logger.debug("Volume set via media volume")
            except Exception as e2:
                logger.debug("media volume failed: %s", e2)
                try:
                    await self._run("shell", "settings", "put", "system", "volume_music", str(idx))
                    logger.debug("Volume set via settings put")
                except Exception as e3:
                    logger.debug("settings put failed: %s", e3)
                    # If everything failed, try approximate via keyevents
                    if cur is not None:
                        delta = idx - int(cur)
                        cmd = "up" if delta > 0 else "down"
                        logger.info("Fallback to keyevents (%d steps %s)", abs(delta), cmd)
                        for _ in range(abs(delta)):
                            await self.volume(cmd)
                        return
                    else:
                        logger.warning("Cannot set volume: no current level available for fallback")
                        return

        # Verify and nudge if necessary
        info2 = await self.audio_music_info()
        cur2 = info2.get("current")
        if isinstance(cur2, int) and cur2 != idx:
            delta = idx - cur2
            cmd = "up" if delta > 0 else "down"
            logger.info("Nudging volume via keyevents (%d steps %s)", abs(delta), cmd)
            for _ in range(abs(delta)):
                await self.volume(cmd)

    async def set_brightness(self, value: int) -> None:
        v = max(0, min(255, int(value)))
        await self._run("shell", "settings", "put", "system", "screen_brightness", str(v))

    async def screen(self, action: str) -> None:
        # Toggle with power key; we try to enforce state via dumpsys if necessary later
        if action.lower() in ("toggle", "power"):
            await self.keyevent(26)
            return
        # For on/off, attempt to check and toggle if needed
        is_on = await self.screen_state()
        if action.lower() == "on" and not is_on:
            await self.keyevent(26)
        elif action.lower() == "off" and is_on:
            await self.keyevent(26)

    async def screen_state(self) -> bool:
        """Return screen on/off state.

        Order chosen to satisfy existing tests: use `dumpsys power` first,
        then fall back to `dumpsys display` parsing (mScreenState) if needed.
        """
        # Primary: dumpsys power (expected by tests)
        try:
            state = await self._run("shell", "dumpsys", "power", timeout=8.0)
            if ("Display Power: state=ON" in state) or ("mHoldingDisplaySuspendBlocker=true" in state):
                return True
            if ("Display Power: state=OFF" in state):
                return False
        except Exception as e:
            logger.debug("Failed to get screen state via dumpsys power: %s", e)

        # Fallback: dumpsys display using mScreenState
        try:
            state = await self._run("shell", "dumpsys", "display", timeout=8.0)
            if "mScreenState=" in state:
                for line in state.splitlines():
                    if "mScreenState=" in line:
                        return "mScreenState=ON" in line
                return "mScreenState=ON" in state
        except Exception as e:
            logger.warning("Failed to get screen state via display dumpsys: %s", e)
        return False

    async def get_brightness(self) -> int:
        out = await self._run("shell", "settings", "get", "system", "screen_brightness")
        try:
            return int(out.strip())
        except Exception:
            logger.exception("Failed to parse brightness value")
            return 0

    async def launch_app(self, package: str) -> None:
        await self._run("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")

    async def stop_app(self, package: str) -> None:
        await self._run("shell", "am", "force-stop", package)

    async def switch_app(self, package: str) -> None:
        await self.launch_app(package)

    async def top_app(self) -> dict:
        # Try dumpsys activity activities for top activity
        out = await self._run("shell", "dumpsys", "activity", "activities")
        pkg = None
        act = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("mResumedActivity:") or "topResumedActivity" in line:
                # e.g., mResumedActivity: ActivityRecord{... u0 com.spotify.music/.MainActivity}
                parts = line.split()
                for token in parts:
                    if "/" in token and "." in token:
                        comp = token.strip()
                        if comp.endswith("}"):
                            comp = comp[:-1]
                        pkg, act = comp.split("/", 1)
                        break
                break
        return {"package": pkg, "activity": act}

    async def list_packages(self, pattern: Optional[str] = None) -> list[str]:
        args = ["shell", "pm", "list", "packages"]
        if pattern:
            args.append(pattern)
        out = await self._run(*args)
        pkgs = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkgs.append(line.split(":", 1)[1])
        return pkgs

    @asynccontextmanager
    async def _temp_remote_file(self, suffix: str = ".tmp"):
        """Context manager for temporary remote files."""
        remote_path = f"/sdcard/__isg_{os.getpid()}_{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}{suffix}"
        try:
            yield remote_path
        finally:
            try:
                await self._run("shell", "rm", "-f", remote_path, timeout=5.0)
            except Exception:
                logger.debug("Failed to cleanup remote file: %s", remote_path)
    
    async def screenshot(self, path: str) -> None:
        """Capture a screenshot to host path with optimized fallback strategy."""
        # Try exec-out first (fastest method)
        if await self._try_exec_out_screenshot(path):
            return
        
        # Fallback to traditional method
        async with self._temp_remote_file(".png") as remote_path:
            try:
                await self._run("shell", "screencap", "-p", remote_path, timeout=10.0)
                await self._run("pull", remote_path, path, timeout=15.0)
                logger.debug("Screenshot saved via fallback method: %s", path)
            except Exception as e:
                logger.error("Screenshot failed: %s", e)
                raise ADBError(f"Screenshot capture failed: {e}") from e
    
    async def _try_exec_out_screenshot(self, path: str) -> bool:
        """Try to capture screenshot using exec-out method."""
        try:
            cmd = ["adb", *self._target(), "exec-out", "screencap", "-p"]
            proc = await asyncio.create_subprocess_exec(
                *cmd, 
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE,
                limit=10 * 1024 * 1024  # 10MB limit for screenshots
            )
            
            try:
                with open(path, "wb") as f:
                    chunk_size = 64 * 1024  # 64KB chunks
                    while True:
                        chunk = await asyncio.wait_for(
                            proc.stdout.read(chunk_size), timeout=3.0
                        )
                        if not chunk:
                            break
                        f.write(chunk)
                
                await asyncio.wait_for(proc.wait(), timeout=5.0)
                if proc.returncode == 0:
                    logger.debug("Screenshot saved via exec-out: %s", path)
                    return True
                    
            except asyncio.TimeoutError:
                logger.warning("Exec-out screenshot timed out")
            except Exception as e:
                logger.debug("Exec-out screenshot failed: %s", e)
            finally:
                if proc.returncode is None:
                    proc.kill()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        logger.warning("Failed to kill exec-out process")
                        
        except Exception as e:
            logger.debug("Failed to start exec-out screenshot: %s", e)
        
        return False

    async def screenshot_bytes(self) -> bytes:
        """Capture screenshot and return as bytes with optimized handling."""
        # Try exec-out first (most efficient)
        try:
            data = await self._exec_out_screenshot_bytes()
            if data:
                return data
        except Exception as e:
            logger.debug("Exec-out screenshot_bytes failed: %s", e)
        
        # Fallback to file-based method
        async with self._temp_remote_file(".png") as remote_path:
            try:
                await self._run("shell", "screencap", "-p", remote_path, timeout=10.0)
                
                # Use temporary file for pulling
                with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
                    await self._run("pull", remote_path, tmp_file.name, timeout=15.0)
                    tmp_file.seek(0)
                    data = tmp_file.read()
                    
                if not data:
                    raise ADBError("Screenshot data is empty")
                    
                logger.debug("Screenshot captured via fallback (%d bytes)", len(data))
                return data
                
            except Exception as e:
                logger.error("Screenshot bytes capture failed: %s", e)
                raise ADBError(f"Screenshot capture failed: {e}") from e
    
    async def _exec_out_screenshot_bytes(self) -> Optional[bytes]:
        """Capture screenshot bytes using exec-out method."""
        cmd = ["adb", *self._target(), "exec-out", "screencap", "-p"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=10 * 1024 * 1024  # 10MB limit
        )
        
        data = bytearray()
        try:
            chunk_size = 64 * 1024  # 64KB chunks
            while True:
                chunk = await asyncio.wait_for(
                    proc.stdout.read(chunk_size), timeout=3.0
                )
                if not chunk:
                    break
                data.extend(chunk)
            
            await asyncio.wait_for(proc.wait(), timeout=5.0)
            if proc.returncode == 0 and data:
                logger.debug("Screenshot captured via exec-out (%d bytes)", len(data))
                return bytes(data)
                
        except asyncio.TimeoutError:
            logger.warning("Exec-out screenshot bytes timed out")
        except Exception as e:
            logger.debug("Exec-out screenshot bytes error: %s", e)
        finally:
            if proc.returncode is None:
                proc.kill()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
        
        return None

    async def metrics(self) -> Dict[str, Any]:
        """Collect comprehensive device metrics with optimized parallel execution."""
        # Collect basic metrics in parallel using lighter commands
        tasks = {
            'mem': self._get_memory_info_proc(),
            'net': self._run("shell", "dumpsys", "-t", "10", "connectivity", timeout=15.0),
            'screen': self._get_screen_info(),
            'audio': self._get_audio_info(),
            'storage': self._get_storage_info(),
            'foreground_app': self._get_foreground_app(),
            'cpu_usage': self._get_cpu_usage(),
            # Also capture full cpuinfo so we can provide user/kernel breakdown for HA
            'cpuinfo': self._run("shell", "dumpsys", "-t", "5", "cpuinfo", timeout=8.0)
        }
        
        # Add optional metrics based on device capabilities
        if self.has_battery:
            tasks['battery'] = self._run("shell", "dumpsys", "-t", "5", "battery", timeout=10.0)
        
        if self.has_cellular:
            tasks['tele'] = self._run("shell", "dumpsys", "-t", "5", "telephony.registry", timeout=10.0)
        
        # Add additional info gathering with timeout flags
        tasks.update({
            'wifi': self._run("shell", "dumpsys", "-t", "5", "wifi", timeout=10.0)
        })
        
        # Execute all tasks concurrently with error handling
        results = await self._gather_with_fallback(tasks)
        
        # Process results
        return self._process_metrics_results(results)
    
    async def _gather_with_fallback(self, tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks concurrently with individual error handling."""
        results = {}
        
        # Convert tasks to coroutines and gather
        async def safe_task(name: str, coro):
            try:
                if asyncio.iscoroutine(coro):
                    return name, await coro
                else:
                    return name, await coro
            except Exception as e:
                logger.warning("Failed to collect %s metrics: %s", name, e)
                return name, None
        
        # Execute all tasks concurrently
        task_results = await asyncio.gather(
            *[safe_task(name, task) for name, task in tasks.items()],
            return_exceptions=False
        )
        
        # Convert to dictionary
        for name, result in task_results:
            results[name] = result
        
        return results
    
    async def _get_screen_info(self) -> Optional[Dict[str, Any]]:
        """Get screen state and brightness info."""
        try:
            screen_on = await self.screen_state()
            brightness = await self.get_brightness()
            return {
                'on': screen_on,
                'brightness': brightness
            }
        except Exception as e:
            logger.warning("Failed to get screen info: %s", e)
            return None
    
    async def _get_audio_info(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive audio volume information."""
        try:
            # Use the new comprehensive audio info method
            full_audio = await self.audio_full_info()
            
            # Format for compatibility with existing structure
            audio = {
                'music': {
                    'index': full_audio['music'].get('current'),
                    'max': full_audio['music'].get('max'),
                    'percent': full_audio['music'].get('percent')
                },
                'ring': {
                    'index': full_audio['ring'].get('current'),
                    'max': full_audio['ring'].get('max'),
                    'percent': full_audio['ring'].get('percent')
                },
                'alarm': {
                    'index': full_audio['alarm'].get('current'),
                    'max': full_audio['alarm'].get('max'),
                    'percent': full_audio['alarm'].get('percent')
                },
                'ringer_mode': full_audio.get('ringer_mode', 'UNKNOWN')
            }
            return audio
        except Exception as e:
            logger.warning("Failed to get audio info: %s", e)
            return {'music': {}, 'ring': {}, 'alarm': {}, 'ringer_mode': 'UNKNOWN'}
    
    async def _get_memory_info_proc(self) -> Optional[Dict[str, Any]]:
        """Get memory information from /proc/meminfo with improved parsing."""
        try:
            # Get memory info using multiple methods for better accuracy
            raw_output = await self._run("shell", "cat", "/proc/meminfo", timeout=5.0)
            total_kb = available_kb = free_kb = cached_kb = buffers_kb = None
            
            for line in raw_output.splitlines():
                line = line.strip()
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    available_kb = int(line.split()[1])
                elif line.startswith("MemFree:"):
                    free_kb = int(line.split()[1])
                elif line.startswith("Cached:"):
                    cached_kb = int(line.split()[1])
                elif line.startswith("Buffers:"):
                    buffers_kb = int(line.split()[1])
            
            # Calculate memory usage
            if total_kb and total_kb > 0:
                if available_kb is not None:
                    # Use MemAvailable if available (more accurate)
                    used_kb = total_kb - available_kb
                    used_percent = (used_kb / total_kb) * 100
                elif free_kb is not None:
                    # Fallback to MemFree + Cached + Buffers
                    used_kb = total_kb - free_kb
                    if cached_kb is not None:
                        used_kb -= cached_kb
                    if buffers_kb is not None:
                        used_kb -= buffers_kb
                    used_percent = (used_kb / total_kb) * 100
                else:
                    used_kb = 0
                    used_percent = 0
                
                return {
                    'total_kb': total_kb,
                    'available_kb': available_kb,
                    'used_kb': used_kb,
                    'used_percent': round(used_percent, 1),
                    'raw_info': f"Total: {total_kb}KB, Available: {available_kb}KB, Used: {used_kb}KB ({used_percent:.1f}%)"
                }
        except Exception as e:
            logger.debug("Failed to get memory info from /proc/meminfo: %s", e)
        
        return None
    
    async def _get_foreground_app(self) -> Optional[str]:
        """Get foreground app package name efficiently."""
        try:
            output = await self._run("shell", "dumpsys", "activity", "activities", timeout=10.0)
            for line in output.splitlines():
                if "mResumedActivity:" in line or "topResumedActivity" in line:
                    # Extract package name from patterns like: mResumedActivity: ActivityRecord{... u0 com.spotify.music/.MainActivity}
                    parts = line.split()
                    for token in parts:
                        if "/" in token and "." in token:
                            comp = token.strip()
                            if comp.endswith("}"):
                                comp = comp[:-1]
                            if "/" in comp:
                                pkg = comp.split("/", 1)[0]
                                return pkg
                    break
        except Exception as e:
            logger.debug("Failed to get foreground app: %s", e)
        
        return None
    
    async def _get_cpu_usage(self) -> Optional[str]:
        """Get CPU usage percentage using top command for better accuracy."""
        try:
            # Use top command to get real-time CPU usage
            output = await self._run("shell", "top", "-n", "1", "-d", "1", timeout=5.0)
            
            # Parse top output for CPU usage
            lines = output.splitlines()
            for line in lines:
                line = line.strip()
                # Look for CPU usage line (usually contains "CPU:")
                if "CPU:" in line or "cpu" in line.lower():
                    # Extract percentage from line like "CPU: 15% usr 5% sys 0% nic 80% idle"
                    import re
                    cpu_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if cpu_match:
                        cpu_percent = float(cpu_match.group(1))
                        # Calculate total CPU usage (100 - idle)
                        if "idle" in line.lower():
                            idle_match = re.search(r'(\d+(?:\.\d+)?)%\s*idle', line)
                            if idle_match:
                                idle_percent = float(idle_match.group(1))
                                cpu_percent = 100 - idle_percent
                        return f"{cpu_percent:.1f}%"
                    break
            
            # Fallback to dumpsys cpuinfo if top doesn't work
            output = await self._run("shell", "dumpsys", "-t", "5", "cpuinfo", timeout=8.0)
            for line in output.splitlines():
                if "TOTAL:" in line or line.strip().lower().startswith("total:"):
                    parts = line.split(":", 1)[-1]
                    for token in parts.split():
                        if "%" in token and any(c.isdigit() for c in token):
                            return token.split("%")[0] + "%"
                    break
        except Exception as e:
            logger.debug("Failed to get CPU usage: %s", e)
        
        return None
    
    async def _get_storage_info(self) -> Dict[str, Any]:
        """Get storage information for data and sdcard partitions."""
        storage = {}
        
        # Get storage info for both partitions concurrently
        tasks = {
            'data': self._get_partition_storage('/data'),
            'sdcard': self._get_partition_storage('/sdcard')
        }
        
        results = await self._gather_with_fallback(tasks)
        
        for partition, info in results.items():
            if info:
                storage[partition] = info
        
        return storage
    
    async def _get_partition_storage(self, path: str) -> Optional[Dict[str, Any]]:
        """Get storage info for a specific partition."""
        try:
            df_output = await self._run("shell", "df", "-k", path, timeout=5.0)
            for line in df_output.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    total_kb = int(parts[1])
                    used_kb = int(parts[2])
                    avail_kb = int(parts[3])
                    usep = parts[4]
                    try:
                        used_pct = float(usep.strip().strip('%'))
                    except ValueError:
                        used_pct = round(used_kb * 100 / total_kb, 1) if total_kb else 0
                    
                    return {
                        'total_kb': total_kb,
                        'used_kb': used_kb,
                        'avail_kb': avail_kb,
                        'used_percent': used_pct
                    }
        except Exception as e:
            logger.debug("Failed to get storage info for %s: %s", path, e)
        
        return None
    
    def _process_metrics_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process collected metrics into final format."""
        out = {
            'battery': {},
            'memory_summary': {},
            'network': {},
            'screen': results.get('screen', {}),
            'audio': results.get('audio', {'music': {}}),
            'storage': results.get('storage', {})
        }
        
        # Add new efficient metrics
        if results.get('foreground_app'):
            out['foreground_app'] = results['foreground_app']
        
        if results.get('cpu_usage'):
            out['cpu'] = {'usage': results['cpu_usage']}
        
        # Process battery info
        battery_raw = results.get('battery', '')
        if battery_raw:
            self._process_battery_info(out['battery'], battery_raw)
        
        # Process memory info - now from /proc/meminfo
        mem_data = results.get('mem')
        if mem_data and isinstance(mem_data, dict):
            # New format from /proc/meminfo
            out['memory_summary'] = {
                'total_ram': f"{mem_data.get('total_kb', 0)}KB",
                'available_ram': f"{mem_data.get('available_kb', 0)}KB", 
                'used_ram': f"{mem_data.get('used_kb', 0)}KB",
                'used_percent': mem_data.get('used_percent', 0.0)
            }
        elif mem_data and isinstance(mem_data, str):
            # Fallback to old dumpsys format if needed
            self._process_memory_info(out['memory_summary'], mem_data)
        
        # Process network info
        net_raw = results.get('net', '')
        wifi_raw = results.get('wifi', '')
        tele_raw = results.get('tele', '')
        if net_raw or wifi_raw or tele_raw:
            self._process_network_info(out['network'], net_raw, wifi_raw, tele_raw)
        
        # Process CPU info
        cpu_raw = results.get('cpuinfo', '')
        if cpu_raw:
            cpu_info = self._process_cpu_info(cpu_raw)
            if cpu_info:
                out['cpu'] = cpu_info
        
        return out
    
    def _process_battery_info(self, battery_dict: Dict[str, Any], battery_raw: str) -> None:
        """Process battery information from dumpsys output."""
        temp_raw = None
        health_raw = None
        
        for line in battery_raw.splitlines():
            if ':' in line:
                k, v = [x.strip() for x in line.split(':', 1)]
                battery_dict[k.replace(' ', '_').lower()] = v
                
                if k.strip().lower() == 'temperature':
                    try:
                        temp_raw = int(v)
                    except ValueError:
                        pass
                elif k.strip().lower() == 'health':
                    health_raw = v
        
        # Normalize temperature
        if temp_raw is not None:
            battery_dict['temperature_c'] = round(temp_raw / 10.0, 1)
        
        # Normalize health
        health_map = {
            '1': 'unknown', '2': 'good', '3': 'overheat',
            '4': 'dead', '5': 'over_voltage', '6': 'failure', '7': 'cold'
        }
        if health_raw is not None:
            battery_dict['health_name'] = health_map.get(
                str(health_raw).strip(), str(health_raw).strip()
            )
    
    def _process_memory_info(self, memory_dict: Dict[str, Any], mem_raw: str) -> None:
        """Process memory information from dumpsys output."""
        total_k = free_k = used_k = None
        
        for line in mem_raw.splitlines():
            s = line.strip()
            if any(s.startswith(prefix) for prefix in ['Total RAM:', 'Free RAM:', 'Used RAM:']):
                k, v = [x.strip() for x in line.split(':', 1)]
                memory_dict[k.replace(' ', '_').lower()] = v
                
                # Extract numeric value
                num = ''.join(ch for ch in v if ch.isdigit())
                try:
                    val = int(num)
                    if k.startswith('Total'):
                        total_k = val
                    elif k.startswith('Free'):
                        free_k = val
                    elif k.startswith('Used'):
                        used_k = val
                except ValueError:
                    pass
        
        # Calculate used percentage
        if total_k and used_k is not None:
            try:
                memory_dict['used_percent'] = round(used_k / total_k * 100, 1)
            except (ZeroDivisionError, TypeError):
                pass
        elif total_k and free_k is not None:
            try:
                used = max(total_k - free_k, 0)
                memory_dict['used_percent'] = round(used / total_k * 100, 1)
            except (ZeroDivisionError, TypeError):
                pass
    
    def _process_network_info(self, network_dict: Dict[str, Any], 
                            net_raw: str, wifi_raw: str, tele_raw: str) -> None:
        """Process network information from various dumpsys outputs."""
        # Process connectivity info
        active_type = None
        for line in net_raw.splitlines():
            if 'mNetworkCapabilities' in line and 'NET_CAPABILITY_INTERNET' in line:
                network_dict['internet'] = True
            if 'NetworkAgentInfo' in line:
                if 'WIFI' in line:
                    active_type = 'wifi'
                elif 'ETHERNET' in line:
                    active_type = 'ethernet'
                elif any(x in line for x in ['MOBILE', 'CELLULAR']):
                    active_type = 'cellular'
        
        if active_type:
            network_dict['type'] = active_type
        
        # Process WiFi info
        if wifi_raw:
            wifi_info = {}
            for line in wifi_raw.splitlines():
                ls = line.strip()
                if ls.startswith('SSID:') and '<unknown ssid>' not in ls:
                    wifi_info['ssid'] = ls.split(':', 1)[1].strip()
                elif 'RSSI:' in ls:
                    try:
                        rssi = int(ls.split('RSSI:', 1)[1].split()[0])
                        wifi_info['rssi_dbm'] = rssi
                    except (ValueError, IndexError):
                        pass
                elif 'Link speed:' in ls:
                    try:
                        sp = ls.split(':', 1)[1].strip()
                        mbps = int(''.join(ch for ch in sp if ch.isdigit()))
                        wifi_info['link_mbps'] = mbps
                    except (ValueError, IndexError):
                        pass
            
            if wifi_info:
                network_dict['wifi'] = wifi_info
        
        # Process cellular info
        if tele_raw:
            cellular_info = {}
            for line in tele_raw.splitlines():
                ls = line.strip()
                if 'mSignalStrength=' in ls:
                    if 'level=' in ls:
                        try:
                            lvl = int(ls.split('level=', 1)[1].split(',', 1)[0].strip())
                            cellular_info['level'] = lvl
                        except (ValueError, IndexError):
                            pass
                    if 'dbm=' in ls:
                        try:
                            dbm = int(ls.split('dbm=', 1)[1].split(',', 1)[0].strip())
                            cellular_info['dbm'] = dbm
                        except (ValueError, IndexError):
                            pass
                    break
            
            if cellular_info:
                network_dict['cellular'] = cellular_info
    
    def _process_cpu_info(self, cpu_raw: str) -> Optional[Dict[str, float]]:
        """Process CPU information from dumpsys output."""
        for line in cpu_raw.splitlines():
            if 'TOTAL:' in line or line.strip().lower().startswith('total:'):
                parts = line.split(':', 1)[-1]
                fields = {}
                for token in parts.split('+'):
                    token = token.strip()
                    if '%' in token:
                        try:
                            value = float(token.split('%', 1)[0].strip())
                            name = token.split('%', 1)[1].strip()
                            fields[name] = value
                        except (ValueError, IndexError):
                            continue
                if fields:
                    return fields
                break
        
        return None
