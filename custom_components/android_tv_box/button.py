"""Button platform mapping remote keys to discrete Button entities."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)


KEY_BUTTONS = [
    ("Up", "key_up"),
    ("Down", "key_down"),
    ("Left", "key_left"),
    ("Right", "key_right"),
    ("Enter", "key_enter"),
    ("Back", "key_back"),
    ("Home", "key_home"),
    ("Play", "media_play"),
    ("Pause", "media_pause"),
    ("Stop", "media_stop"),
    ("Next", "media_next"),
    ("Previous", "media_previous"),
    ("Volume Up", "volume_up"),
    ("Volume Down", "volume_down"),
    ("Mute", "volume_mute"),
    ("Power On", "power_on"),
    ("Power Off", "power_off"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box buttons from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)

    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    entities: List[AndroidTVBoxButton] = []
    for label, method in KEY_BUTTONS:
        entities.append(AndroidTVBoxButton(adb_service, config, label, method))

    async_add_entities(entities)


class AndroidTVBoxButton(ButtonEntity):
    """A button that invokes a specific ADBService method."""

    _attr_has_entity_name = True

    def __init__(self, adb_service: ADBService, config: Dict[str, Any], label: str, method_name: str) -> None:
        self._adb = adb_service
        self._config = config
        self._label = label
        self._method = method_name
        uid = f"android_tv_box_button_{method_name}_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_unique_id = uid
        self._attr_name = label
        self._attr_device_info = {
            "identifiers": {("android_tv_box", f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}")},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    async def async_press(self) -> None:
        func = getattr(self._adb, self._method, None)
        if callable(func):
            await func()
        else:
            _LOGGER.warning("ADBService has no method %s for button %s", self._method, self._label)
