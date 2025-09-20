"""Media Player platform for Android TV Box integration."""
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import asyncio

from .helpers import get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


class AndroidTVBoxCoordinator(DataUpdateCoordinator):
    """Coordinator for Android TV Box data updates."""

    def __init__(self, hass: HomeAssistant, adb_service: ADBService):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Android TV Box",
            update_interval=SCAN_INTERVAL,
        )
        self.adb_service = adb_service

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        # Default data structure
        data = {
            "volume_level": 0.5,
            "is_on": False,
            "current_app": "Unknown",
            "is_volume_muted": False,
            "media_state": "unknown"
        }
        
        try:
            # Get volume level and mute status
            try:
                volume = await self.adb_service.get_volume()
                if volume is not None:
                    data["volume_level"] = volume / 100
                    data["is_volume_muted"] = volume == 0
                else:
                    data["volume_level"] = 0.5
                    data["is_volume_muted"] = False
            except Exception as e:
                _LOGGER.warning(f"Failed to get volume: {e}")
            
            # Check if device is powered on
            try:
                is_on = await self.adb_service.is_powered_on()
                data["is_on"] = is_on
            except Exception as e:
                _LOGGER.warning(f"Failed to get power status: {e}")
            
            # Get current app
            try:
                current_app = await self.adb_service.get_current_app()
                data["current_app"] = current_app if current_app else "Unknown"
            except Exception as e:
                _LOGGER.warning(f"Failed to get current app: {e}")
            
            # Determine media state using media_session when possible
            try:
                playback = await self.adb_service.get_playback_state()
            except Exception:
                playback = None

            if not data["is_on"]:
                data["media_state"] = "off"
            elif playback in ("playing", "paused", "stopped", "idle"):
                data["media_state"] = playback
            elif data["current_app"] and data["current_app"] != "Unknown":
                # Fallback heuristic
                data["media_state"] = "playing"
            else:
                data["media_state"] = "idle"
            
            return data
        except Exception as err:
            _LOGGER.error(f"Error communicating with Android TV Box: {err}")
            return data  # Return default data instead of raising exception


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box media player from a config entry."""
    adb_service = get_adb_service(hass)
    config = get_config(hass)
    
    if not adb_service:
        _LOGGER.error("ADB service not available")
        return

    # Create coordinator
    coordinator = AndroidTVBoxCoordinator(hass, adb_service)
    # Ensure first refresh completes before entity is created
    await coordinator.async_config_entry_first_refresh()
    
    # Create media player entity
    entity = AndroidTVBoxMediaPlayer(coordinator, config)
    async_add_entities([entity])


class AndroidTVBoxMediaPlayer(MediaPlayerEntity):
    """Representation of an Android TV Box media player."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: AndroidTVBoxCoordinator, config: Dict[str, Any]):
        """Initialize the media player."""
        self.coordinator = coordinator
        self.config = config
        self._attr_unique_id = f"android_tv_box_{config.get('host', '127.0.0.1')}_{config.get('port', 5555)}"
        self._attr_device_info = {
            "identifiers": {("android_tv_box", self._attr_unique_id)},
            "name": config.get("name", "Android TV Box"),
            "manufacturer": "LinknLink",
            "model": "TV Box",
        }

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        data = self.coordinator.data or {}
        if not data.get("is_on", False):
            return MediaPlayerState.OFF
        
        # Use the media state from coordinator data
        media_state = data.get("media_state", "unknown")
        if media_state == "off":
            return MediaPlayerState.OFF
        elif media_state == "playing":
            return MediaPlayerState.PLAYING
        elif media_state == "paused":
            return MediaPlayerState.PAUSED
        elif media_state in ("idle", "stopped"):
            return MediaPlayerState.IDLE
        else:
            return MediaPlayerState.STANDBY

    @property
    def volume_level(self) -> Optional[float]:
        """Volume level of the media player (0..1)."""
        data = self.coordinator.data or {}
        return data.get("volume_level")

    @property
    def is_volume_muted(self) -> bool:
        """Boolean if volume is currently muted."""
        data = self.coordinator.data or {}
        return data.get("is_volume_muted", False)

    @property
    def media_title(self) -> Optional[str]:
        """Title of current playing media."""
        data = self.coordinator.data or {}
        current_app = data.get("current_app")
        return current_app if current_app else "Android TV Box"

    @property
    def media_content_type(self) -> Optional[MediaType]:
        """Content type of current playing media."""
        return MediaType.APP

    @property
    def media_content_id(self) -> Optional[str]:
        """Content ID of current playing media."""
        data = self.coordinator.data or {}
        return data.get("current_app")

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self.coordinator.adb_service.power_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self.coordinator.adb_service.power_off()
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        """Send play command."""
        await self.coordinator.adb_service.media_play()
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.coordinator.adb_service.media_pause()
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self.coordinator.adb_service.media_stop()
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.coordinator.adb_service.media_previous()
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.coordinator.adb_service.media_next()
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        volume_percentage = int(volume * 100)
        await self.coordinator.adb_service.set_volume(volume_percentage)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute:
            # Store current volume level before muting
            data = self.coordinator.data or {}
            current_volume = data.get("volume_level", 0.5)
            if current_volume > 0:
                # Store volume level for unmuting
                self._previous_volume = current_volume
            await self.coordinator.adb_service.volume_mute()
        else:
            # Use stored volume level or default to 50%
            restore_volume = getattr(self, '_previous_volume', 0.5) * 100
            await self.coordinator.adb_service.set_volume(int(restore_volume))
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        await self.coordinator.adb_service.volume_up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        await self.coordinator.adb_service.volume_down()
        await self.coordinator.async_request_refresh()

    async def async_play_media(self, media_type: MediaType, media_id: str, **kwargs: Any) -> None:
        """Play a piece of media."""
        if media_type == MediaType.APP:
            # Launch app
            await self.coordinator.adb_service.launch_app(media_id)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("Unsupported media type: %s", media_type)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        self.coordinator.async_remove_listener(self._handle_coordinator_update)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
