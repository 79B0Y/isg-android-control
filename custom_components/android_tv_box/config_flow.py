"""Config flow for Android TV Box integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from adb_shell.exceptions import AdbAuthError, AdbConnectionError, AdbTimeoutError
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .adb_service import ADBConnectionError as IntegrationADBConnectionError
from .adb_service import ADBKeyError, ADBService
from .config import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="127.0.0.1"): str,
        vol.Required("port", default=5555): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        vol.Required("name", default="Android TV Box"): str,
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
            # Check for existing entries
            await self.async_set_unique_id(f"{user_input['host']}:{user_input['port']}")
            self._abort_if_unique_id_configured()

            # Test ADB connection
            adb_service = ADBService(
                host=user_input["host"],
                port=user_input["port"],
            )

            try:
                await adb_service.connect()
            except ADBKeyError as err:
                _LOGGER.error("Unable to prepare ADB keys: %s", err)
                errors["base"] = "adb_not_found"
            except AdbAuthError as err:
                _LOGGER.error("ADB authentication failed: %s", err)
                errors["base"] = "adb_auth_failed"
            except (AdbConnectionError, AdbTimeoutError, IntegrationADBConnectionError, OSError) as err:
                _LOGGER.error("Unable to connect to Android device: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as exc:  # pragma: no cover - defensive logging
                _LOGGER.error("Unexpected error testing ADB connection: %s", exc)
                errors["base"] = "unknown"
            else:
                entry_data = {
                    "host": user_input["host"],
                    "port": user_input["port"],
                    "name": user_input["name"],
                }
                return self.async_create_entry(
                    title=user_input["name"],
                    data=entry_data,
                )
            finally:
                await adb_service.disconnect()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)