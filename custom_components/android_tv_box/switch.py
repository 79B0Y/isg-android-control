"""Switch platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import asyncio

from . import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 30  # seconds


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
        try:
            data = {}
            
            # Check if device is powered on
            is_on = await self.adb_service.is_powered_on()
            data["power_on"] = is_on
            
            # Check WiFi status
            wifi_on = await self.adb_service.is_wifi_on()
            data["wifi_on"] = wifi_on
            
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Android TV Box: {err}")


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
    
    # Create switch entities
    entities = [
        AndroidTVBoxPowerSwitch(coordinator, config),
        AndroidTVBoxWiFiSwitch(coordinator, config),
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
            "manufacturer": "Android",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get("power_on", False)

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
            "manufacturer": "Android",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get("wifi_on", False)

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
