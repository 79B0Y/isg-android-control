"""Configuration schema for Android TV Box integration."""
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.helpers import config_validation as cv

DOMAIN = "android_tv_box"

# Default configuration values
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5555
DEFAULT_NAME = "Android TV Box"
DEFAULT_SCREENSHOT_PATH = "/sdcard/isgbackup/screenshot/"
DEFAULT_SCREENSHOT_KEEP_COUNT = 3
DEFAULT_SCREENSHOT_INTERVAL = 3
DEFAULT_PERFORMANCE_CHECK_INTERVAL = 500
DEFAULT_CPU_THRESHOLD = 50
DEFAULT_TERMUX_MODE = True
DEFAULT_UBUNTU_VENV_PATH = "~/uiauto_env"
DEFAULT_ADB_PATH = "/usr/bin/adb"

# Default apps configuration
DEFAULT_APPS = {
    "Home Assistant": "io.homeassistant.companion.android",
    "YouTube": "com.google.android.youtube",
    "Spotify": "com.spotify.music",
    "iSG": "com.linknlink.app.device.isg",
}

DEFAULT_VISIBLE_APPS = ["Home Assistant", "YouTube", "Spotify", "iSG"]

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional("screenshot_path", default=DEFAULT_SCREENSHOT_PATH): cv.string,
                vol.Optional("screenshot_keep_count", default=DEFAULT_SCREENSHOT_KEEP_COUNT): cv.positive_int,
                vol.Optional("screenshot_interval", default=DEFAULT_SCREENSHOT_INTERVAL): cv.positive_int,
                vol.Optional("performance_check_interval", default=DEFAULT_PERFORMANCE_CHECK_INTERVAL): cv.positive_int,
                vol.Optional("cpu_threshold", default=DEFAULT_CPU_THRESHOLD): cv.positive_int,
                vol.Optional("termux_mode", default=DEFAULT_TERMUX_MODE): cv.boolean,
                vol.Optional("ubuntu_venv_path", default=DEFAULT_UBUNTU_VENV_PATH): cv.string,
                vol.Optional("adb_path", default=DEFAULT_ADB_PATH): cv.string,
                vol.Optional("apps", default=DEFAULT_APPS): vol.Schema({
                    cv.string: cv.string,  # app_name: package_name
                }),
                vol.Optional("visible", default=DEFAULT_VISIBLE_APPS): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional("isg_monitoring", default=True): cv.boolean,
                vol.Optional("isg_check_interval", default=30): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Entity configuration
ENTITY_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("media_player", default=True): cv.boolean,
        vol.Optional("switch", default=True): cv.boolean,
        vol.Optional("camera", default=True): cv.boolean,
        vol.Optional("sensor", default=True): cv.boolean,
        vol.Optional("remote", default=True): cv.boolean,
    }
)

# Service schemas
SERVICE_SCREENSHOT_SCHEMA = vol.Schema(
    {
        vol.Optional("filename"): cv.string,
        vol.Optional("keep_count", default=DEFAULT_SCREENSHOT_KEEP_COUNT): cv.positive_int,
    }
)

SERVICE_LAUNCH_APP_SCHEMA = vol.Schema(
    {
        vol.Required("package_name"): cv.string,
        vol.Optional("activity_name"): cv.string,
    }
)

SERVICE_SET_BRIGHTNESS_SCHEMA = vol.Schema(
    {
        vol.Required("brightness"): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    }
)

SERVICE_SET_VOLUME_SCHEMA = vol.Schema(
    {
        vol.Required("volume"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SERVICE_KILL_PROCESS_SCHEMA = vol.Schema(
    {
        vol.Required("process_id"): cv.positive_int,
    }
)

SERVICE_WAKE_ISG_SCHEMA = vol.Schema({})

SERVICE_RESTART_ISG_SCHEMA = vol.Schema({})
