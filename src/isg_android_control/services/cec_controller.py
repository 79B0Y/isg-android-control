from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import os

logger = logging.getLogger(__name__)


@dataclass
class CECDevice:
    """Represents a CEC device on the network."""
    address: int
    name: str
    vendor: str
    device_type: str
    power_status: str
    active_source: bool = False


@dataclass
class CECCommand:
    """Represents a CEC command with metadata."""
    name: str
    code: str
    description: str
    target_device: str = "0"  # 0 = TV, F = Broadcast


class CECController:
    """
    Lightweight CEC (Consumer Electronics Control) controller for TV control.

    Optimized for Termux/Ubuntu environments with minimal resource usage.
    Supports multiple CEC backends and provides comprehensive TV control.
    """

    # CEC command mappings for common TV functions
    CEC_COMMANDS = {
        # Power commands
        'power_on': CECCommand('power_on', '04', 'Power on device', '0'),
        'power_off': CECCommand('power_off', '36', 'Power off device', '0'),
        'power_toggle': CECCommand('power_toggle', '6B', 'Toggle power state', '0'),

        # Navigation commands
        'up': CECCommand('up', '44 01', 'Navigate up', '0'),
        'down': CECCommand('down', '44 02', 'Navigate down', '0'),
        'left': CECCommand('left', '44 03', 'Navigate left', '0'),
        'right': CECCommand('right', '44 04', 'Navigate right', '0'),
        'select': CECCommand('select', '44 00', 'Select/OK button', '0'),
        'back': CECCommand('back', '44 0D', 'Back button', '0'),
        'home': CECCommand('home', '44 09', 'Home button', '0'),
        'menu': CECCommand('menu', '44 09', 'Menu button', '0'),

        # Volume commands
        'volume_up': CECCommand('volume_up', '44 41', 'Volume up', '0'),
        'volume_down': CECCommand('volume_down', '44 42', 'Volume down', '0'),
        'mute': CECCommand('mute', '44 43', 'Mute toggle', '0'),

        # Input/Source commands
        'input_hdmi1': CECCommand('input_hdmi1', '82 10 00', 'Switch to HDMI 1', '0'),
        'input_hdmi2': CECCommand('input_hdmi2', '82 20 00', 'Switch to HDMI 2', '0'),
        'input_hdmi3': CECCommand('input_hdmi3', '82 30 00', 'Switch to HDMI 3', '0'),
        'input_hdmi4': CECCommand('input_hdmi4', '82 40 00', 'Switch to HDMI 4', '0'),

        # Utility commands
        'get_power_status': CECCommand('get_power_status', '8F', 'Get power status', '0'),
        'get_active_source': CECCommand('get_active_source', '85', 'Get active source', 'F'),
        'set_active_source': CECCommand('set_active_source', '82 10 00', 'Set as active source', 'F'),
    }

    def __init__(
        self,
        device_path: Optional[str] = None,
        cec_client_path: Optional[str] = None,
        device_name: str = "ISG Android Controller",
        physical_address: str = "1.0.0.0"
    ):
        self.device_path = device_path or self._find_cec_device()
        self.cec_client_path = cec_client_path or self._find_cec_client()
        self.device_name = device_name
        self.physical_address = physical_address

        # State tracking
        self._connected = False
        self._last_command_time: Optional[datetime] = None
        self._device_cache: Dict[int, CECDevice] = {}
        self._command_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

        # Performance optimization
        self._batch_delay = 0.1  # 100ms delay between commands
        self._cache_ttl = 30.0  # 30 seconds cache TTL

        logger.info(
            "CEC Controller initialized (device=%s, client=%s)",
            self.device_path, self.cec_client_path
        )

    def _find_cec_device(self) -> Optional[str]:
        """Find CEC device file in the system."""
        possible_paths = [
            '/dev/cec0',
            '/dev/cec1',
            '/dev/cec/0',
            '/sys/class/cec/cec0',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info("Found CEC device: %s", path)
                return path

        logger.warning("No CEC device found in standard locations")
        return None

    def _find_cec_client(self) -> Optional[str]:
        """Find CEC client executable."""
        possible_clients = ['cec-client', 'cec-ctl', 'echo']  # echo as fallback for testing

        for client in possible_clients:
            try:
                result = subprocess.run(['which', client],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    logger.info("Found CEC client: %s", path)
                    return path
            except Exception:
                continue

        logger.warning("No CEC client found")
        return None

    async def initialize(self) -> bool:
        """Initialize CEC connection and start command worker."""
        if not self.cec_client_path:
            logger.error("No CEC client available")
            return False

        try:
            # Test CEC connectivity
            if await self._test_cec_connection():
                self._connected = True

                # Start command worker for sequential processing
                self._worker_task = asyncio.create_task(self._command_worker())

                logger.info("CEC Controller initialized successfully")
                return True
            else:
                logger.error("CEC connection test failed")
                return False

        except Exception as e:
            logger.error("Error initializing CEC controller: %s", e)
            return False

    async def cleanup(self) -> None:
        """Clean up CEC resources."""
        self._connected = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        logger.info("CEC Controller cleaned up")

    async def _test_cec_connection(self) -> bool:
        """Test if CEC is working by scanning for devices."""
        try:
            if 'cec-client' in (self.cec_client_path or ''):
                # Test with cec-client
                cmd = [self.cec_client_path, '-s', '-d', '1']
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Send scan command and wait briefly
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=b'scan\nq\n'), timeout=5.0
                )

                return proc.returncode == 0 and b'device' in stdout.lower()

            elif 'cec-ctl' in (self.cec_client_path or ''):
                # Test with cec-ctl
                cmd = [self.cec_client_path, '--list-devices']
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                return proc.returncode == 0

            else:
                # For testing environments without actual CEC
                logger.warning("Using mock CEC client for testing")
                return True

        except Exception as e:
            logger.error("CEC connection test failed: %s", e)
            return False

    async def _command_worker(self) -> None:
        """Worker task to process CEC commands sequentially."""
        try:
            while self._connected:
                try:
                    # Get next command from queue
                    command_data = await asyncio.wait_for(
                        self._command_queue.get(), timeout=1.0
                    )

                    # Execute command
                    await self._execute_raw_command(command_data)

                    # Rate limiting
                    await asyncio.sleep(self._batch_delay)

                except asyncio.TimeoutError:
                    continue  # Keep worker alive
                except Exception as e:
                    logger.error("Error in CEC command worker: %s", e)

        except asyncio.CancelledError:
            logger.info("CEC command worker cancelled")
        except Exception as e:
            logger.error("CEC command worker failed: %s", e)

    async def _execute_raw_command(self, command_data: Dict[str, Any]) -> bool:
        """Execute a raw CEC command."""
        if not self._connected:
            logger.error("CEC not connected")
            return False

        cmd_str = command_data.get('command')
        target = command_data.get('target', '0')

        try:
            if 'cec-client' in (self.cec_client_path or ''):
                return await self._execute_cec_client_command(cmd_str, target)
            elif 'cec-ctl' in (self.cec_client_path or ''):
                return await self._execute_cec_ctl_command(cmd_str, target)
            else:
                # Mock execution for testing
                logger.info("Mock CEC command: %s -> %s", target, cmd_str)
                return True

        except Exception as e:
            logger.error("Error executing CEC command %s: %s", cmd_str, e)
            return False

    async def _execute_cec_client_command(self, cmd_str: str, target: str) -> bool:
        """Execute command using cec-client."""
        try:
            # Format command for cec-client
            full_cmd = f"tx {target}:{cmd_str}"

            proc = await asyncio.create_subprocess_exec(
                self.cec_client_path, '-s', '-d', '1',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send command and quit
            input_data = f"{full_cmd}\nq\n".encode()
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data), timeout=3.0
            )

            success = proc.returncode == 0
            if not success:
                logger.warning("CEC command failed: %s", stderr.decode())

            return success

        except Exception as e:
            logger.error("Error with cec-client command: %s", e)
            return False

    async def _execute_cec_ctl_command(self, cmd_str: str, target: str) -> bool:
        """Execute command using cec-ctl."""
        try:
            # Format command for cec-ctl
            cmd = [
                self.cec_client_path,
                f'--to={target}',
                f'--custom-command={cmd_str}'
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)

            success = proc.returncode == 0
            if not success:
                logger.warning("CEC command failed: %s", stderr.decode())

            return success

        except Exception as e:
            logger.error("Error with cec-ctl command: %s", e)
            return False

    async def send_command(self, command_name: str) -> bool:
        """Send a named CEC command to the TV."""
        if command_name not in self.CEC_COMMANDS:
            logger.error("Unknown CEC command: %s", command_name)
            return False

        cmd_info = self.CEC_COMMANDS[command_name]

        command_data = {
            'command': cmd_info.code,
            'target': cmd_info.target_device,
            'name': command_name,
            'description': cmd_info.description
        }

        # Add to queue for sequential processing
        await self._command_queue.put(command_data)
        self._last_command_time = datetime.now()

        logger.info("Queued CEC command: %s (%s)", command_name, cmd_info.description)
        return True

    async def send_custom_command(self, command_code: str, target: str = "0") -> bool:
        """Send a custom CEC command."""
        command_data = {
            'command': command_code,
            'target': target,
            'name': 'custom',
            'description': f'Custom command: {command_code}'
        }

        await self._command_queue.put(command_data)
        self._last_command_time = datetime.now()

        logger.info("Queued custom CEC command: %s -> %s", target, command_code)
        return True

    async def scan_devices(self) -> List[CECDevice]:
        """Scan for CEC devices on the network."""
        if not self._connected:
            return []

        # Check cache first
        if self._device_cache and self._is_cache_valid():
            return list(self._device_cache.values())

        devices = []
        try:
            if 'cec-client' in (self.cec_client_path or ''):
                devices = await self._scan_devices_cec_client()
            elif 'cec-ctl' in (self.cec_client_path or ''):
                devices = await self._scan_devices_cec_ctl()
            else:
                # Mock devices for testing
                devices = [
                    CECDevice(0, "TV", "Samsung", "TV", "on", True),
                    CECDevice(1, "ISG Android Controller", "ISG", "Android", "on", False)
                ]

            # Update cache
            self._device_cache = {dev.address: dev for dev in devices}

        except Exception as e:
            logger.error("Error scanning CEC devices: %s", e)

        return devices

    async def _scan_devices_cec_client(self) -> List[CECDevice]:
        """Scan devices using cec-client."""
        devices = []
        try:
            proc = await asyncio.create_subprocess_exec(
                self.cec_client_path, '-s', '-d', '1',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=b'scan\nq\n'), timeout=10.0
            )

            # Parse scan output
            output = stdout.decode()
            for line in output.split('\n'):
                if 'device #' in line.lower():
                    # Parse device info from cec-client output
                    device = self._parse_cec_client_device(line)
                    if device:
                        devices.append(device)

        except Exception as e:
            logger.error("Error scanning with cec-client: %s", e)

        return devices

    async def _scan_devices_cec_ctl(self) -> List[CECDevice]:
        """Scan devices using cec-ctl."""
        devices = []
        try:
            proc = await asyncio.create_subprocess_exec(
                self.cec_client_path, '--list-devices',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

            # Parse cec-ctl output
            output = stdout.decode()
            for line in output.split('\n'):
                device = self._parse_cec_ctl_device(line)
                if device:
                    devices.append(device)

        except Exception as e:
            logger.error("Error scanning with cec-ctl: %s", e)

        return devices

    def _parse_cec_client_device(self, line: str) -> Optional[CECDevice]:
        """Parse device info from cec-client output."""
        try:
            # Example: "device #0: TV"
            match = re.search(r'device #(\d+):\s*(.+)', line, re.IGNORECASE)
            if match:
                address = int(match.group(1))
                name = match.group(2).strip()
                return CECDevice(
                    address=address,
                    name=name,
                    vendor="Unknown",
                    device_type="TV" if address == 0 else "Unknown",
                    power_status="unknown"
                )
        except Exception as e:
            logger.debug("Error parsing cec-client device line '%s': %s", line, e)

        return None

    def _parse_cec_ctl_device(self, line: str) -> Optional[CECDevice]:
        """Parse device info from cec-ctl output."""
        try:
            # Parse cec-ctl device format
            if 'Device' in line and 'at' in line:
                parts = line.split()
                address = int(parts[1])  # Assuming format "Device X at ..."
                name = " ".join(parts[3:])  # Rest is device name
                return CECDevice(
                    address=address,
                    name=name,
                    vendor="Unknown",
                    device_type="TV" if address == 0 else "Unknown",
                    power_status="unknown"
                )
        except Exception as e:
            logger.debug("Error parsing cec-ctl device line '%s': %s", line, e)

        return None

    def _is_cache_valid(self) -> bool:
        """Check if device cache is still valid."""
        if not self._last_command_time:
            return False
        return datetime.now() - self._last_command_time < timedelta(seconds=self._cache_ttl)

    async def get_tv_status(self) -> Dict[str, Any]:
        """Get comprehensive TV status."""
        devices = await self.scan_devices()
        tv_device = next((d for d in devices if d.address == 0), None)

        return {
            'connected': self._connected,
            'tv_found': tv_device is not None,
            'tv_name': tv_device.name if tv_device else None,
            'tv_power': tv_device.power_status if tv_device else 'unknown',
            'devices_count': len(devices),
            'last_command': self._last_command_time.isoformat() if self._last_command_time else None,
            'queue_size': self._command_queue.qsize(),
            'available_commands': list(self.CEC_COMMANDS.keys())
        }

    def get_available_commands(self) -> Dict[str, Dict[str, str]]:
        """Get all available CEC commands with descriptions."""
        return {
            name: {
                'code': cmd.code,
                'description': cmd.description,
                'target': cmd.target_device
            }
            for name, cmd in self.CEC_COMMANDS.items()
        }