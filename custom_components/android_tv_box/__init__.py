"""Android TV Box integration for Home Assistant."""
import asyncio
import logging
from typing import Dict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .config import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player", "switch", "camera", "sensor", "remote", "select", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Android TV Box component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Android TV Box from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store configuration
    hass.data[DOMAIN]["config"] = entry.data
    
    # Set up platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
    
    _LOGGER.info("Android TV Box config entry loaded successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    
    if unload_ok:
        hass.data[DOMAIN].pop("config", None)
    
    return unload_ok