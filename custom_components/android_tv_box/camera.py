"""Camera platform for Android TV Box integration."""
import logging
import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import aiohttp

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 3  # seconds - screenshot interval


class AndroidTVBoxCameraCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box camera data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService, config: Dict[str, Any]):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box Camera",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service
        self.config = config
        self.screenshot_path = config.get("screenshot_path", "/sdcard/isgbackup/screenshot/")
        self.keep_count = config.get("screenshot_keep_count", 3)
        self._last_screenshot_time = 0

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            current_time = datetime.now()
            
            # Only take screenshot if enough time has passed
            if current_time.timestamp() - self._last_screenshot_time >= self.config.get("screenshot_interval", 3):
                await self._take_screenshot()
                self._last_screenshot_time = current_time.timestamp()
            
            # Clean up old screenshots
            await self._cleanup_screenshots()
            
            return {"last_update": current_time}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Android TV Box: {err}")

    async def _take_screenshot(self) -> None:
        """Take a screenshot and save it."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_{timestamp}.png"
            filepath = os.path.join(self.screenshot_path, filename)
            
            # Ensure directory exists
            await self.adb_service.shell_command(f"mkdir -p {self.screenshot_path}")
            
            # Take screenshot
            success = await self.adb_service.take_screenshot(filepath)
            if success:
                _LOGGER.debug(f"Screenshot saved: {filepath}")
            else:
                _LOGGER.error(f"Failed to take screenshot: {filepath}")
                
        except Exception as e:
            _LOGGER.error(f"Screenshot error: {e}")

    async def _cleanup_screenshots(self) -> None:
        """Clean up old screenshots, keeping only the most recent ones."""
        try:
            # List all screenshot files
            result = await self.adb_service.shell_command(f"ls -t {self.screenshot_path}/screen_*.png 2>/dev/null || true")
            
            if not result.strip():
                return
                
            files = [f.strip() for f in result.split('\n') if f.strip()]
            
            # Remove old files if we have more than keep_count
            if len(files) > self.keep_count:
                files_to_remove = files[self.keep_count:]
                for file in files_to_remove:
                    await self.adb_service.shell_command(f"rm -f {file}")
                    _LOGGER.debug(f"Removed old screenshot: {file}")
                    
        except Exception as e:
            _LOGGER.error(f"Screenshot cleanup error: {e}")

    async def get_latest_screenshot(self) -> Optional[bytes]:
        """Get the latest screenshot as bytes."""
        try:
            # Get the most recent screenshot file
            result = await self.adb_service.shell_command(f"ls -t {self.screenshot_path}/screen_*.png 2>/dev/null | head -1")
            
            if not result.strip():
                return None
                
            latest_file = result.strip()
            
            # Pull the file from device to local temp location
            temp_file = f"/tmp/android_tv_screenshot_{datetime.now().timestamp()}.png"
            
            # Use adb pull to get the file
            cmd = ["pull", latest_file, temp_file]
            result = await self.adb_service._run_command(cmd)
            
            if os.path.exists(temp_file):
                with open(temp_file, 'rb') as f:
                    data = f.read()
                os.remove(temp_file)  # Clean up temp file
                return data
            else:
                _LOGGER.error(f"Failed to pull screenshot: {latest_file}")
                return None
                
        except Exception as e:
            _LOGGER.error(f"Get screenshot error: {e}")
            return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box camera from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxCameraCoordinator(hass, adb_service, config)
    
    # Create camera entity
    entity = AndroidTVBoxCamera(coordinator, config)
    async_add_entities([entity])


class AndroidTVBoxCamera(Camera):
    """Representation of an Android TV Box camera."""

    _attr_has_entity_name = True
    _attr_name = "Screen"

    def __init__(self, coordinator: AndroidTVBoxCameraCoordinator, config: Dict[str, Any]):
        """Initialize the camera."""
        super().__init__()
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_camera_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "Android",
            "model": "TV Box",
        }

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return bytes of camera image."""
        return await self.coordinator.get_latest_screenshot()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        self.coordinator.async_remove_listener(self._handle_coordinator_update)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
