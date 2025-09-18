"""Web server for Android TV Box integration management."""
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
import aiohttp_cors

from . import DOMAIN, get_adb_service, get_config
from .adb_service import ADBService

_LOGGER = logging.getLogger(__name__)

class AndroidTVBoxWebServer:
    """Web server for Android TV Box management interface."""

    def __init__(self, hass, port: int = 3003):
        """Initialize web server."""
        self.hass = hass
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        self._config_file = None

    async def start(self) -> bool:
        """Start the web server."""
        try:
            self.app = web.Application()
            
            # Setup CORS
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })

            # Add routes
            self._setup_routes()
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)

            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            _LOGGER.info(f"Android TV Box web server started on port {self.port}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Failed to start web server: {e}")
            return False

    async def stop(self):
        """Stop the web server."""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            _LOGGER.info("Android TV Box web server stopped")
        except Exception as e:
            _LOGGER.error(f"Error stopping web server: {e}")

    def _setup_routes(self):
        """Setup web routes."""
        # Static files
        self.app.router.add_static('/', path=os.path.join(os.path.dirname(__file__), 'web'), name='static')
        
        # API routes
        self.app.router.add_get('/api/config', self._get_config)
        self.app.router.add_post('/api/config', self._update_config)
        self.app.router.add_get('/api/apps', self._get_apps)
        self.app.router.add_post('/api/apps', self._add_app)
        self.app.router.add_put('/api/apps/{app_id}', self._update_app)
        self.app.router.add_delete('/api/apps/{app_id}', self._delete_app)
        self.app.router.add_get('/api/status', self._get_status)
        self.app.router.add_post('/api/test-connection', self._test_connection)
        self.app.router.add_post('/api/test-mqtt', self._test_mqtt)
        self.app.router.add_post('/api/restart-ha', self._restart_ha)

    async def _get_config(self, request: Request) -> Response:
        """Get current configuration."""
        try:
            config = get_config(self.hass)
            return web.json_response({
                "success": True,
                "data": config
            })
        except Exception as e:
            _LOGGER.error(f"Error getting config: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _update_config(self, request: Request) -> Response:
        """Update configuration."""
        try:
            data = await request.json()
            
            # Validate required fields
            required_fields = ['host', 'port', 'name']
            for field in required_fields:
                if field not in data:
                    return web.json_response({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }, status=400)
            
            # Update configuration
            config = get_config(self.hass)
            config.update(data)
            
            # Save to configuration file
            await self._save_config_to_file(config)
            
            return web.json_response({
                "success": True,
                "message": "Configuration updated successfully"
            })
            
        except Exception as e:
            _LOGGER.error(f"Error updating config: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _get_apps(self, request: Request) -> Response:
        """Get configured apps."""
        try:
            config = get_config(self.hass)
            apps = config.get('apps', {})
            visible = config.get('visible', [])
            
            app_list = []
            for name, package in apps.items():
                app_list.append({
                    "id": name,
                    "name": name,
                    "package": package,
                    "visible": name in visible
                })
            
            return web.json_response({
                "success": True,
                "data": app_list
            })
            
        except Exception as e:
            _LOGGER.error(f"Error getting apps: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _add_app(self, request: Request) -> Response:
        """Add new app."""
        try:
            data = await request.json()
            
            if 'name' not in data or 'package' not in data:
                return web.json_response({
                    "success": False,
                    "error": "Missing name or package"
                }, status=400)
            
            config = get_config(self.hass)
            apps = config.get('apps', {})
            visible = config.get('visible', [])
            
            # Add app
            apps[data['name']] = data['package']
            
            # Add to visible if specified
            if data.get('visible', False) and data['name'] not in visible:
                visible.append(data['name'])
            
            config['apps'] = apps
            config['visible'] = visible
            
            # Save configuration
            await self._save_config_to_file(config)
            
            return web.json_response({
                "success": True,
                "message": f"App '{data['name']}' added successfully"
            })
            
        except Exception as e:
            _LOGGER.error(f"Error adding app: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _update_app(self, request: Request) -> Response:
        """Update existing app."""
        try:
            app_id = request.match_info['app_id']
            data = await request.json()
            
            config = get_config(self.hass)
            apps = config.get('apps', {})
            visible = config.get('visible', [])
            
            if app_id not in apps:
                return web.json_response({
                    "success": False,
                    "error": "App not found"
                }, status=404)
            
            # Update app
            if 'name' in data:
                # Rename app
                new_name = data['name']
                package = apps[app_id]
                del apps[app_id]
                apps[new_name] = package
                
                # Update visible list
                if app_id in visible:
                    visible.remove(app_id)
                    if data.get('visible', True):
                        visible.append(new_name)
                
                app_id = new_name
            
            if 'package' in data:
                apps[app_id] = data['package']
            
            # Update visibility
            if 'visible' in data:
                if data['visible'] and app_id not in visible:
                    visible.append(app_id)
                elif not data['visible'] and app_id in visible:
                    visible.remove(app_id)
            
            config['apps'] = apps
            config['visible'] = visible
            
            # Save configuration
            await self._save_config_to_file(config)
            
            return web.json_response({
                "success": True,
                "message": f"App '{app_id}' updated successfully"
            })
            
        except Exception as e:
            _LOGGER.error(f"Error updating app: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _delete_app(self, request: Request) -> Response:
        """Delete app."""
        try:
            app_id = request.match_info['app_id']
            
            config = get_config(self.hass)
            apps = config.get('apps', {})
            visible = config.get('visible', [])
            
            if app_id not in apps:
                return web.json_response({
                    "success": False,
                    "error": "App not found"
                }, status=404)
            
            # Remove app
            del apps[app_id]
            if app_id in visible:
                visible.remove(app_id)
            
            config['apps'] = apps
            config['visible'] = visible
            
            # Save configuration
            await self._save_config_to_file(config)
            
            return web.json_response({
                "success": True,
                "message": f"App '{app_id}' deleted successfully"
            })
            
        except Exception as e:
            _LOGGER.error(f"Error deleting app: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _get_status(self, request: Request) -> Response:
        """Get system status."""
        try:
            adb_service = get_adb_service(self.hass)
            config = get_config(self.hass)
            
            status = {
                "adb_connected": False,
                "device_powered_on": False,
                "wifi_enabled": False,
                "current_app": None,
                "isg_running": False,
                "timestamp": datetime.now().isoformat()
            }
            
            if adb_service:
                try:
                    status["adb_connected"] = await adb_service.is_connected()
                    if status["adb_connected"]:
                        status["device_powered_on"] = await adb_service.is_powered_on()
                        status["wifi_enabled"] = await adb_service.is_wifi_on()
                        status["current_app"] = await adb_service.get_current_app()
                        status["isg_running"] = await adb_service.is_isg_running()
                except Exception as e:
                    _LOGGER.warning(f"Error getting status: {e}")
            
            return web.json_response({
                "success": True,
                "data": status
            })
            
        except Exception as e:
            _LOGGER.error(f"Error getting status: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _test_connection(self, request: Request) -> Response:
        """Test ADB connection."""
        try:
            data = await request.json()
            host = data.get('host', '127.0.0.1')
            port = data.get('port', 5555)
            
            # Create temporary ADB service for testing
            test_adb = ADBService(host, port)
            connected = await test_adb.connect()
            
            if connected:
                await test_adb.disconnect()
                return web.json_response({
                    "success": True,
                    "message": "Connection successful"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": "Connection failed"
                })
                
        except Exception as e:
            _LOGGER.error(f"Error testing connection: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _test_mqtt(self, request: Request) -> Response:
        """Test MQTT connection."""
        try:
            data = await request.json()
            broker = data.get('broker', 'localhost')
            port = data.get('port', 1883)
            username = data.get('username')
            password = data.get('password')
            
            # Test MQTT connection
            import paho.mqtt.client as mqtt
            import socket
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.disconnect()
                    return True
                return False
            
            client = mqtt.Client()
            if username and password:
                client.username_pw_set(username, password)
            
            client.on_connect = on_connect
            
            try:
                client.connect(broker, port, 5)
                client.loop_start()
                await asyncio.sleep(2)
                client.loop_stop()
                
                return web.json_response({
                    "success": True,
                    "message": "MQTT connection successful"
                })
            except Exception as e:
                return web.json_response({
                    "success": False,
                    "error": f"MQTT connection failed: {str(e)}"
                })
                
        except Exception as e:
            _LOGGER.error(f"Error testing MQTT: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _restart_ha(self, request: Request) -> Response:
        """Restart Home Assistant."""
        try:
            # Schedule restart
            self.hass.async_create_task(self._restart_home_assistant())
            
            return web.json_response({
                "success": True,
                "message": "Home Assistant restart scheduled"
            })
            
        except Exception as e:
            _LOGGER.error(f"Error restarting HA: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _restart_home_assistant(self):
        """Restart Home Assistant."""
        await asyncio.sleep(2)  # Give time for response
        self.hass.async_create_task(self.hass.async_stop())

    async def _save_config_to_file(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            config_dir = self.hass.config.config_dir
            config_file = os.path.join(config_dir, 'android_tv_box_config.json')
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            _LOGGER.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            _LOGGER.error(f"Error saving config: {e}")
            raise
