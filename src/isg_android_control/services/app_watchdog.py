from __future__ import annotations

import asyncio
import logging
from typing import Optional, Set
from datetime import datetime, timedelta

from ..core.adb import ADBController, ADBError

logger = logging.getLogger(__name__)


class AppWatchdog:
    """
    Monitors specific apps and restarts them if they're not running.

    Optimized for monitoring critical apps like ISG that should always be running.
    Uses efficient ADB commands and configurable check intervals.
    """

    def __init__(
        self,
        adb: ADBController,
        target_packages: Set[str],
        check_interval: float = 300.0,  # 5 minutes default
        restart_attempts: int = 3,
        restart_delay: float = 10.0
    ):
        self.adb = adb
        self.target_packages = target_packages
        self.check_interval = check_interval
        self.restart_attempts = restart_attempts
        self.restart_delay = restart_delay

        # State tracking
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._restart_counts = {pkg: 0 for pkg in target_packages}
        self._last_restart_times = {pkg: None for pkg in target_packages}
        self._consecutive_failures = {pkg: 0 for pkg in target_packages}

    async def check_app_running(self, package: str) -> bool:
        """Check if a specific app package is currently running."""
        try:
            # Use 'ps' command to check if the app process is running
            # More efficient than checking foreground app or full process list
            output = await self.adb._run("shell", "ps", "-A", timeout=10.0)

            # Look for the package name in process list
            lines = output.strip().split('\n')
            for line in lines:
                if package in line:
                    # Verify it's actually the app process, not just a substring match
                    parts = line.split()
                    if len(parts) >= 9:  # Standard ps output format
                        process_name = parts[8]  # COMMAND column
                        if process_name == package or process_name.endswith(f":{package}"):
                            logger.debug("App %s is running: %s", package, process_name)
                            return True

            logger.debug("App %s is not running", package)
            return False

        except Exception as e:
            logger.warning("Error checking if app %s is running: %s", package, e)
            return False  # Assume not running on error to trigger restart attempt

    async def restart_app(self, package: str) -> bool:
        """Restart an app by stopping and launching it."""
        try:
            logger.info("Attempting to restart app: %s", package)

            # First, try to stop the app (force-stop)
            try:
                await self.adb._run("shell", "am", "force-stop", package, timeout=15.0)
                logger.debug("Force-stopped app: %s", package)
            except Exception as e:
                logger.debug("Error force-stopping app %s (continuing): %s", package, e)

            # Wait a moment for the app to fully stop
            await asyncio.sleep(2.0)

            # Launch the app using monkey command (more reliable than am start)
            try:
                await self.adb._run(
                    "shell", "monkey", "-p", package, "-c",
                    "android.intent.category.LAUNCHER", "1",
                    timeout=20.0
                )
                logger.info("Successfully restarted app: %s", package)

                # Update restart tracking
                self._restart_counts[package] += 1
                self._last_restart_times[package] = datetime.now()
                self._consecutive_failures[package] = 0

                return True

            except Exception as e:
                logger.error("Error launching app %s: %s", package, e)
                return False

        except Exception as e:
            logger.error("Error restarting app %s: %s", package, e)
            return False

    async def check_and_restart_apps(self) -> None:
        """Check all target apps and restart any that are not running."""
        for package in self.target_packages:
            try:
                is_running = await self.check_app_running(package)

                if not is_running:
                    logger.warning("App %s is not running, attempting restart", package)

                    # Check if we've tried too many times recently
                    last_restart = self._last_restart_times[package]
                    if (last_restart and
                        datetime.now() - last_restart < timedelta(minutes=2)):
                        logger.warning(
                            "App %s was restarted recently (%s), skipping restart attempt",
                            package, last_restart
                        )
                        continue

                    # Attempt restart with retries
                    restart_success = False
                    for attempt in range(self.restart_attempts):
                        if attempt > 0:
                            logger.info("Restart attempt %d/%d for app %s",
                                      attempt + 1, self.restart_attempts, package)
                            await asyncio.sleep(self.restart_delay)

                        if await self.restart_app(package):
                            restart_success = True
                            break

                    if restart_success:
                        # Verify the app actually started
                        await asyncio.sleep(5.0)  # Give app time to start
                        if await self.check_app_running(package):
                            logger.info("App %s successfully restarted and verified running", package)
                        else:
                            logger.warning("App %s restart command succeeded but app not detected running", package)
                    else:
                        self._consecutive_failures[package] += 1
                        logger.error(
                            "Failed to restart app %s after %d attempts (consecutive failures: %d)",
                            package, self.restart_attempts, self._consecutive_failures[package]
                        )
                else:
                    # App is running, reset failure count
                    if self._consecutive_failures[package] > 0:
                        logger.debug("App %s is now running, resetting failure count", package)
                        self._consecutive_failures[package] = 0

            except Exception as e:
                logger.error("Error in watchdog check for app %s: %s", package, e)

    async def start_monitoring(self) -> None:
        """Start the app monitoring watchdog."""
        if self._monitoring:
            logger.warning("App watchdog is already running")
            return

        self._monitoring = True
        logger.info(
            "Starting app watchdog (interval=%.1fmin, packages=%s)",
            self.check_interval / 60, list(self.target_packages)
        )

        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop the app monitoring watchdog."""
        if not self._monitoring:
            return

        logger.info("Stopping app watchdog")
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
                    await self.check_and_restart_apps()

                    # Wait for next check interval
                    await asyncio.sleep(self.check_interval)

                except Exception as e:
                    logger.error("Error in app watchdog monitoring loop: %s", e)
                    # Continue monitoring with a shorter delay on errors
                    await asyncio.sleep(min(60.0, self.check_interval / 5))

        except asyncio.CancelledError:
            logger.info("App watchdog monitoring loop cancelled")
        except Exception as e:
            logger.error("App watchdog monitoring loop failed: %s", e)
        finally:
            self._monitoring = False

    def get_status(self) -> dict:
        """Get current watchdog status and statistics."""
        return {
            'monitoring': self._monitoring,
            'check_interval': self.check_interval,
            'target_packages': list(self.target_packages),
            'restart_counts': self._restart_counts.copy(),
            'last_restart_times': {
                pkg: time.isoformat() if time else None
                for pkg, time in self._last_restart_times.items()
            },
            'consecutive_failures': self._consecutive_failures.copy(),
            'restart_attempts': self.restart_attempts,
            'restart_delay': self.restart_delay
        }

    async def manual_restart(self, package: str) -> bool:
        """Manually restart a specific app."""
        if package not in self.target_packages:
            logger.warning("Package %s is not in watchdog targets", package)
            return False

        logger.info("Manual restart requested for app: %s", package)
        return await self.restart_app(package)

    async def add_target_package(self, package: str) -> None:
        """Add a new package to monitor."""
        if package not in self.target_packages:
            self.target_packages.add(package)
            self._restart_counts[package] = 0
            self._last_restart_times[package] = None
            self._consecutive_failures[package] = 0
            logger.info("Added package %s to watchdog targets", package)

    async def remove_target_package(self, package: str) -> None:
        """Remove a package from monitoring."""
        if package in self.target_packages:
            self.target_packages.remove(package)
            del self._restart_counts[package]
            del self._last_restart_times[package]
            del self._consecutive_failures[package]
            logger.info("Removed package %s from watchdog targets", package)


class ISGAppWatchdog(AppWatchdog):
    """Specialized watchdog for ISG app with predefined settings."""

    def __init__(self, adb: ADBController):
        super().__init__(
            adb=adb,
            target_packages={"com.linknlink.app.device.isg"},
            check_interval=300.0,  # 5 minutes
            restart_attempts=3,
            restart_delay=10.0
        )

    async def check_isg_app_health(self) -> dict:
        """Get detailed health information about the ISG app."""
        package = "com.linknlink.app.device.isg"

        try:
            # Check if running
            is_running = await self.check_app_running(package)

            # Get additional info if running
            additional_info = {}
            if is_running:
                try:
                    # Check if it's in foreground
                    foreground_info = await self.adb.top_app()
                    is_foreground = foreground_info.get("package") == package
                    additional_info["is_foreground"] = is_foreground

                    # Get memory usage
                    mem_info = await self.adb._run("shell", "dumpsys", "meminfo", package, timeout=10.0)
                    # Parse basic memory info
                    for line in mem_info.split('\n'):
                        if 'TOTAL PSS:' in line:
                            memory_mb = line.split(':')[1].strip().split()[0]
                            additional_info["memory_mb"] = memory_mb
                            break

                except Exception as e:
                    logger.debug("Error getting additional ISG app info: %s", e)

            return {
                "package": package,
                "is_running": is_running,
                "restart_count": self._restart_counts.get(package, 0),
                "last_restart": self._last_restart_times.get(package),
                "consecutive_failures": self._consecutive_failures.get(package, 0),
                **additional_info
            }

        except Exception as e:
            logger.error("Error checking ISG app health: %s", e)
            return {
                "package": package,
                "error": str(e),
                "is_running": False
            }