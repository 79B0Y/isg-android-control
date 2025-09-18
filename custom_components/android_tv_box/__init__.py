"""Android TV Box integration for Home Assistant."""
import asyncio
import logging
from typing import Dict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .config import DOMAIN, CONFIG_SCHEMA
from .adb_service import ADBService
from .services import async_setup_services, async_unload_services
from .web_server import AndroidTVBoxWebServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player", "switch", "camera", "sensor", "remote", "select", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Android TV Box component."""
    if DOMAIN not in config:
        return True

    # Validate configuration
    config[DOMAIN] = CONFIG_SCHEMA[DOMAIN](config[DOMAIN])
    
    # Store configuration in hass data
    hass.data[DOMAIN] = {
        "config": config[DOMAIN],
        "adb_service": None,
        "entities": {}
    }

    # Initialize ADB service
    adb_config = config[DOMAIN]
    adb_service = ADBService(
        host=adb_config.get("host", "127.0.0.1"),
        port=adb_config.get("port", 5555),
        adb_path=adb_config.get("adb_path", "/usr/bin/adb")
    )

    # Test connection
    if await adb_service.connect():
        hass.data[DOMAIN]["adb_service"] = adb_service
        _LOGGER.info("Android TV Box integration initialized successfully")
    else:
        _LOGGER.error("Failed to connect to Android TV Box")
        return False

    # Load platforms
    for platform in PLATFORMS:
        if adb_config.get(platform, True):
            hass.async_create_task(
                hass.helpers.discovery.async_load_platform(
                    platform, DOMAIN, {}, config
                )
            )

    # Set up custom services
    await async_setup_services(hass)

    # Start web server
    web_server = AndroidTVBoxWebServer(hass, port=3003)
    if await web_server.start():
        hass.data[DOMAIN]["web_server"] = web_server
        _LOGGER.info("Web management interface started on port 3003")
    else:
        _LOGGER.warning("Failed to start web management interface")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Android TV Box from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize ADB service
    adb_service = ADBService(
        host=entry.data.get("host", "127.0.0.1"),
        port=entry.data.get("port", 5555),
        adb_path=entry.data.get("adb_path", "/usr/bin/adb")
    )

    # Test connection
    if await adb_service.connect():
        hass.data[DOMAIN]["adb_service"] = adb_service
        hass.data[DOMAIN]["config"] = entry.data
        
        # Set up platforms
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "media_player")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "switch")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "camera")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "remote")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "select")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
        )
        
        # Set up custom services
        await async_setup_services(hass)
        
        # Start web server
        web_server = AndroidTVBoxWebServer(hass, port=3003)
        if await web_server.start():
            hass.data[DOMAIN]["web_server"] = web_server
            _LOGGER.info("Web management interface started on port 3003")
        else:
            _LOGGER.warning("Failed to start web management interface")
        
        _LOGGER.info("Android TV Box config entry loaded successfully")
        return True
    else:
        _LOGGER.error("Failed to connect to Android TV Box")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Disconnect ADB service
    if DOMAIN in hass.data and "adb_service" in hass.data[DOMAIN]:
        adb_service = hass.data[DOMAIN]["adb_service"]
        await adb_service.disconnect()
    
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
        hass.data[DOMAIN].pop("adb_service", None)
        hass.data[DOMAIN].pop("config", None)
        # Stop web server
        if "web_server" in hass.data[DOMAIN]:
            web_server = hass.data[DOMAIN]["web_server"]
            await web_server.stop()
            hass.data[DOMAIN].pop("web_server", None)
        # Unload custom services
        await async_unload_services(hass)
    
    return unload_ok


# Helper functions moved to helpers.py to avoid circular imports
