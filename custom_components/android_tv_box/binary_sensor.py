"""Binary Sensor platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


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
        # Default data structure
        data = {
            "isg_running": False,
            "isg_wake_attempted": False,
            "adb_connected": False,
            "high_cpu_warning": False
        }
        
        try:
            # Check ADB connection status
            try:
                adb_connected = await self.adb_service.is_connected()
                data["adb_connected"] = adb_connected
            except Exception as e:
                _LOGGER.warning(f"Failed to check ADB connection: {e}")
                data["adb_connected"] = False
            
            # Only check other services if ADB is connected
            if data["adb_connected"]:
                # Check iSG status if monitoring is enabled
                if self.isg_monitoring:
                    try:
                        isg_running = await self.adb_service.is_isg_running()
                        data["isg_running"] = isg_running
                        
                        if not isg_running:
                            _LOGGER.warning("iSG is not running, attempting to wake it up...")
                            try:
                                wake_success = await self.adb_service.wake_up_isg()
                                data["isg_wake_attempted"] = wake_success
                                if wake_success:
                                    _LOGGER.info("iSG wake up successful")
                                else:
                                    _LOGGER.error("iSG wake up failed")
                            except Exception as e:
                                _LOGGER.error(f"Failed to wake up iSG: {e}")
                                data["isg_wake_attempted"] = False
                        else:
                            data["isg_wake_attempted"] = False
                    except Exception as e:
                        _LOGGER.warning(f"Failed to check iSG status: {e}")
                
                # Check system performance for high CPU warning
                try:
                    performance = await self.adb_service.get_system_performance()
                    cpu_usage = performance.get("cpu_usage", 0)
                    cpu_threshold = self.config.get("cpu_threshold", 50)
                    data["high_cpu_warning"] = cpu_usage > cpu_threshold
                except Exception as e:
                    _LOGGER.debug(f"Failed to get system performance: {e}")
            
            return data
        except Exception as err:
            _LOGGER.error(f"Error communicating with Android TV Box: {err}")
            return data  # Return default data instead of raising exception


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
    # Ensure first refresh completes before entities are created
    await coordinator.async_config_entry_first_refresh()
    
    # Create binary sensor entities
    entities = [
        AndroidTVBoxConnectionSensor(coordinator, config),
        AndroidTVBoxHighCPUWarningSensor(coordinator, config),
    ]
    
    # Only create iSG sensor if monitoring is enabled
    if config.get("isg_monitoring", True):
        entities.append(AndroidTVBoxISGRunningSensor(coordinator, config))
    
    async_add_entities(entities)


class AndroidTVBoxConnectionSensor(BinarySensorEntity):
    """Representation of an Android TV Box connection status binary sensor."""

    _attr_has_entity_name = True
    _attr_name = "Connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: AndroidTVBoxBinarySensorCoordinator, config: Dict[str, Any]):
        """Initialize the connection sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_connection_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if ADB is connected."""
        data = self.coordinator.data or {}
        return data.get("adb_connected", False)

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
        return True  # Connection sensor is always available


class AndroidTVBoxHighCPUWarningSensor(BinarySensorEntity):
    """Representation of an Android TV Box high CPU warning binary sensor."""

    _attr_has_entity_name = True
    _attr_name = "High CPU Warning"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: AndroidTVBoxBinarySensorCoordinator, config: Dict[str, Any]):
        """Initialize the high CPU warning sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_high_cpu_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if CPU usage is high."""
        data = self.coordinator.data or {}
        return data.get("high_cpu_warning", False)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {"cpu_threshold": self.config.get("cpu_threshold", 50)}

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


class AndroidTVBoxISGRunningSensor(BinarySensorEntity):
    """Representation of an Android TV Box iSG running binary sensor."""

    _attr_has_entity_name = True
    _attr_name = "iSG Running"
    # RUNNING device class is not available in older HA versions; keep None for compatibility
    _attr_device_class = None

    def __init__(self, coordinator: AndroidTVBoxBinarySensorCoordinator, config: Dict[str, Any]):
        """Initialize the iSG running sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_isg_running_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if iSG is running."""
        data = self.coordinator.data or {}
        return data.get("isg_running", False)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "wake_attempted": data.get("isg_wake_attempted", False),
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
