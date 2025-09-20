"""Config flow for Android TV Box integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .adb_service import ADBService
from .config import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="127.0.0.1"): str,
        vol.Required("port", default=5555): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        vol.Required("name", default="Android TV Box"): str,
        vol.Optional("adb_path", default="/usr/bin/adb"): str,
    }
)


class AndroidTVBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Android TV Box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            data: Dict[str, Any] = dict(user_input)
            legacy_name = data.pop("device_name", None)
            if not data.get("name"):
                data["name"] = legacy_name or "Android TV Box"

            # Check for existing entries
            await self.async_set_unique_id(f"{data['host']}:{data['port']}")
            self._abort_if_unique_id_configured()

            # Test ADB connection
            try:
                adb_service = ADBService(
                    host=data["host"],
                    port=data["port"],
                    adb_path=data.get("adb_path", "/usr/bin/adb")
                )

                connected = await adb_service.connect()
                if connected:
                    await adb_service.disconnect()
                    return self.async_create_entry(
                        title=data["name"],
                        data=data,
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception as exc:
                _LOGGER.error("Error testing ADB connection: %s", exc)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)