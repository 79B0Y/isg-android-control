"""Android TV Box integration for Home Assistant."""
import asyncio
import logging
from typing import Dict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .config import DOMAIN
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.CAMERA,
    Platform.SENSOR,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Android TV Box component from configuration.yaml."""
    # This integration is primarily configured via config flow
    # but we support configuration.yaml for backward compatibility
    if DOMAIN in config:
        # Import from configuration.yaml
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "import"}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Android TV Box from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store configuration
    hass.data[DOMAIN]["config"] = entry.data

    # Create ADB service
    host = entry.data.get("host", "127.0.0.1")
    port = entry.data.get("port", 5555)
    adb_path = entry.data.get("adb_path", "/usr/bin/adb")

    adb_service = ADBService(host=host, port=port, adb_path=adb_path)

    # Test connection
    connected = await adb_service.connect()
    if not connected:
        _LOGGER.warning(f"Failed to connect to Android device at {host}:{port}")

    # Store ADB service
    hass.data[DOMAIN]["adb_service"] = adb_service

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Android TV Box config entry loaded successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Disconnect ADB service
        if DOMAIN in hass.data and "adb_service" in hass.data[DOMAIN]:
            adb_service = hass.data[DOMAIN]["adb_service"]
            await adb_service.disconnect()

        # Clean up data
        hass.data[DOMAIN].pop("config", None)
        hass.data[DOMAIN].pop("adb_service", None)

    return unload_ok