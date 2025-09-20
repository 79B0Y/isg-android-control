"""Select platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


class AndroidTVBoxSelectCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box select data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService, config: Dict[str, Any]):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box Select",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service
        self.config = config
        self.apps = config.get("apps", {})
        self.visible_apps = config.get("visible", [])

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        # Default data structure
        data = {
            "current_app": "Unknown",
            "current_app_name": None
        }
        
        try:
            # Get current app
            try:
                current_app = await self.adb_service.get_current_app()
                data["current_app"] = current_app
                
                # Find current app name from package name
                current_app_name = None
                for app_name, package_name in self.apps.items():
                    if package_name == current_app:
                        current_app_name = app_name
                        break
                
                data["current_app_name"] = current_app_name
            except Exception as e:
                _LOGGER.warning(f"Failed to get current app: {e}")
            
            return data
        except Exception as err:
            _LOGGER.error(f"Error communicating with Android TV Box: {err}")
            return data  # Return default data instead of raising exception


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box select from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxSelectCoordinator(hass, adb_service, config)
    # Ensure first refresh completes before entity is created
    await coordinator.async_config_entry_first_refresh()
    
    # Create select entity
    entity = AndroidTVBoxAppSelect(coordinator, config)
    async_add_entities([entity])


class AndroidTVBoxAppSelect(SelectEntity):
    """Representation of an Android TV Box app select."""

    _attr_has_entity_name = True
    _attr_name = "App Selector"

    def __init__(self, coordinator: AndroidTVBoxSelectCoordinator, config: Dict[str, Any]):
        """Initialize the app select."""
        self.coordinator = coordinator
        self.config = config
        
        # Use apps and visible_apps from coordinator, which has the correct config
        self.apps = coordinator.apps
        self.visible_apps = coordinator.visible_apps
        
        _LOGGER.info(f"Select entity initialized with apps: {self.apps}")
        _LOGGER.info(f"Select entity initialized with visible apps: {self.visible_apps}")
        _LOGGER.info(f"Coordinator config apps: {coordinator.config.get('apps', {})}")
        _LOGGER.info(f"Coordinator config visible: {coordinator.config.get('visible', [])}")
        self._attr_unique_id = f"android_tv_box_app_select_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def options(self) -> List[str]:
        """Return a list of available options."""
        if self.visible_apps:
            # Return only visible apps
            options = [app for app in self.visible_apps if app in self.apps]
        else:
            # Return all configured apps
            options = list(self.apps.keys())
        
        _LOGGER.info(f"Select options: {options}")
        return options

    @property
    def current_option(self) -> Optional[str]:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None
        
        current_app = self.coordinator.data.get("current_app")
        if not current_app:
            return None
        
        # Find app name from package name
        for app_name, package_name in self.apps.items():
            if package_name == current_app:
                _LOGGER.info(f"Current app: {app_name} ({package_name})")
                return app_name
        
        _LOGGER.warning(f"Unknown app package: {current_app}")
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.info(f"📱 SELECT OPTION CALLED: {option}")
        _LOGGER.info(f"Available apps: {list(self.apps.keys())}")
        
        if option not in self.apps:
            _LOGGER.error(f"❌ Unknown app: {option}, available apps: {list(self.apps.keys())}")
            return

        package_name = self.apps[option]
        _LOGGER.info(f"🚀 Launching app: {option} ({package_name})")
        
        try:
            success = await self.coordinator.adb_service.launch_app(package_name)
            if success:
                _LOGGER.info(f"✅ Successfully launched {option}")
                # Update coordinator data immediately
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"❌ Failed to launch {option}")
        except Exception as e:
            _LOGGER.error(f"💥 Exception launching {option}: {e}")

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
