from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a process from top command."""
    pid: int
    user: str
    cpu_percent: float
    mem_percent: float
    command: str
    service_name: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics from system monitoring."""
    timestamp: datetime
    processes: List[ProcessInfo]
    total_cpu_usage: float
    total_memory_usage: float
    high_cpu_processes: List[ProcessInfo]


class TermuxPerformanceMonitor:
    """
    Direct system performance monitor for Termux environments.

    Monitors CPU and memory usage using native Linux commands instead of ADB,
    providing more accurate and faster performance data.
    """

    def __init__(
        self,
        cpu_threshold: float = 50.0,
        monitoring_interval: float = 0.5,
        kill_after_violations: int = 3,
        enable_auto_kill: bool = True
    ):
        self.cpu_threshold = cpu_threshold
        self.monitoring_interval = monitoring_interval
        self.kill_after_violations = kill_after_violations
        self.enable_auto_kill = enable_auto_kill

        # Track violation counts for processes
        self.violation_counts: Dict[int, int] = {}
        self.violation_timestamps: Dict[int, datetime] = {}

        # Protected processes that should never be killed
        self.protected_processes = {
            'init', 'kernel', 'systemd', 'termux', 'sshd', 'adb',
            'isg-android-control', 'python', 'python3'
        }

        # Detect environment
        self.is_termux = self._detect_termux_environment()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

    def _detect_termux_environment(self) -> bool:
        """Detect if running in Termux environment."""
        try:
            # Check for Termux-specific environment variables
            if os.environ.get('PREFIX') and '/com.termux' in os.environ.get('PREFIX', ''):
                return True
            
            # Check for Android-specific files
            if os.path.exists('/system/build.prop'):
                return True
                
            # Check for Termux-specific paths
            if os.path.exists('/data/data/com.termux'):
                return True
                
            return False
        except Exception:
            return False

    async def get_top_output(self) -> str:
        """Get top command output with optimized parameters for Android/Termux."""
        try:
            # Try different top command variations for different environments
            commands_to_try = [
                # Linux/Termux style
                ['top', '-b', '-n', '1', '-o', '%CPU'],
                # Alternative Linux style
                ['top', '-b', '-n', '1'],
                # Simple top
                ['top', '-n', '1'],
                # Basic top
                ['top']
            ]
            
            for cmd in commands_to_try:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)

                    if proc.returncode == 0:
                        return stdout.decode('utf-8', errors='ignore')
                    else:
                        logger.debug("top command '%s' failed with code %d: %s", ' '.join(cmd), proc.returncode, stderr.decode())
                        continue
                        
                except Exception as e:
                    logger.debug("top command '%s' failed: %s", ' '.join(cmd), e)
                    continue
            
            logger.warning("All top command variations failed")
            return ""

        except Exception as e:
            logger.error("Error running top command: %s", e)
            return ""

    def parse_top_output(self, output: str) -> PerformanceMetrics:
        """Parse top command output to extract process information."""
        lines = output.strip().split('\n')
        processes = []
        total_cpu = 0.0
        total_memory = 0.0

        # Find the header line to understand column positions
        header_idx = -1
        for i, line in enumerate(lines):
            if 'PID' in line and 'CPU' in line:
                header_idx = i
                break

        if header_idx == -1:
            logger.warning("Could not find process header in top output")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                processes=[],
                total_cpu_usage=0.0,
                total_memory_usage=0.0,
                high_cpu_processes=[]
            )

        # Parse process lines
        for line in lines[header_idx + 1:]:
            if not line.strip():
                continue

            process = self._parse_process_line(line)
            if process:
                processes.append(process)
                total_cpu += process.cpu_percent
                total_memory += process.mem_percent

        # Find high CPU processes
        high_cpu_processes = [p for p in processes if p.cpu_percent >= self.cpu_threshold]

        return PerformanceMetrics(
            timestamp=datetime.now(),
            processes=processes,
            total_cpu_usage=min(total_cpu, 100.0),  # Cap at 100%
            total_memory_usage=min(total_memory, 100.0),
            high_cpu_processes=high_cpu_processes
        )

    def _parse_process_line(self, line: str) -> Optional[ProcessInfo]:
        """Parse a single process line from top output."""
        try:
            # Common top output format variations for Android/Termux:
            # PID  USER     PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
            parts = line.split()

            if len(parts) < 11:
                return None

            pid = int(parts[0])
            user = parts[1]
            cpu_str = parts[8]  # %CPU column
            mem_str = parts[9]  # %MEM column
            command = ' '.join(parts[11:])  # COMMAND and args

            # Parse CPU percentage
            cpu_percent = 0.0
            if cpu_str and cpu_str != 'CPU':
                try:
                    cpu_percent = float(cpu_str.rstrip('%'))
                except ValueError:
                    pass

            # Parse memory percentage
            mem_percent = 0.0
            if mem_str and mem_str != 'MEM':
                try:
                    mem_percent = float(mem_str.rstrip('%'))
                except ValueError:
                    pass

            return ProcessInfo(
                pid=pid,
                user=user,
                cpu_percent=cpu_percent,
                mem_percent=mem_percent,
                command=command
            )

        except (ValueError, IndexError) as e:
            logger.debug("Failed to parse process line '%s': %s", line, e)
            return None

    async def get_service_name(self, pid: int) -> Optional[str]:
        """Get service name for a process using systemctl or ps."""
        try:
            # Try to get service name via ps
            proc = await asyncio.create_subprocess_exec(
                'ps', '-p', str(pid), '-o', 'comm=',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)

            if proc.returncode == 0:
                service_name = stdout.decode().strip()
                return service_name if service_name else None

        except Exception as e:
            logger.debug("Failed to get service name for PID %d: %s", pid, e)

        return None

    async def get_app_info(self, pid: int) -> Dict[str, str]:
        """Get detailed application information for a process."""
        app_info = {
            'package_name': 'unknown',
            'app_name': 'unknown',
            'user': 'unknown'
        }
        
        try:
            # Try to get package name from Android process
            proc = await asyncio.create_subprocess_exec(
                'ps', '-p', str(pid), '-o', 'user,comm,args',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)

            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        app_info['user'] = parts[0]
                        app_info['app_name'] = parts[1]
                        
                        # Try to extract package name from command line
                        full_cmd = ' '.join(parts[2:])
                        if '.' in full_cmd:
                            # Look for package-like patterns (com.example.app)
                            import re
                            package_match = re.search(r'([a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*)', full_cmd)
                            if package_match:
                                app_info['package_name'] = package_match.group(1)
                            else:
                                app_info['package_name'] = parts[1]

        except Exception as e:
            logger.debug("Failed to get app info for PID %d: %s", pid, e)

        return app_info

    async def kill_process(self, process: ProcessInfo) -> bool:
        """Kill a process and log the action with detailed app information."""
        try:
            # Get detailed app information before killing
            app_info = await self.get_app_info(process.pid)
            
            logger.warning(
                "Killing high CPU process: PID=%d, CPU=%.1f%%, Command=%s, "
                "Package=%s, App=%s, User=%s",
                process.pid, process.cpu_percent, process.command,
                app_info['package_name'], app_info['app_name'], app_info['user']
            )

            # Try graceful termination first
            proc = await asyncio.create_subprocess_exec(
                'kill', '-TERM', str(process.pid),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=2.0)

            if proc.returncode == 0:
                logger.info(
                    "Successfully sent TERM signal to PID %d (%s - %s)",
                    process.pid, app_info['package_name'], app_info['app_name']
                )
                return True

            # If graceful termination failed, try force kill
            logger.warning(
                "TERM failed for PID %d (%s), trying KILL: %s",
                process.pid, app_info['package_name'], stderr.decode()
            )

            proc = await asyncio.create_subprocess_exec(
                'kill', '-KILL', str(process.pid),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=2.0)

            if proc.returncode == 0:
                logger.info(
                    "Successfully killed PID %d (%s - %s) with KILL signal",
                    process.pid, app_info['package_name'], app_info['app_name']
                )
                return True
            else:
                logger.error(
                    "Failed to kill PID %d (%s): %s",
                    process.pid, app_info['package_name'], stderr.decode()
                )
                return False

        except Exception as e:
            logger.error("Exception while killing PID %d: %s", process.pid, e)
            return False

    def is_protected_process(self, process: ProcessInfo) -> bool:
        """Check if a process should be protected from automatic killing."""
        command_lower = process.command.lower()

        for protected in self.protected_processes:
            if protected in command_lower:
                return True

        # Don't kill processes owned by root unless they're clearly user processes
        if process.user == 'root' and not any(
            app in command_lower for app in ['app', 'android', 'game', 'browser']
        ):
            return True

        return False

    async def process_high_cpu_processes(self, high_cpu_processes: List[ProcessInfo]) -> None:
        """Process high CPU usage violations and kill processes if necessary."""
        if not self.enable_auto_kill:
            return

        current_time = datetime.now()

        for process in high_cpu_processes:
            pid = process.pid

            # Skip protected processes
            if self.is_protected_process(process):
                logger.debug(
                    "Skipping protected process: PID=%d, Command=%s",
                    pid, process.command
                )
                continue

            # Get service name if not already available
            if process.service_name is None:
                process.service_name = await self.get_service_name(pid)

            # Get app information for better logging
            app_info = await self.get_app_info(pid)

            # Track violations
            if pid not in self.violation_counts:
                self.violation_counts[pid] = 0
                self.violation_timestamps[pid] = current_time

            self.violation_counts[pid] += 1

            logger.info(
                "High CPU process detected: PID=%d, CPU=%.1f%%, Violations=%d/%d, "
                "Command=%s, Package=%s, App=%s, User=%s",
                pid, process.cpu_percent, self.violation_counts[pid],
                self.kill_after_violations, process.command,
                app_info['package_name'], app_info['app_name'], app_info['user']
            )

            # Kill if violation threshold reached
            if self.violation_counts[pid] >= self.kill_after_violations:
                success = await self.kill_process(process)

                if success:
                    # Remove from tracking after successful kill
                    del self.violation_counts[pid]
                    del self.violation_timestamps[pid]

        # Clean up old violations (processes that no longer exceed threshold)
        current_pids = {p.pid for p in high_cpu_processes}
        expired_pids = []

        for pid in self.violation_counts:
            if pid not in current_pids:
                # Process no longer violating - check if we should clean up
                last_violation = self.violation_timestamps.get(pid, current_time)
                if current_time - last_violation > timedelta(minutes=5):
                    expired_pids.append(pid)

        for pid in expired_pids:
            logger.debug("Cleaning up violation tracking for PID %d", pid)
            del self.violation_counts[pid]
            del self.violation_timestamps[pid]

    async def get_performance_snapshot(self) -> PerformanceMetrics:
        """Get a single performance snapshot."""
        output = await self.get_top_output()
        return self.parse_top_output(output)

    async def start_monitoring(self) -> None:
        """Start continuous performance monitoring."""
        if self._monitoring:
            logger.warning("Performance monitoring is already running")
            return

        self._monitoring = True
        logger.info(
            "Starting Termux performance monitoring (interval=%.1fs, threshold=%.1f%%, auto_kill=%s)",
            self.monitoring_interval, self.cpu_threshold, self.enable_auto_kill
        )

        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring:
            return

        logger.info("Stopping performance monitoring")
        self._monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        try:
            while self._monitoring:
                try:
                    # Get performance metrics
                    metrics = await self.get_performance_snapshot()

                    if metrics.high_cpu_processes:
                        logger.info(
                            "Performance snapshot: CPU=%.1f%%, Memory=%.1f%%, High CPU processes=%d",
                            metrics.total_cpu_usage, metrics.total_memory_usage,
                            len(metrics.high_cpu_processes)
                        )

                        # Process high CPU processes
                        await self.process_high_cpu_processes(metrics.high_cpu_processes)

                    # Wait for next monitoring cycle
                    await asyncio.sleep(self.monitoring_interval)

                except Exception as e:
                    logger.error("Error in monitoring loop: %s", e)
                    await asyncio.sleep(self.monitoring_interval)

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error("Monitoring loop failed: %s", e)
        finally:
            self._monitoring = False

    async def get_system_info(self) -> Dict[str, any]:
        """Get general system information."""
        try:
            system_info = {
                'monitoring_active': self._monitoring,
                'cpu_threshold': self.cpu_threshold,
                'auto_kill_enabled': self.enable_auto_kill,
                'active_violations': len(self.violation_counts)
            }
            
            # Try to get load average (Linux/Termux)
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_line = f.read().strip()
                    load_parts = load_line.split()
                    if len(load_parts) >= 3:
                        system_info['load_average'] = {
                            '1min': float(load_parts[0]),
                            '5min': float(load_parts[1]),
                            '15min': float(load_parts[2])
                        }
            except (FileNotFoundError, ValueError, IndexError) as e:
                logger.debug("Could not read load average: %s", e)
                system_info['load_average'] = {'1min': 0.0, '5min': 0.0, '15min': 0.0}

            # Try to get memory info (Linux/Termux)
            try:
                memory_info = {}
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if 'kB' in value:
                                try:
                                    value = int(value.split()[0]) * 1024  # Convert to bytes
                                except ValueError:
                                    pass
                            memory_info[key] = value
                system_info['memory'] = memory_info
            except (FileNotFoundError, ValueError) as e:
                logger.debug("Could not read memory info: %s", e)
                system_info['memory'] = {}

            return system_info

        except Exception as e:
            logger.error("Error getting system info: %s", e)
            return {
                'error': str(e),
                'monitoring_active': self._monitoring,
                'cpu_threshold': self.cpu_threshold,
                'auto_kill_enabled': self.enable_auto_kill,
                'active_violations': len(self.violation_counts)
            }