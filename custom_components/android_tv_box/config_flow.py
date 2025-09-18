"""Config flow for Android TV Box integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .adb_service import ADBService, ADBConnectionError
from .config import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="127.0.0.1"): str,
        vol.Required("port", default=5555): vol.Coerce(int),
        vol.Required("name", default="Android TV Box"): str,
        vol.Optional("adb_path", default="/usr/bin/adb"): str,
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("screenshot_path", default="/sdcard/isgbackup/screenshot/"): str,
        vol.Optional("screenshot_keep_count", default=3): vol.Coerce(int),
        vol.Optional("screenshot_interval", default=3): vol.Coerce(int),
        vol.Optional("performance_check_interval", default=500): vol.Coerce(int),
        vol.Optional("cpu_threshold", default=50): vol.Coerce(int),
        vol.Optional("termux_mode", default=True): bool,
        vol.Optional("ubuntu_venv_path", default="~/uiauto_env"): str,
        vol.Optional("media_player", default=True): bool,
        vol.Optional("switch", default=True): bool,
        vol.Optional("camera", default=True): bool,
        vol.Optional("sensor", default=True): bool,
        vol.Optional("remote", default=True): bool,
        vol.Optional("select", default=True): bool,
        vol.Optional("binary_sensor", default=True): bool,
        vol.Optional("isg_monitoring", default=True): bool,
        vol.Optional("isg_check_interval", default=30): vol.Coerce(int),
    }
)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Android TV Box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Test connection (optional - don't fail if ADB is not available)
                try:
                    adb_service = ADBService(
                        host=user_input["host"],
                        port=user_input["port"],
                        adb_path=user_input["adb_path"]
                    )
                    
                    if await adb_service.connect():
                        await adb_service.disconnect()
                        _LOGGER.info("ADB connection test successful")
                    else:
                        _LOGGER.warning("ADB connection test failed, but continuing with setup")
                        
                except Exception as e:
                    _LOGGER.warning(f"ADB connection test failed: {e}, but continuing with setup")
                
                # Create entry regardless of ADB connection test
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                )
                    
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)

    async def async_step_options(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Update options
            return self.async_create_entry(
                title=self.config_entry.title,
                data={**self.config_entry.data, **user_input},
            )

        # Get current options
        options = self.config_entry.options or {}
        
        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "screenshot_path",
                        default=options.get("screenshot_path", "/sdcard/isgbackup/screenshot/")
                    ): str,
                    vol.Optional(
                        "screenshot_keep_count",
                        default=options.get("screenshot_keep_count", 3)
                    ): vol.Coerce(int),
                    vol.Optional(
                        "screenshot_interval",
                        default=options.get("screenshot_interval", 3)
                    ): vol.Coerce(int),
                    vol.Optional(
                        "performance_check_interval",
                        default=options.get("performance_check_interval", 500)
                    ): vol.Coerce(int),
                    vol.Optional(
                        "cpu_threshold",
                        default=options.get("cpu_threshold", 50)
                    ): vol.Coerce(int),
                    vol.Optional(
                        "termux_mode",
                        default=options.get("termux_mode", True)
                    ): bool,
                    vol.Optional(
                        "ubuntu_venv_path",
                        default=options.get("ubuntu_venv_path", "~/uiauto_env")
                    ): str,
                    vol.Optional(
                        "media_player",
                        default=options.get("media_player", True)
                    ): bool,
                    vol.Optional(
                        "switch",
                        default=options.get("switch", True)
                    ): bool,
                    vol.Optional(
                        "camera",
                        default=options.get("camera", True)
                    ): bool,
                    vol.Optional(
                        "sensor",
                        default=options.get("sensor", True)
                    ): bool,
                    vol.Optional(
                        "remote",
                        default=options.get("remote", True)
                    ): bool,
                }
            ),
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Android TV Box."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_OPTIONS_DATA_SCHEMA,
        )
