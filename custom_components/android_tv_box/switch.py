"""Switch platform for Android TV Box integration."""
import logging
from typing import Any, Dict
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import asyncio

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class AndroidTVBoxSwitchCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box switch data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box Switches",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        # Default data structure
        data = {
            "power_on": False,
            "wifi_on": False,
            "adb_connected": False
        }
        
        try:
            # Check if device is powered on
            try:
                is_on = await self.adb_service.is_powered_on()
                data["power_on"] = is_on
            except Exception as e:
                _LOGGER.warning(f"Failed to get power status: {e}")
            
            # Check WiFi status
            try:
                wifi_on = await self.adb_service.is_wifi_on()
                data["wifi_on"] = wifi_on
            except Exception as e:
                _LOGGER.warning(f"Failed to get WiFi status: {e}")
            
            # Check ADB connection status
            try:
                adb_connected = await self.adb_service.is_connected()
                data["adb_connected"] = adb_connected
            except Exception as e:
                _LOGGER.warning(f"Failed to get ADB connection status: {e}")
            
            return data
        except Exception as err:
            _LOGGER.error(f"Error communicating with Android TV Box: {err}")
            return data  # Return default data instead of raising exception


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box switches from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxSwitchCoordinator(hass, adb_service)
    
    await coordinator.async_config_entry_first_refresh()

    # Create switch entities
    entities = [
        AndroidTVBoxPowerSwitch(coordinator, config),
        AndroidTVBoxWiFiSwitch(coordinator, config),
        AndroidTVBoxADBSwitch(coordinator, config),
    ]
    
    async_add_entities(entities)


class AndroidTVBoxPowerSwitch(SwitchEntity):
    """Representation of an Android TV Box power switch."""

    _attr_has_entity_name = True
    _attr_name = "Power"

    def __init__(self, coordinator: AndroidTVBoxSwitchCoordinator, config: Dict[str, Any]):
        """Initialize the power switch."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_power_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        data = self.coordinator.data or {}
        return data.get("power_on", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.adb_service.power_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.adb_service.power_off()
        await self.coordinator.async_request_refresh()

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


class AndroidTVBoxWiFiSwitch(SwitchEntity):
    """Representation of an Android TV Box WiFi switch."""

    _attr_has_entity_name = True
    _attr_name = "WiFi"

    def __init__(self, coordinator: AndroidTVBoxSwitchCoordinator, config: Dict[str, Any]):
        """Initialize the WiFi switch."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_wifi_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        data = self.coordinator.data or {}
        return data.get("wifi_on", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.adb_service.wifi_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.adb_service.wifi_off()
        await self.coordinator.async_request_refresh()

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


class AndroidTVBoxADBSwitch(SwitchEntity):
    """Representation of an Android TV Box ADB connection switch."""

    _attr_has_entity_name = True
    _attr_name = "ADB Connection"

    def __init__(self, coordinator: AndroidTVBoxSwitchCoordinator, config: Dict[str, Any]):
        """Initialize the ADB connection switch."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_adb_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
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

    @property
    def icon(self) -> str:
        """Return the icon for the switch."""
        return "mdi:connection" if self.is_on else "mdi:lan-disconnect"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Connect ADB."""
        await self.coordinator.adb_service.connect()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disconnect ADB."""
        await self.coordinator.adb_service.disconnect()
        await self.coordinator.async_request_refresh()

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
        return True  # ADB switch should always be available
