"""Android TV Box integration for Home Assistant."""
import asyncio
import logging
from typing import Any, Dict, Optional

from adb_shell import exceptions as adb_exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .adb_service import ADBConnectionError, ADBKeyError, ADBService
from .config import DOMAIN

_LOGGER = logging.getLogger(__name__)

BASE_ADB_ERROR = getattr(
    adb_exceptions,
    "AdbError",
    getattr(adb_exceptions, "AdbException", Exception),
)
AdbAuthError = getattr(
    adb_exceptions,
    "AdbAuthError",
    getattr(adb_exceptions, "AuthenticationError", BASE_ADB_ERROR),
)

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.CAMERA,
    Platform.SENSOR,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Android TV Box component from configuration.yaml."""
    # Store YAML config for web interface access
    if DOMAIN in config:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]
        
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
    adb_service = ADBService(host=host, port=port)

    # Test connection
    last_error: Optional[str] = None
    try:
        connected = await adb_service.connect()
    except (ADBKeyError, ADBConnectionError, AdbAuthError) as err:
        connected = False
        last_error = str(err)

    if not connected:
        if last_error:
            _LOGGER.warning(
                "Failed to connect to Android device at %s:%s: %s", host, port, last_error
            )
        else:
            _LOGGER.warning("Failed to connect to Android device at %s:%s", host, port)

    # Store ADB service
    hass.data[DOMAIN]["adb_service"] = adb_service

    # Start web server
    from .web_server import AndroidTVBoxWebServer
    web_server = AndroidTVBoxWebServer(hass, port=3003)
    started = await web_server.start()
    if started:
        _LOGGER.info("Android TV Box web server started on port 3003")
        hass.data[DOMAIN]["web_server"] = web_server
    else:
        _LOGGER.warning("Failed to start Android TV Box web server")

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start background WiFi connectivity monitor and recovery
    async def _wifi_monitor():
        from .helpers import get_adb_service
        adb = get_adb_service(hass)
        if not adb:
            return
        consecutive_down = 0
        while True:
            try:
                # Consider WiFi down if disabled or SSID/IP unknown
                wifi_on = await adb.is_wifi_on()
                wifi_info = await adb.get_wifi_info()
                ssid = (wifi_info or {}).get("ssid")
                ip = (wifi_info or {}).get("ip_address")
                wifi_connected = bool(wifi_on and ssid and ssid != "Unknown" and ip and ip != "Unknown")
                if wifi_connected:
                    consecutive_down = 0
                else:
                    consecutive_down += 1
                    # 60s window with 15s checks => 4 consecutive misses
                    if consecutive_down >= 4:
                        _LOGGER.warning("WiFi appears down for ~60s. Attempting recovery: enable WiFi, then reboot if needed.")
                        # First try enabling WiFi explicitly
                        try:
                            await adb.wifi_on()
                            await adb.shell_command("svc wifi enable")
                        except Exception:
                            pass
                        await asyncio.sleep(10)
                        # Re-check; if still down, reboot device
                        try:
                            wifi_on2 = await adb.is_wifi_on()
                            info2 = await adb.get_wifi_info()
                            if not (wifi_on2 and (info2.get("ssid") not in (None, "Unknown"))):
                                _LOGGER.warning("WiFi recovery failed, rebooting Android device...")
                                await adb.reboot_device()
                                # Give device time to reboot and ADB to come back
                                await asyncio.sleep(30)
                                await adb.connect()
                                # Ensure WiFi is enabled after reboot
                                await adb.wifi_on()
                        except Exception as e:
                            _LOGGER.error(f"WiFi recovery error: {e}")
                        finally:
                            consecutive_down = 0
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.debug(f"WiFi monitor iteration error: {e}")
                await asyncio.sleep(15)

    wifi_task = hass.loop.create_task(_wifi_monitor())
    hass.data[DOMAIN].setdefault("tasks", []).append(wifi_task)

    _LOGGER.info("Android TV Box config entry loaded successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Cancel background tasks
        for task in hass.data.get(DOMAIN, {}).get("tasks", []):
            try:
                task.cancel()
            except Exception:
                pass
        hass.data[DOMAIN].pop("tasks", None)
        # Stop web server
        if DOMAIN in hass.data and "web_server" in hass.data[DOMAIN]:
            web_server = hass.data[DOMAIN]["web_server"]
            await web_server.stop()
            _LOGGER.info("Android TV Box web server stopped")

        # Disconnect ADB service
        if DOMAIN in hass.data and "adb_service" in hass.data[DOMAIN]:
            adb_service = hass.data[DOMAIN]["adb_service"]
            await adb_service.disconnect()

        # Clean up data
        hass.data[DOMAIN].pop("config", None)
        hass.data[DOMAIN].pop("adb_service", None)
        hass.data[DOMAIN].pop("web_server", None)

    return unload_ok
