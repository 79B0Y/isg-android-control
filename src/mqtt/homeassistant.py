"""
Home Assistant MQTT自动发现集成
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from loguru import logger

from src.mqtt.client import get_mqtt_client
from src.core.config import get_settings
from src.core.device_controller import get_device_controller
from src.services.screenshot_service import get_screenshot_service
from src.models.requests import NavigationDirection, VolumeStream


class HomeAssistantMQTT:
    """Home Assistant MQTT自动发现集成类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.mqtt_config = self.settings.mqtt
        self.mqtt_client = get_mqtt_client()
        
        self.device_controller = get_device_controller()
        self.screenshot_service = get_screenshot_service()
        
        # 设备信息
        self.device_id = self.mqtt_config.device_id
        self.base_topic = self.mqtt_config.base_topic
        
        # 实体配置
        self.entities = {}
        
        logger.info("Home Assistant MQTT integration initialized")
    
    async def setup(self):
        """设置Home Assistant集成"""
        try:
            # 等待MQTT连接
            if not self.mqtt_client.is_connected:
                await self.mqtt_client.connect()
            
            if not self.mqtt_client.is_connected:
                logger.error("Cannot setup Home Assistant integration: MQTT not connected")
                return False
            
            # 设置自动发现实体
            await self._setup_entities()
            
            # 订阅命令主题
            await self._setup_command_subscriptions()
            
            # 发布初始状态
            await self._publish_initial_states()
            
            # 启动状态更新任务
            asyncio.create_task(self._state_update_loop())
            
            logger.info("Home Assistant MQTT integration setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Home Assistant setup error: {e}")
            return False
    
    async def _setup_entities(self):
        """设置自动发现实体"""
        
        # 截图摄像头实体
        await self._setup_camera_entity()
        
        # 截图按钮实体
        await self._setup_screenshot_button()
        
        # 导航按钮实体
        await self._setup_navigation_buttons()
        
        # 音量控制实体
        await self._setup_volume_controls()
        
        # 亮度控制实体
        await self._setup_brightness_control()
        
        # 屏幕开关实体
        await self._setup_screen_switch()
        
        # 系统传感器实体
        await self._setup_system_sensors()
        
        # 应用快捷方式
        await self._setup_app_shortcuts()
    
    async def _setup_camera_entity(self):
        """设置截图摄像头实体"""
        entity_id = f"{self.device_id}_screenshot"
        
        config = {
            "name": "Android Screenshot",
            "unique_id": entity_id,
            "topic": f"isg/{self.device_id}/android/screenshot/image",
            "device": self._get_device_info(),
            "availability": {
                "topic": f"isg/{self.device_id}/android/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        discovery_topic = f"{self.base_topic}/camera/{entity_id}/config"
        await self.mqtt_client.publish(discovery_topic, config, retain=True)
        
        self.entities["camera_screenshot"] = {
            "config_topic": discovery_topic,
            "state_topic": config["topic"],
            "entity_id": entity_id
        }
        
        logger.info(f"Setup camera entity: {entity_id}")
    
    async def _setup_screenshot_button(self):
        """设置截图按钮实体"""
        entity_id = f"{self.device_id}_take_screenshot"
        
        config = {
            "name": "Take Screenshot",
            "unique_id": entity_id,
            "command_topic": f"isg/{self.device_id}/android/screenshot/take",
            "device": self._get_device_info(),
            "availability": {
                "topic": f"isg/{self.device_id}/android/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        discovery_topic = f"{self.base_topic}/button/{entity_id}/config"
        await self.mqtt_client.publish(discovery_topic, config, retain=True)
        
        self.entities["button_screenshot"] = {
            "config_topic": discovery_topic,
            "command_topic": config["command_topic"],
            "entity_id": entity_id
        }
        
        logger.info(f"Setup button entity: {entity_id}")
    
    async def _setup_navigation_buttons(self):
        """设置导航按钮实体"""
        directions = {
            "up": "Up",
            "down": "Down", 
            "left": "Left",
            "right": "Right",
            "center": "OK",
            "back": "Back",
            "home": "Home",
            "menu": "Menu"
        }
        
        for direction, name in directions.items():
            entity_id = f"{self.device_id}_nav_{direction}"
            
            config = {
                "name": f"Navigation {name}",
                "unique_id": entity_id,
                "command_topic": f"isg/{self.device_id}/android/navigation/{direction}",
                "device": self._get_device_info(),
                "icon": self._get_navigation_icon(direction),
                "availability": {
                    "topic": f"isg/{self.device_id}/android/availability",
                    "payload_available": "online",
                    "payload_not_available": "offline"
                }
            }
            
            discovery_topic = f"{self.base_topic}/button/{entity_id}/config"
            await self.mqtt_client.publish(discovery_topic, config, retain=True)
            
            self.entities[f"button_nav_{direction}"] = {
                "config_topic": discovery_topic,
                "command_topic": config["command_topic"],
                "entity_id": entity_id
            }
        
        logger.info("Setup navigation button entities")
    
    async def _setup_volume_controls(self):
        """设置音量控制实体"""
        streams = {
            "media": "Media Volume",
            "notification": "Notification Volume",
            "system": "System Volume"
        }
        
        for stream, name in streams.items():
            entity_id = f"{self.device_id}_volume_{stream}"
            
            config = {
                "name": name,
                "unique_id": entity_id,
                "command_topic": f"isg/{self.device_id}/android/volume/{stream}/set",
                "state_topic": f"isg/{self.device_id}/android/volume/{stream}/state",
                "min": 0,
                "max": 15,
                "step": 1,
                "mode": "slider",
                "device": self._get_device_info(),
                "icon": "mdi:volume-high",
                "availability": {
                    "topic": f"isg/{self.device_id}/android/availability",
                    "payload_available": "online",
                    "payload_not_available": "offline"
                }
            }
            
            discovery_topic = f"{self.base_topic}/number/{entity_id}/config"
            await self.mqtt_client.publish(discovery_topic, config, retain=True)
            
            self.entities[f"volume_{stream}"] = {
                "config_topic": discovery_topic,
                "command_topic": config["command_topic"],
                "state_topic": config["state_topic"],
                "entity_id": entity_id
            }
        
        logger.info("Setup volume control entities")
    
    async def _setup_brightness_control(self):
        """设置亮度控制实体"""
        entity_id = f"{self.device_id}_brightness"
        
        config = {
            "name": "Screen Brightness",
            "unique_id": entity_id,
            "command_topic": f"isg/{self.device_id}/android/brightness/set",
            "state_topic": f"isg/{self.device_id}/android/brightness/state",
            "min": 0,
            "max": 255,
            "step": 1,
            "mode": "slider",
            "device": self._get_device_info(),
            "icon": "mdi:brightness-6",
            "availability": {
                "topic": f"isg/{self.device_id}/android/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        discovery_topic = f"{self.base_topic}/number/{entity_id}/config"
        await self.mqtt_client.publish(discovery_topic, config, retain=True)
        
        self.entities["brightness"] = {
            "config_topic": discovery_topic,
            "command_topic": config["command_topic"],
            "state_topic": config["state_topic"],
            "entity_id": entity_id
        }
        
        logger.info("Setup brightness control entity")
    
    async def _setup_screen_switch(self):
        """设置屏幕开关实体"""
        entity_id = f"{self.device_id}_screen"
        
        config = {
            "name": "Screen Power",
            "unique_id": entity_id,
            "command_topic": f"isg/{self.device_id}/android/screen/set",
            "state_topic": f"isg/{self.device_id}/android/screen/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device": self._get_device_info(),
            "icon": "mdi:monitor",
            "availability": {
                "topic": f"isg/{self.device_id}/android/availability",
                "payload_available": "online",
                "payload_not_available": "offline"
            }
        }
        
        discovery_topic = f"{self.base_topic}/switch/{entity_id}/config"
        await self.mqtt_client.publish(discovery_topic, config, retain=True)
        
        self.entities["screen"] = {
            "config_topic": discovery_topic,
            "command_topic": config["command_topic"],
            "state_topic": config["state_topic"],
            "entity_id": entity_id
        }
        
        logger.info("Setup screen switch entity")
    
    async def _setup_system_sensors(self):
        """设置系统传感器实体"""
        sensors = {
            "cpu_usage": {"name": "CPU Usage", "unit": "%", "icon": "mdi:cpu-64-bit"},
            "memory_usage": {"name": "Memory Usage", "unit": "%", "icon": "mdi:memory"},
            "battery_level": {"name": "Battery Level", "unit": "%", "icon": "mdi:battery"},
            "battery_temperature": {"name": "Battery Temperature", "unit": "°C", "icon": "mdi:thermometer"},
            "storage_usage": {"name": "Storage Usage", "unit": "%", "icon": "mdi:harddisk"}
        }
        
        for sensor_key, sensor_info in sensors.items():
            entity_id = f"{self.device_id}_{sensor_key}"
            
            config = {
                "name": sensor_info["name"],
                "unique_id": entity_id,
                "state_topic": f"isg/{self.device_id}/android/sensor/{sensor_key}",
                "unit_of_measurement": sensor_info["unit"],
                "device": self._get_device_info(),
                "icon": sensor_info["icon"],
                "availability": {
                    "topic": f"isg/{self.device_id}/android/availability",
                    "payload_available": "online",
                    "payload_not_available": "offline"
                }
            }
            
            discovery_topic = f"{self.base_topic}/sensor/{entity_id}/config"
            await self.mqtt_client.publish(discovery_topic, config, retain=True)
            
            self.entities[f"sensor_{sensor_key}"] = {
                "config_topic": discovery_topic,
                "state_topic": config["state_topic"],
                "entity_id": entity_id
            }
        
        logger.info("Setup system sensor entities")
    
    async def _setup_app_shortcuts(self):
        """设置应用快捷方式实体"""
        for app_key, package_name in self.settings.apps.items():
            app_name = app_key.replace('_', ' ').title()
            entity_id = f"{self.device_id}_app_{app_key}"
            
            config = {
                "name": f"Launch {app_name}",
                "unique_id": entity_id,
                "command_topic": f"isg/{self.device_id}/android/app/{app_key}/launch",
                "device": self._get_device_info(),
                "icon": "mdi:play",
                "availability": {
                    "topic": f"isg/{self.device_id}/android/availability",
                    "payload_available": "online",
                    "payload_not_available": "offline"
                }
            }
            
            discovery_topic = f"{self.base_topic}/button/{entity_id}/config"
            await self.mqtt_client.publish(discovery_topic, config, retain=True)
            
            self.entities[f"app_{app_key}"] = {
                "config_topic": discovery_topic,
                "command_topic": config["command_topic"],
                "entity_id": entity_id
            }
        
        logger.info("Setup app shortcut entities")
    
    async def _setup_command_subscriptions(self):
        """设置命令主题订阅"""
        
        # 截图命令
        await self.mqtt_client.subscribe(
            f"isg/{self.device_id}/android/screenshot/take",
            self._handle_screenshot_command
        )
        
        # 导航命令
        for direction in ["up", "down", "left", "right", "center", "back", "home", "menu"]:
            await self.mqtt_client.subscribe(
                f"isg/{self.device_id}/android/navigation/{direction}",
                lambda topic, payload, d=direction: self._handle_navigation_command(topic, payload, d)
            )
        
        # 音量命令
        for stream in ["media", "notification", "system"]:
            await self.mqtt_client.subscribe(
                f"isg/{self.device_id}/android/volume/{stream}/set",
                lambda topic, payload, s=stream: self._handle_volume_command(topic, payload, s)
            )
        
        # 亮度命令
        await self.mqtt_client.subscribe(
            f"isg/{self.device_id}/android/brightness/set",
            self._handle_brightness_command
        )
        
        # 屏幕开关命令
        await self.mqtt_client.subscribe(
            f"isg/{self.device_id}/android/screen/set",
            self._handle_screen_command
        )
        
        # 应用启动命令
        for app_key in self.settings.apps.keys():
            await self.mqtt_client.subscribe(
                f"isg/{self.device_id}/android/app/{app_key}/launch",
                lambda topic, payload, app=app_key: self._handle_app_launch_command(topic, payload, app)
            )
        
        logger.info("Command subscriptions setup completed")
    
    async def _publish_initial_states(self):
        """发布初始状态"""
        
        # 发布可用性状态
        await self.mqtt_client.publish(
            f"isg/{self.device_id}/android/availability",
            "online",
            retain=True
        )
        
        # 发布系统状态
        await self._update_system_states()
        
        logger.info("Initial states published")
    
    async def _state_update_loop(self):
        """状态更新循环"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒更新一次
                await self._update_system_states()
                
            except asyncio.CancelledError:
                logger.info("State update loop cancelled")
                break
            except Exception as e:
                logger.error(f"State update loop error: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    async def _update_system_states(self):
        """更新系统状态"""
        try:
            # 获取系统信息
            system_info = await self.device_controller.get_system_info()
            performance = await self.device_controller.get_performance_stats()
            
            # 更新传感器状态
            sensors = {
                "cpu_usage": performance.get("cpu_usage", 0),
                "memory_usage": performance.get("memory_usage", 0),
                "battery_level": system_info.get("battery_level", 0),
                "battery_temperature": system_info.get("battery_temperature", 0),
                "storage_usage": performance.get("storage_usage", 0)
            }
            
            for sensor_name, value in sensors.items():
                topic = f"isg/{self.device_id}/android/sensor/{sensor_name}"
                await self.mqtt_client.publish(topic, value, retain=True)
            
            # 更新屏幕状态
            screen_on = system_info.get("screen_on", False)
            screen_topic = f"isg/{self.device_id}/android/screen/state"
            await self.mqtt_client.publish(screen_topic, "ON" if screen_on else "OFF", retain=True)
            
            # 更新亮度状态
            brightness = system_info.get("brightness")
            if brightness is not None:
                brightness_topic = f"isg/{self.device_id}/android/brightness/state"
                await self.mqtt_client.publish(brightness_topic, brightness, retain=True)
            
            # 更新音量状态
            for stream in [VolumeStream.MEDIA, VolumeStream.NOTIFICATION, VolumeStream.SYSTEM]:
                try:
                    level = await self.device_controller.get_volume(stream)
                    if level is not None:
                        volume_topic = f"isg/{self.device_id}/android/volume/{stream.value}/state"
                        await self.mqtt_client.publish(volume_topic, level, retain=True)
                except Exception:
                    pass  # 忽略单个音量流的错误
            
        except Exception as e:
            logger.error(f"Update system states error: {e}")
    
    # 命令处理方法
    
    async def _handle_screenshot_command(self, topic: str, payload: str):
        """处理截图命令"""
        try:
            logger.info("Received screenshot command")
            
            # 捕获截图
            screenshot_info = await self.screenshot_service.capture_screenshot()
            
            if screenshot_info:
                # 获取Base64编码
                base64_data = await self.screenshot_service.get_screenshot_as_base64(
                    screenshot_info["filename"]
                )
                
                if base64_data:
                    # 发布截图数据
                    image_topic = f"isg/{self.device_id}/android/screenshot/image"
                    await self.mqtt_client.publish(image_topic, base64_data)
                    
                    logger.info(f"Screenshot published to MQTT: {screenshot_info['filename']}")
                else:
                    logger.error("Failed to encode screenshot to base64")
            else:
                logger.error("Failed to capture screenshot")
                
        except Exception as e:
            logger.error(f"Screenshot command error: {e}")
    
    async def _handle_navigation_command(self, topic: str, payload: str, direction: str):
        """处理导航命令"""
        try:
            logger.info(f"Received navigation command: {direction}")
            
            nav_direction = NavigationDirection(direction)
            success = await self.device_controller.navigate(nav_direction)
            
            if success:
                logger.info(f"Navigation {direction} executed successfully")
            else:
                logger.warning(f"Navigation {direction} failed")
                
        except Exception as e:
            logger.error(f"Navigation command error: {e}")
    
    async def _handle_volume_command(self, topic: str, payload: str, stream: str):
        """处理音量命令"""
        try:
            logger.info(f"Received volume command: {stream} = {payload}")
            
            level = int(payload)
            volume_stream = VolumeStream(stream)
            success = await self.device_controller.set_volume(volume_stream, level)
            
            if success:
                # 更新状态
                state_topic = f"isg/{self.device_id}/android/volume/{stream}/state"
                await self.mqtt_client.publish(state_topic, level, retain=True)
                logger.info(f"Volume {stream} set to {level}")
            else:
                logger.warning(f"Failed to set volume {stream} to {level}")
                
        except Exception as e:
            logger.error(f"Volume command error: {e}")
    
    async def _handle_brightness_command(self, topic: str, payload: str):
        """处理亮度命令"""
        try:
            logger.info(f"Received brightness command: {payload}")
            
            level = int(payload)
            success = await self.device_controller.set_brightness(level)
            
            if success:
                # 更新状态
                state_topic = f"isg/{self.device_id}/android/brightness/state"
                await self.mqtt_client.publish(state_topic, level, retain=True)
                logger.info(f"Brightness set to {level}")
            else:
                logger.warning(f"Failed to set brightness to {level}")
                
        except Exception as e:
            logger.error(f"Brightness command error: {e}")
    
    async def _handle_screen_command(self, topic: str, payload: str):
        """处理屏幕开关命令"""
        try:
            logger.info(f"Received screen command: {payload}")
            
            if payload == "ON":
                success = await self.device_controller.screen_on()
            elif payload == "OFF":
                success = await self.device_controller.screen_off()
            else:
                logger.warning(f"Invalid screen command payload: {payload}")
                return
            
            if success:
                # 更新状态
                state_topic = f"isg/{self.device_id}/android/screen/state"
                await self.mqtt_client.publish(state_topic, payload, retain=True)
                logger.info(f"Screen {'turned on' if payload == 'ON' else 'turned off'}")
            else:
                logger.warning(f"Failed to set screen to {payload}")
                
        except Exception as e:
            logger.error(f"Screen command error: {e}")
    
    async def _handle_app_launch_command(self, topic: str, payload: str, app_key: str):
        """处理应用启动命令"""
        try:
            logger.info(f"Received app launch command: {app_key}")
            
            package_name = self.settings.apps.get(app_key)
            if package_name:
                success = await self.device_controller.launch_app(package_name)
                
                if success:
                    logger.info(f"App {app_key} launched successfully")
                else:
                    logger.warning(f"Failed to launch app {app_key}")
            else:
                logger.warning(f"Unknown app key: {app_key}")
                
        except Exception as e:
            logger.error(f"App launch command error: {e}")
    
    # 辅助方法
    
    def _get_device_info(self) -> Dict[str, Any]:
        """获取设备信息（用于Home Assistant设备注册）"""
        return {
            "identifiers": [self.device_id],
            "name": "Android TV Controller",
            "model": "iSG Android Device",
            "manufacturer": "iSG",
            "sw_version": "1.0.0"
        }
    
    def _get_navigation_icon(self, direction: str) -> str:
        """获取导航按钮图标"""
        icons = {
            "up": "mdi:arrow-up",
            "down": "mdi:arrow-down",
            "left": "mdi:arrow-left",
            "right": "mdi:arrow-right",
            "center": "mdi:checkbox-marked-circle",
            "back": "mdi:arrow-left",
            "home": "mdi:home",
            "menu": "mdi:menu"
        }
        return icons.get(direction, "mdi:gesture-tap")


# 全局Home Assistant MQTT集成实例
_homeassistant_mqtt_instance: Optional[HomeAssistantMQTT] = None


def get_homeassistant_mqtt() -> HomeAssistantMQTT:
    """获取Home Assistant MQTT集成实例（单例）"""
    global _homeassistant_mqtt_instance
    if _homeassistant_mqtt_instance is None:
        _homeassistant_mqtt_instance = HomeAssistantMQTT()
    return _homeassistant_mqtt_instance