from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .ha import HAIntegration
from ..services.cec_controller import CECController

logger = logging.getLogger(__name__)


class CECHAIntegration:
    """
    Home Assistant CEC integration for Android TV device control.

    Creates HA entities for TV control via CEC, integrating with existing
    Android TV device in Home Assistant.
    """

    def __init__(self, ha: HAIntegration, cec: CECController):
        self.ha = ha
        self.cec = cec
        self.base_topic = f"{ha.settings.mqtt.base_topic}/cec"

        # Entity configurations for HA auto-discovery
        self.entities = {
            # Media Player for TV
            'tv': {
                'component': 'media_player',
                'name': 'Android TV CEC',
                'unique_id': 'isg_android_tv_cec',
                'device_class': 'tv',
                'features': [
                    'turn_on', 'turn_off', 'volume_up', 'volume_down',
                    'volume_mute', 'select_source'
                ]
            },

            # Individual button controls
            'power': {
                'component': 'button',
                'name': 'TV Power Toggle',
                'unique_id': 'isg_tv_power_toggle',
                'icon': 'mdi:power'
            },
            'volume_up': {
                'component': 'button',
                'name': 'TV Volume Up',
                'unique_id': 'isg_tv_volume_up',
                'icon': 'mdi:volume-plus'
            },
            'volume_down': {
                'component': 'button',
                'name': 'TV Volume Down',
                'unique_id': 'isg_tv_volume_down',
                'icon': 'mdi:volume-minus'
            },
            'mute': {
                'component': 'button',
                'name': 'TV Mute',
                'unique_id': 'isg_tv_mute',
                'icon': 'mdi:volume-mute'
            },

            # Navigation controls
            'nav_up': {
                'component': 'button',
                'name': 'TV Navigate Up',
                'unique_id': 'isg_tv_nav_up',
                'icon': 'mdi:arrow-up'
            },
            'nav_down': {
                'component': 'button',
                'name': 'TV Navigate Down',
                'unique_id': 'isg_tv_nav_down',
                'icon': 'mdi:arrow-down'
            },
            'nav_left': {
                'component': 'button',
                'name': 'TV Navigate Left',
                'unique_id': 'isg_tv_nav_left',
                'icon': 'mdi:arrow-left'
            },
            'nav_right': {
                'component': 'button',
                'name': 'TV Navigate Right',
                'unique_id': 'isg_tv_nav_right',
                'icon': 'mdi:arrow-right'
            },
            'select': {
                'component': 'button',
                'name': 'TV Select/OK',
                'unique_id': 'isg_tv_select',
                'icon': 'mdi:check-circle'
            },
            'back': {
                'component': 'button',
                'name': 'TV Back',
                'unique_id': 'isg_tv_back',
                'icon': 'mdi:arrow-left-circle'
            },
            'home': {
                'component': 'button',
                'name': 'TV Home',
                'unique_id': 'isg_tv_home',
                'icon': 'mdi:home'
            },
            'menu': {
                'component': 'button',
                'name': 'TV Menu',
                'unique_id': 'isg_tv_menu',
                'icon': 'mdi:menu'
            },

            # Input selection
            'input_hdmi1': {
                'component': 'button',
                'name': 'TV HDMI 1',
                'unique_id': 'isg_tv_hdmi1',
                'icon': 'mdi:video-input-hdmi'
            },
            'input_hdmi2': {
                'component': 'button',
                'name': 'TV HDMI 2',
                'unique_id': 'isg_tv_hdmi2',
                'icon': 'mdi:video-input-hdmi'
            },
            'input_hdmi3': {
                'component': 'button',
                'name': 'TV HDMI 3',
                'unique_id': 'isg_tv_hdmi3',
                'icon': 'mdi:video-input-hdmi'
            },
            'input_hdmi4': {
                'component': 'button',
                'name': 'TV HDMI 4',
                'unique_id': 'isg_tv_hdmi4',
                'icon': 'mdi:video-input-hdmi'
            },

            # Status sensors
            'tv_status': {
                'component': 'sensor',
                'name': 'TV CEC Status',
                'unique_id': 'isg_tv_cec_status',
                'icon': 'mdi:television'
            },
            'cec_devices': {
                'component': 'sensor',
                'name': 'CEC Devices Count',
                'unique_id': 'isg_cec_devices_count',
                'icon': 'mdi:counter'
            }
        }

        # Command mapping for MQTT subscriptions
        self.command_mapping = {
            'power_toggle': 'power_toggle',
            'power_on': 'power_on',
            'power_off': 'power_off',
            'volume_up': 'volume_up',
            'volume_down': 'volume_down',
            'mute': 'mute',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'select': 'select',
            'back': 'back',
            'home': 'home',
            'menu': 'menu',
            'hdmi1': 'input_hdmi1',
            'hdmi2': 'input_hdmi2',
            'hdmi3': 'input_hdmi3',
            'hdmi4': 'input_hdmi4',
        }

    async def publish_discovery(self) -> None:
        """Publish CEC device discovery to Home Assistant."""
        if not self.ha.client:
            logger.warning("MQTT client not available for CEC discovery")
            return

        try:
            # Get device info for HA integration
            device_info = self._get_device_info()

            # Publish each entity
            for entity_id, entity_config in self.entities.items():
                await self._publish_entity_discovery(entity_id, entity_config, device_info)

            logger.info("Published CEC discovery configuration to Home Assistant")

        except Exception as e:
            logger.error("Error publishing CEC discovery: %s", e)

    async def _publish_entity_discovery(
        self,
        entity_id: str,
        entity_config: Dict[str, Any],
        device_info: Dict[str, Any]
    ) -> None:
        """Publish discovery configuration for a single entity."""
        component = entity_config['component']
        name = entity_config['name']
        unique_id = entity_config['unique_id']

        # Base discovery topic
        discovery_topic = f"homeassistant/{component}/{unique_id}/config"

        # Base configuration
        config = {
            'name': name,
            'unique_id': unique_id,
            'device': device_info,
            'availability_topic': f"{self.base_topic}/availability",
            'payload_available': 'online',
            'payload_not_available': 'offline'
        }

        # Add icon if specified
        if 'icon' in entity_config:
            config['icon'] = entity_config['icon']

        # Component-specific configuration
        if component == 'media_player':
            config.update({
                'state_topic': f"{self.base_topic}/tv/state",
                'command_topic': f"{self.base_topic}/tv/command",
                'supported_features': self._get_media_player_features(),
                'source_list': ['HDMI 1', 'HDMI 2', 'HDMI 3', 'HDMI 4'],
                'select_source_command_topic': f"{self.base_topic}/tv/select_source"
            })

        elif component == 'button':
            config.update({
                'command_topic': f"{self.base_topic}/button/{entity_id}",
                'payload_press': entity_id
            })

        elif component == 'sensor':
            config.update({
                'state_topic': f"{self.base_topic}/sensor/{entity_id}",
                'value_template': '{{ value_json.state if value_json else value }}'
            })

        # Publish discovery configuration
        await asyncio.to_thread(
            self.ha.client.publish,
            discovery_topic,
            json.dumps(config),
            retain=True
        )

        logger.debug("Published discovery for %s: %s", component, name)

    def _get_device_info(self) -> Dict[str, Any]:
        """Get device information for HA integration."""
        return {
            'identifiers': ['isg_android_tv_cec'],
            'name': 'Android TV (CEC)',
            'model': 'CEC Controller',
            'manufacturer': 'ISG',
            'sw_version': '1.0.0',
            'via_device': 'isg_android_controller',  # Link to main Android device
            'suggested_area': 'Living Room'
        }

    def _get_media_player_features(self) -> List[str]:
        """Get supported media player features."""
        return [
            'turn_on',
            'turn_off',
            'volume_up',
            'volume_down',
            'volume_mute',
            'select_source'
        ]

    async def setup_subscriptions(self) -> None:
        """Setup MQTT subscriptions for CEC commands."""
        if not self.ha.client:
            logger.warning("MQTT client not available for CEC subscriptions")
            return

        try:
            # Subscribe to TV media player commands
            tv_command_topic = f"{self.base_topic}/tv/command"
            self.ha.client.message_callback_add(tv_command_topic, self._handle_tv_command)
            await asyncio.to_thread(self.ha.client.subscribe, tv_command_topic)

            # Subscribe to TV source selection
            source_topic = f"{self.base_topic}/tv/select_source"
            self.ha.client.message_callback_add(source_topic, self._handle_source_selection)
            await asyncio.to_thread(self.ha.client.subscribe, source_topic)

            # Subscribe to individual button commands
            button_topic = f"{self.base_topic}/button/+"
            self.ha.client.message_callback_add(button_topic, self._handle_button_command)
            await asyncio.to_thread(self.ha.client.subscribe, button_topic)

            logger.info("Setup CEC MQTT subscriptions")

        except Exception as e:
            logger.error("Error setting up CEC subscriptions: %s", e)

    def _handle_tv_command(self, client, userdata, message):
        """Handle TV media player commands."""
        try:
            command = message.payload.decode('utf-8').lower()
            logger.info("Received TV command: %s", command)

            # Map media player commands to CEC commands
            cec_command = None
            if command == 'turn_on':
                cec_command = 'power_on'
            elif command == 'turn_off':
                cec_command = 'power_off'
            elif command == 'volume_up':
                cec_command = 'volume_up'
            elif command == 'volume_down':
                cec_command = 'volume_down'
            elif command == 'volume_mute':
                cec_command = 'mute'

            if cec_command:
                # Schedule CEC command execution
                asyncio.create_task(self._execute_cec_command(cec_command))

        except Exception as e:
            logger.error("Error handling TV command: %s", e)

    def _handle_source_selection(self, client, userdata, message):
        """Handle TV source selection commands."""
        try:
            source = message.payload.decode('utf-8')
            logger.info("Received source selection: %s", source)

            # Map source names to CEC commands
            source_mapping = {
                'HDMI 1': 'input_hdmi1',
                'HDMI 2': 'input_hdmi2',
                'HDMI 3': 'input_hdmi3',
                'HDMI 4': 'input_hdmi4'
            }

            cec_command = source_mapping.get(source)
            if cec_command:
                asyncio.create_task(self._execute_cec_command(cec_command))

        except Exception as e:
            logger.error("Error handling source selection: %s", e)

    def _handle_button_command(self, client, userdata, message):
        """Handle individual button commands."""
        try:
            # Extract button name from topic
            topic_parts = message.topic.split('/')
            button_name = topic_parts[-1]

            command_payload = message.payload.decode('utf-8')
            logger.info("Received button command: %s -> %s", button_name, command_payload)

            # Map button to CEC command
            cec_command = self.command_mapping.get(button_name)
            if not cec_command:
                # Try direct mapping if button name matches CEC command
                if button_name in CECController.CEC_COMMANDS:
                    cec_command = button_name

            if cec_command:
                asyncio.create_task(self._execute_cec_command(cec_command))
            else:
                logger.warning("Unknown button command: %s", button_name)

        except Exception as e:
            logger.error("Error handling button command: %s", e)

    async def _execute_cec_command(self, command: str) -> None:
        """Execute a CEC command and update HA state."""
        try:
            success = await self.cec.send_command(command)

            if success:
                logger.info("Successfully executed CEC command: %s", command)
                # Update HA state if needed
                await self.publish_state_update(command)
            else:
                logger.warning("Failed to execute CEC command: %s", command)

        except Exception as e:
            logger.error("Error executing CEC command %s: %s", command, e)

    async def publish_state_update(self, last_command: Optional[str] = None) -> None:
        """Publish current TV/CEC state to Home Assistant."""
        if not self.ha.client:
            return

        try:
            # Get current TV status
            tv_status = await self.cec.get_tv_status()

            # Publish TV media player state
            tv_state = {
                'state': 'on' if tv_status.get('tv_found') else 'off',
                'source': 'Unknown',
                'volume_level': 0.5,  # CEC doesn't provide exact volume
                'is_volume_muted': False,
                'media_title': 'TV',
                'last_command': last_command,
                'updated': datetime.now().isoformat()
            }

            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/tv/state",
                json.dumps(tv_state),
                retain=True
            )

            # Publish CEC status sensor
            cec_status = {
                'state': 'connected' if tv_status['connected'] else 'disconnected',
                'attributes': {
                    'tv_found': tv_status.get('tv_found', False),
                    'tv_name': tv_status.get('tv_name', 'Unknown'),
                    'devices_count': tv_status.get('devices_count', 0),
                    'queue_size': tv_status.get('queue_size', 0),
                    'last_command': tv_status.get('last_command')
                }
            }

            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/sensor/tv_status",
                json.dumps(cec_status),
                retain=True
            )

            # Publish devices count sensor
            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/sensor/cec_devices",
                str(tv_status.get('devices_count', 0)),
                retain=True
            )

            # Publish availability
            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/availability",
                'online' if tv_status['connected'] else 'offline',
                retain=True
            )

        except Exception as e:
            logger.error("Error publishing CEC state: %s", e)

    async def publish_device_scan(self) -> None:
        """Publish detected CEC devices information."""
        if not self.ha.client:
            return

        try:
            devices = await self.cec.scan_devices()

            device_info = {
                'devices': [
                    {
                        'address': dev.address,
                        'name': dev.name,
                        'vendor': dev.vendor,
                        'type': dev.device_type,
                        'power': dev.power_status,
                        'active': dev.active_source
                    }
                    for dev in devices
                ],
                'count': len(devices),
                'scan_time': datetime.now().isoformat()
            }

            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/devices",
                json.dumps(device_info),
                retain=True
            )

            logger.info("Published CEC device scan results: %d devices", len(devices))

        except Exception as e:
            logger.error("Error publishing device scan: %s", e)

    async def cleanup(self) -> None:
        """Clean up CEC HA integration."""
        if not self.ha.client:
            return

        try:
            # Publish offline status
            await asyncio.to_thread(
                self.ha.client.publish,
                f"{self.base_topic}/availability",
                'offline',
                retain=True
            )

            logger.info("CEC HA integration cleaned up")

        except Exception as e:
            logger.error("Error cleaning up CEC HA integration: %s", e)