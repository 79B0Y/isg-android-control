"""Custom services for Android TV Box integration."""
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent

from . import DOMAIN
from .helpers import get_adb_service, get_config
from .config import (
    SERVICE_SCREENSHOT_SCHEMA,
    SERVICE_LAUNCH_APP_SCHEMA,
    SERVICE_SET_BRIGHTNESS_SCHEMA,
    SERVICE_SET_VOLUME_SCHEMA,
    SERVICE_KILL_PROCESS_SCHEMA,
    SERVICE_WAKE_ISG_SCHEMA,
    SERVICE_RESTART_ISG_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up custom services."""
    
    async def take_screenshot_service(call: ServiceCall) -> None:
        """Service to take a screenshot."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        filename = call.data.get("filename")
        keep_count = call.data.get("keep_count", 3)
        
        try:
            if filename:
                # Use custom filename
                filepath = f"/sdcard/isgbackup/screenshot/{filename}"
                success = await adb_service.take_screenshot(filepath)
            else:
                # Use default naming with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screen_{timestamp}.png"
                filepath = f"/sdcard/isgbackup/screenshot/{filename}"
                success = await adb_service.take_screenshot(filepath)
            
            if success:
                _LOGGER.info(f"Screenshot taken: {filename}")
            else:
                _LOGGER.error(f"Failed to take screenshot: {filename}")
                
        except Exception as e:
            _LOGGER.error(f"Screenshot service error: {e}")

    async def launch_app_service(call: ServiceCall) -> None:
        """Service to launch an app."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        package_name = call.data.get("package_name")
        activity_name = call.data.get("activity_name")
        
        try:
            success = await adb_service.launch_app(package_name, activity_name)
            if success:
                _LOGGER.info(f"App launched: {package_name}")
            else:
                _LOGGER.error(f"Failed to launch app: {package_name}")
                
        except Exception as e:
            _LOGGER.error(f"Launch app service error: {e}")

    async def set_brightness_service(call: ServiceCall) -> None:
        """Service to set screen brightness."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        brightness = call.data.get("brightness")
        
        try:
            success = await adb_service.set_brightness(brightness)
            if success:
                _LOGGER.info(f"Brightness set to: {brightness}")
            else:
                _LOGGER.error(f"Failed to set brightness: {brightness}")
                
        except Exception as e:
            _LOGGER.error(f"Set brightness service error: {e}")

    async def set_volume_service(call: ServiceCall) -> None:
        """Service to set volume level."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        volume = call.data.get("volume")
        
        try:
            success = await adb_service.set_volume(volume)
            if success:
                _LOGGER.info(f"Volume set to: {volume}%")
            else:
                _LOGGER.error(f"Failed to set volume: {volume}%")
                
        except Exception as e:
            _LOGGER.error(f"Set volume service error: {e}")

    async def kill_process_service(call: ServiceCall) -> None:
        """Service to kill a process."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        process_id = call.data.get("process_id")
        
        try:
            success = await adb_service.kill_process(process_id)
            if success:
                _LOGGER.info(f"Process killed: {process_id}")
            else:
                _LOGGER.error(f"Failed to kill process: {process_id}")
                
        except Exception as e:
            _LOGGER.error(f"Kill process service error: {e}")

    async def wake_isg_service(call: ServiceCall) -> None:
        """Service to wake up iSG app."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        try:
            success = await adb_service.wake_up_isg()
            if success:
                _LOGGER.info("iSG wake up successful")
            else:
                _LOGGER.error("iSG wake up failed")
                
        except Exception as e:
            _LOGGER.error(f"Wake iSG service error: {e}")

    async def restart_isg_service(call: ServiceCall) -> None:
        """Service to restart iSG app."""
        adb_service = get_adb_service(hass)
        if not adb_service:
            _LOGGER.error("ADB service not available")
            return

        try:
            success = await adb_service.restart_isg()
            if success:
                _LOGGER.info("iSG restart successful")
            else:
                _LOGGER.error("iSG restart failed")
                
        except Exception as e:
            _LOGGER.error(f"Restart iSG service error: {e}")

    # Register services
    hass.services.async_register(
        DOMAIN,
        "take_screenshot",
        take_screenshot_service,
        schema=SERVICE_SCREENSHOT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "launch_app",
        launch_app_service,
        schema=SERVICE_LAUNCH_APP_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "set_brightness",
        set_brightness_service,
        schema=SERVICE_SET_BRIGHTNESS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "set_volume",
        set_volume_service,
        schema=SERVICE_SET_VOLUME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "kill_process",
        kill_process_service,
        schema=SERVICE_KILL_PROCESS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "wake_isg",
        wake_isg_service,
        schema=SERVICE_WAKE_ISG_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "restart_isg",
        restart_isg_service,
        schema=SERVICE_RESTART_ISG_SCHEMA,
    )

    _LOGGER.info("Android TV Box custom services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload custom services."""
    hass.services.async_remove(DOMAIN, "take_screenshot")
    hass.services.async_remove(DOMAIN, "launch_app")
    hass.services.async_remove(DOMAIN, "set_brightness")
    hass.services.async_remove(DOMAIN, "set_volume")
    hass.services.async_remove(DOMAIN, "kill_process")
    hass.services.async_remove(DOMAIN, "wake_isg")
    hass.services.async_remove(DOMAIN, "restart_isg")
    
    _LOGGER.info("Android TV Box custom services unloaded")
