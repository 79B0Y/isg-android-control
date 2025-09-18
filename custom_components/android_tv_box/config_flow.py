"""Config flow for Android TV Box integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="127.0.0.1"): str,
        vol.Required("port", default=5555): vol.Coerce(int),
        vol.Required("name", default="Android TV Box"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain="android_tv_box"):
    """Handle a config flow for Android TV Box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Create entry without testing connection
            return self.async_create_entry(
                title=user_input["name"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)