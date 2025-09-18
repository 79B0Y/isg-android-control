"""Binary Sensor platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 30  # seconds


class AndroidTVBoxBinarySensorCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box binary sensor data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService, config: Dict[str, Any]):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box Binary Sensors",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service
        self.config = config
        self.isg_monitoring = config.get("isg_monitoring", True)
        self.isg_check_interval = config.get("isg_check_interval", 30)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            data = {}
            
            # Check iSG status if monitoring is enabled
            if self.isg_monitoring:
                isg_running = await self.adb_service.is_isg_running()
                data["isg_running"] = isg_running
                
                if not isg_running:
                    _LOGGER.warning("iSG is not running, attempting to wake it up...")
                    wake_success = await self.adb_service.wake_up_isg()
                    data["isg_wake_attempted"] = wake_success
                    if wake_success:
                        _LOGGER.info("iSG wake up successful")
                    else:
                        _LOGGER.error("iSG wake up failed")
                else:
                    data["isg_wake_attempted"] = False
            else:
                data["isg_running"] = None
                data["isg_wake_attempted"] = False
            
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Android TV Box: {err}")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box binary sensors from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxBinarySensorCoordinator(hass, adb_service, config)
    
    # Create binary sensor entities
    entities = []
    
    # Only create iSG sensor if monitoring is enabled
    if config.get("isg_monitoring", True):
        entities.append(AndroidTVBoxISGRunningSensor(coordinator, config))
    
    async_add_entities(entities)


class AndroidTVBoxISGRunningSensor(BinarySensorEntity):
    """Representation of an Android TV Box iSG running binary sensor."""

    _attr_has_entity_name = True
    _attr_name = "iSG Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: AndroidTVBoxBinarySensorCoordinator, config: Dict[str, Any]):
        """Initialize the iSG running sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_isg_running_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "Android",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if iSG is running."""
        return self.coordinator.data.get("isg_running", False)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {
            "wake_attempted": self.coordinator.data.get("isg_wake_attempted", False),
            "monitoring_enabled": self.config.get("isg_monitoring", True),
            "check_interval": self.config.get("isg_check_interval", 30),
        }

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
