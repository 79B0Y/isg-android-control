from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from ..core.adb import ADBController
from .performance_monitor import TermuxPerformanceMonitor
from .app_watchdog import ISGAppWatchdog
from .cec_controller import CECController

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(
        self,
        adb: ADBController,
        enable_termux_monitor: bool = True,
        enable_app_watchdog: bool = True,
        enable_cec: bool = True
    ) -> None:
        self.adb = adb
        self.performance_monitor: Optional[TermuxPerformanceMonitor] = None
        self.app_watchdog: Optional[ISGAppWatchdog] = None
        self.cec_controller: Optional[CECController] = None

        if enable_termux_monitor:
            self.performance_monitor = TermuxPerformanceMonitor(
                cpu_threshold=50.0,  # Kill processes using >50% CPU
                monitoring_interval=0.5,  # Check every 500ms
                kill_after_violations=3,  # Kill after 3 consecutive violations
                enable_auto_kill=True
            )

        if enable_app_watchdog:
            self.app_watchdog = ISGAppWatchdog(adb)

        if enable_cec:
            self.cec_controller = CECController(
                device_name="ISG Android Controller",
                physical_address="1.0.0.0"
            )

    async def start_performance_monitoring(self) -> None:
        """Start the Termux performance monitoring if available."""
        if self.performance_monitor:
            try:
                await self.performance_monitor.start_monitoring()
                logger.info("Started Termux performance monitoring")
            except Exception as e:
                logger.error("Failed to start performance monitoring: %s", e)

    async def stop_performance_monitoring(self) -> None:
        """Stop the Termux performance monitoring."""
        if self.performance_monitor:
            try:
                await self.performance_monitor.stop_monitoring()
                logger.info("Stopped Termux performance monitoring")
            except Exception as e:
                logger.error("Failed to stop performance monitoring: %s", e)

    async def start_app_watchdog(self) -> None:
        """Start the ISG app watchdog if available."""
        if self.app_watchdog:
            try:
                await self.app_watchdog.start_monitoring()
                logger.info("Started ISG app watchdog")
            except Exception as e:
                logger.error("Failed to start app watchdog: %s", e)

    async def stop_app_watchdog(self) -> None:
        """Stop the ISG app watchdog."""
        if self.app_watchdog:
            try:
                await self.app_watchdog.stop_monitoring()
                logger.info("Stopped ISG app watchdog")
            except Exception as e:
                logger.error("Failed to stop app watchdog: %s", e)

    async def start_cec_controller(self) -> None:
        """Start the CEC controller if available."""
        if self.cec_controller:
            try:
                success = await self.cec_controller.initialize()
                if success:
                    logger.info("Started CEC controller")
                else:
                    logger.warning("Failed to initialize CEC controller")
            except Exception as e:
                logger.error("Failed to start CEC controller: %s", e)

    async def stop_cec_controller(self) -> None:
        """Stop the CEC controller."""
        if self.cec_controller:
            try:
                await self.cec_controller.cleanup()
                logger.info("Stopped CEC controller")
            except Exception as e:
                logger.error("Failed to stop CEC controller: %s", e)

    async def snapshot(self) -> Dict[str, Any]:
        """Get comprehensive system metrics from both ADB and Termux monitoring."""
        metrics = {}

        # Get ADB-based metrics (existing functionality)
        try:
            adb_metrics = await self.adb.metrics()
            metrics['adb'] = adb_metrics
        except Exception as e:
            logger.warning("Failed to get ADB metrics: %s", e)
            metrics['adb'] = {'error': str(e)}

        # Get Termux performance metrics if available
        if self.performance_monitor:
            try:
                # Get current performance snapshot
                perf_snapshot = await self.performance_monitor.get_performance_snapshot()
                metrics['performance'] = {
                    'timestamp': perf_snapshot.timestamp.isoformat(),
                    'total_cpu_usage': perf_snapshot.total_cpu_usage,
                    'total_memory_usage': perf_snapshot.total_memory_usage,
                    'process_count': len(perf_snapshot.processes),
                    'high_cpu_process_count': len(perf_snapshot.high_cpu_processes),
                    'high_cpu_processes': [
                        {
                            'pid': p.pid,
                            'user': p.user,
                            'cpu_percent': p.cpu_percent,
                            'mem_percent': p.mem_percent,
                            'command': p.command,
                            'service_name': p.service_name
                        }
                        for p in perf_snapshot.high_cpu_processes
                    ]
                }

                # Get system info
                system_info = await self.performance_monitor.get_system_info()
                metrics['system'] = system_info

            except Exception as e:
                logger.warning("Failed to get performance metrics: %s", e)
                metrics['performance'] = {'error': str(e)}

        # Get app watchdog metrics if available
        if self.app_watchdog:
            try:
                # Get watchdog status
                watchdog_status = self.app_watchdog.get_status()
                metrics['app_watchdog'] = watchdog_status

                # Get ISG app health info
                isg_health = await self.app_watchdog.check_isg_app_health()
                metrics['isg_app'] = isg_health

            except Exception as e:
                logger.warning("Failed to get app watchdog metrics: %s", e)
                metrics['app_watchdog'] = {'error': str(e)}

        # Get CEC controller metrics if available
        if self.cec_controller:
            try:
                # Get TV/CEC status
                tv_status = await self.cec_controller.get_tv_status()
                metrics['cec'] = tv_status

                # Get available CEC commands
                cec_commands = self.cec_controller.get_available_commands()
                metrics['cec']['available_commands'] = list(cec_commands.keys())

            except Exception as e:
                logger.warning("Failed to get CEC metrics: %s", e)
                metrics['cec'] = {'error': str(e)}

        return metrics

    async def get_performance_status(self) -> Dict[str, Any]:
        """Get status of the performance monitoring system."""
        if not self.performance_monitor:
            return {'enabled': False, 'reason': 'Performance monitor not initialized'}

        try:
            system_info = await self.performance_monitor.get_system_info()
            return {
                'enabled': True,
                'monitoring_active': system_info.get('monitoring_active', False),
                'cpu_threshold': system_info.get('cpu_threshold', 50.0),
                'auto_kill_enabled': system_info.get('auto_kill_enabled', True),
                'active_violations': system_info.get('active_violations', 0),
                'load_average': system_info.get('load_average', {}),
            }
        except Exception as e:
            return {'enabled': True, 'error': str(e)}

    async def get_app_watchdog_status(self) -> Dict[str, Any]:
        """Get status of the app watchdog system."""
        if not self.app_watchdog:
            return {'enabled': False, 'reason': 'App watchdog not initialized'}

        try:
            status = self.app_watchdog.get_status()
            # Add ISG app health info
            isg_health = await self.app_watchdog.check_isg_app_health()
            status['isg_app_health'] = isg_health
            return status
        except Exception as e:
            return {'enabled': True, 'error': str(e)}

    async def restart_isg_app(self) -> Dict[str, Any]:
        """Manually restart the ISG app."""
        if not self.app_watchdog:
            return {'success': False, 'error': 'App watchdog not available'}

        try:
            success = await self.app_watchdog.manual_restart("com.linknlink.app.device.isg")
            return {'success': success, 'package': 'com.linknlink.app.device.isg'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_cec_status(self) -> Dict[str, Any]:
        """Get CEC controller status."""
        if not self.cec_controller:
            return {'enabled': False, 'reason': 'CEC controller not initialized'}

        try:
            status = await self.cec_controller.get_tv_status()
            commands = self.cec_controller.get_available_commands()
            status['available_commands'] = list(commands.keys())
            return status
        except Exception as e:
            return {'enabled': True, 'error': str(e)}

    async def send_cec_command(self, command: str) -> Dict[str, Any]:
        """Send a CEC command to the TV."""
        if not self.cec_controller:
            return {'success': False, 'error': 'CEC controller not available'}

        try:
            success = await self.cec_controller.send_command(command)
            return {'success': success, 'command': command}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def scan_cec_devices(self) -> Dict[str, Any]:
        """Scan for CEC devices on the network."""
        if not self.cec_controller:
            return {'success': False, 'error': 'CEC controller not available'}

        try:
            devices = await self.cec_controller.scan_devices()
            return {
                'success': True,
                'devices': [
                    {
                        'address': dev.address,
                        'name': dev.name,
                        'vendor': dev.vendor,
                        'device_type': dev.device_type,
                        'power_status': dev.power_status,
                        'active_source': dev.active_source
                    }
                    for dev in devices
                ],
                'count': len(devices)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

