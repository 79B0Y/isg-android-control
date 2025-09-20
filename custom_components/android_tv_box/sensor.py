"""Sensor platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


class AndroidTVBoxSensorCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box sensor data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService, config: Dict[str, Any]):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box Sensors",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service
        self.config = config
        self.cpu_threshold = config.get("cpu_threshold", 50)
        self._high_cpu_count = 0

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        # Default data structure
        data = {
            "brightness": 0,
            "ssid": "Unknown",
            "ip_address": "Unknown", 
            "current_app": "Unknown",
            "cpu_usage": 0,
            "memory_used": 0,
            "high_cpu_warning": False,
            "high_cpu_count": 0
        }
        
        try:
            # Get brightness
            try:
                brightness = await self.adb_service.get_brightness()
                data["brightness"] = brightness
            except Exception as e:
                _LOGGER.warning(f"Failed to get brightness: {e}")
            
            # Get WiFi info
            try:
                wifi_info = await self.adb_service.get_wifi_info()
                data.update(wifi_info)
            except Exception as e:
                _LOGGER.warning(f"Failed to get WiFi info: {e}")
            
            # Get current app
            try:
                current_app = await self.adb_service.get_current_app()
                data["current_app"] = current_app
            except Exception as e:
                _LOGGER.warning(f"Failed to get current app: {e}")
            
            # Get system performance
            try:
                performance = await self.adb_service.get_system_performance()
                # Normalize keys for sensors
                # cpu_usage_percent -> cpu_usage
                if "cpu_usage_percent" in performance:
                    data["cpu_usage"] = performance.get("cpu_usage_percent")
                # memory_used_mb -> memory_used
                if "memory_used_mb" in performance:
                    data["memory_used"] = performance.get("memory_used_mb")
                # Keep other fields if needed later
                data.update({
                    "memory_usage_percent": performance.get("memory_usage_percent"),
                    "memory_total_mb": performance.get("memory_total_mb"),
                    "highest_cpu_process": performance.get("highest_cpu_process"),
                    "highest_cpu_pid": performance.get("highest_cpu_pid"),
                    "highest_cpu_percent": performance.get("highest_cpu_percent"),
                    "highest_cpu_service": performance.get("highest_cpu_service"),
                })
            except Exception as e:
                _LOGGER.warning(f"Failed to get system performance: {e}")
            
            # Check for high CPU usage
            cpu_usage = data.get("cpu_usage", 0)
            if cpu_usage > self.cpu_threshold:
                self._high_cpu_count += 1
                if self._high_cpu_count >= 4:  # 4 consecutive high readings
                    data["high_cpu_warning"] = True
                    data["high_cpu_count"] = self._high_cpu_count
                    _LOGGER.warning(f"High CPU usage detected: {cpu_usage}% for {self._high_cpu_count} consecutive readings")
            else:
                self._high_cpu_count = 0
                data["high_cpu_warning"] = False
                data["high_cpu_count"] = 0
            
            return data
        except Exception as err:
            _LOGGER.error(f"Error communicating with Android TV Box: {err}")
            return data  # Return default data instead of raising exception


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box sensors from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxSensorCoordinator(hass, adb_service, config)
    
    # Create sensor entities
    entities = [
        AndroidTVBoxBrightnessSensor(coordinator, config),
        AndroidTVBoxWiFiSSIDSensor(coordinator, config),
        AndroidTVBoxIPAddressSensor(coordinator, config),
        AndroidTVBoxCurrentAppSensor(coordinator, config),
        AndroidTVBoxCPUUsageSensor(coordinator, config),
        AndroidTVBoxMemoryUsageSensor(coordinator, config),
        AndroidTVBoxHighCPUWarningSensor(coordinator, config),
    ]
    
    async_add_entities(entities)


class AndroidTVBoxBrightnessSensor(SensorEntity):
    """Representation of an Android TV Box brightness sensor."""

    _attr_has_entity_name = True
    _attr_name = "Brightness"
    _attr_native_unit_of_measurement = None
    _attr_device_class = None  # Not lux; represents 0-255 Android brightness
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the brightness sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_brightness_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[int]:
        """Return the brightness value."""
        return self.coordinator.data.get("brightness")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxWiFiSSIDSensor(SensorEntity):
    """Representation of an Android TV Box WiFi SSID sensor."""

    _attr_has_entity_name = True
    _attr_name = "WiFi SSID"

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the WiFi SSID sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_wifi_ssid_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[str]:
        """Return the WiFi SSID."""
        return self.coordinator.data.get("ssid")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxIPAddressSensor(SensorEntity):
    """Representation of an Android TV Box IP address sensor."""

    _attr_has_entity_name = True
    _attr_name = "IP Address"

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the IP address sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_ip_address_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[str]:
        """Return the IP address."""
        return self.coordinator.data.get("ip_address")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxCurrentAppSensor(SensorEntity):
    """Representation of an Android TV Box current app sensor."""

    _attr_has_entity_name = True
    _attr_name = "Current App"

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the current app sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_current_app_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[str]:
        """Return the current app."""
        return self.coordinator.data.get("current_app")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxCPUUsageSensor(SensorEntity):
    """Representation of an Android TV Box CPU usage sensor."""

    _attr_has_entity_name = True
    _attr_name = "CPU Usage"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = None  # CPU_USAGE not available in this HA version
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the CPU usage sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_cpu_usage_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[float]:
        """Return the CPU usage."""
        return self.coordinator.data.get("cpu_usage")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxMemoryUsageSensor(SensorEntity):
    """Representation of an Android TV Box memory usage sensor."""

    _attr_has_entity_name = True
    _attr_name = "Memory Usage"
    _attr_native_unit_of_measurement = "MB"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the memory usage sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_memory_usage_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> Optional[int]:
        """Return the memory usage."""
        return self.coordinator.data.get("memory_used")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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


class AndroidTVBoxHighCPUWarningSensor(SensorEntity):
    """Representation of an Android TV Box high CPU warning sensor."""

    _attr_has_entity_name = True
    _attr_name = "High CPU Warning"

    def __init__(self, coordinator: AndroidTVBoxSensorCoordinator, config: Dict[str, Any]):
        """Initialize the high CPU warning sensor."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_high_cpu_warning_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "Android",
            "model": "TV Box",
        }

    @property
    def native_value(self) -> str:
        """Return the high CPU warning status."""
        if self.coordinator.data.get("high_cpu_warning", False):
            count = self.coordinator.data.get("high_cpu_count", 0)
            return f"High CPU detected for {count} consecutive readings"
        return "Normal"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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
