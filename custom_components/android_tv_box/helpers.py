"""Helper functions for Android TV Box integration."""
from typing import Dict, Any, Optional

from homeassistant.core import HomeAssistant

from .adb_service import ADBService
from .config import DOMAIN


def get_adb_service(hass: HomeAssistant) -> Optional[ADBService]:
    """Get the ADB service instance."""
    if DOMAIN not in hass.data:
        return None
    return hass.data[DOMAIN].get("adb_service")


def get_config(hass: HomeAssistant) -> Optional[Dict[str, Any]]:
    """Get the configuration."""
    if DOMAIN not in hass.data:
        return None
    
    # First try yaml_config (from configuration.yaml), then fall back to config entry data
    yaml_config = hass.data[DOMAIN].get("yaml_config")
    if yaml_config:
        return yaml_config
    
    return hass.data[DOMAIN].get("config")


def set_config(hass: HomeAssistant, config: Dict[str, Any]) -> None:
    """Set the configuration."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["config"] = config
