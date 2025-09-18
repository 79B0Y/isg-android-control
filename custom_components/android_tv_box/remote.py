"""Remote platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box remote from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create remote entity
    entity = AndroidTVBoxRemote(adb_service, config)
    async_add_entities([entity])


class AndroidTVBoxRemote(RemoteEntity):
    """Representation of an Android TV Box remote."""

    _attr_has_entity_name = True
    _attr_name = "Remote"

    def __init__(self, adb_service: ADBService, config: Dict[str, Any]):
        """Initialize the remote."""
        self.adb_service = adb_service
        self.config = config
        self._attr_unique_id = f"android_tv_box_remote_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "Android",
            "model": "TV Box",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the remote is on."""
        # Remote is always available when device is connected
        return True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the remote on."""
        # Remote is always on when device is connected
        pass

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the remote off."""
        # Remote cannot be turned off
        pass

    async def async_send_command(self, command: List[str], **kwargs: Any) -> None:
        """Send a command to the device."""
        for cmd in command:
            await self._send_key_command(cmd)

    async def _send_key_command(self, command: str) -> None:
        """Send a key command to the device."""
        command_map = {
            "up": self.adb_service.key_up,
            "down": self.adb_service.key_down,
            "left": self.adb_service.key_left,
            "right": self.adb_service.key_right,
            "enter": self.adb_service.key_enter,
            "ok": self.adb_service.key_enter,
            "back": self.adb_service.key_back,
            "home": self.adb_service.key_home,
            "play": self.adb_service.media_play,
            "pause": self.adb_service.media_pause,
            "stop": self.adb_service.media_stop,
            "next": self.adb_service.media_next,
            "previous": self.adb_service.media_previous,
            "volume_up": self.adb_service.volume_up,
            "volume_down": self.adb_service.volume_down,
            "volume_mute": self.adb_service.volume_mute,
            "power_on": self.adb_service.power_on,
            "power_off": self.adb_service.power_off,
        }
        
        if command in command_map:
            try:
                await command_map[command]()
                _LOGGER.debug(f"Sent command: {command}")
            except Exception as e:
                _LOGGER.error(f"Failed to send command {command}: {e}")
        else:
            _LOGGER.warning(f"Unknown command: {command}")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.adb_service is not None
