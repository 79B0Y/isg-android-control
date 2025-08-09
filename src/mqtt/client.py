"""
MQTT客户端模块
管理与MQTT broker的连接和消息处理
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime

import paho.mqtt.client as mqtt
from loguru import logger

from src.core.config import get_settings
from src.core.logger import log_mqtt_message


class MQTTClient:
    """MQTT客户端类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.mqtt_config = self.settings.mqtt
        
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.reconnect_task: Optional[asyncio.Task] = None
        
        logger.info(f"MQTT Client initialized, broker: {self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}")
    
    async def connect(self) -> bool:
        """连接到MQTT broker"""
        try:
            # 创建MQTT客户端
            self.client = mqtt.Client(
                client_id=self.mqtt_config.client_id,
                clean_session=True
            )
            
            # 设置用户名和密码
            if self.mqtt_config.username and self.mqtt_config.password:
                self.client.username_pw_set(
                    self.mqtt_config.username,
                    self.mqtt_config.password
                )
            
            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_publish = self._on_publish
            
            # 连接到broker
            logger.info(f"Connecting to MQTT broker: {self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}")
            
            self.client.connect_async(
                self.mqtt_config.broker_host,
                self.mqtt_config.broker_port,
                self.mqtt_config.keep_alive
            )
            
            # 启动网络循环
            self.client.loop_start()
            
            # 等待连接建立
            for _ in range(10):  # 最多等待10秒
                if self.is_connected:
                    break
                await asyncio.sleep(1)
            
            if self.is_connected:
                logger.info("MQTT client connected successfully")
                # 启动重连任务
                self.reconnect_task = asyncio.create_task(self._reconnect_loop())
                return True
            else:
                logger.error("MQTT client connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"MQTT client connection error: {e}")
            return False
    
    async def disconnect(self):
        """断开MQTT连接"""
        try:
            if self.reconnect_task:
                self.reconnect_task.cancel()
                self.reconnect_task = None
            
            if self.client and self.is_connected:
                logger.info("Disconnecting MQTT client")
                self.client.loop_stop()
                self.client.disconnect()
                self.is_connected = False
                
        except Exception as e:
            logger.error(f"MQTT client disconnect error: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.is_connected = True
            logger.info("MQTT client connected to broker")
        else:
            self.is_connected = False
            logger.error(f"MQTT client connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"MQTT client disconnected unexpectedly (code: {rc})")
        else:
            logger.info("MQTT client disconnected normally")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            log_mqtt_message(topic, payload, "in")
            
            # 查找匹配的处理器
            handler = self.message_handlers.get(topic)
            if handler:
                asyncio.create_task(handler(topic, payload))
            else:
                # 检查通配符匹配
                for pattern, handler in self.message_handlers.items():
                    if self._topic_matches(pattern, topic):
                        asyncio.create_task(handler(topic, payload))
                        break
                
        except Exception as e:
            logger.error(f"MQTT message handling error: {e}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅回调"""
        logger.debug(f"MQTT subscription successful, mid: {mid}, qos: {granted_qos}")
    
    def _on_publish(self, client, userdata, mid):
        """发布回调"""
        logger.debug(f"MQTT message published, mid: {mid}")
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """检查主题是否匹配模式（支持+和#通配符）"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        i = 0
        j = 0
        
        while i < len(pattern_parts) and j < len(topic_parts):
            if pattern_parts[i] == '#':
                # # 匹配剩余所有部分
                return True
            elif pattern_parts[i] == '+':
                # + 匹配单个部分
                i += 1
                j += 1
            elif pattern_parts[i] == topic_parts[j]:
                # 精确匹配
                i += 1
                j += 1
            else:
                return False
        
        # 检查是否完全匹配
        return i == len(pattern_parts) and j == len(topic_parts)
    
    async def _reconnect_loop(self):
        """重连循环任务"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                if not self.is_connected and self.client:
                    logger.info("Attempting to reconnect to MQTT broker")
                    try:
                        self.client.reconnect()
                    except Exception as e:
                        logger.warning(f"MQTT reconnection attempt failed: {e}")
                        
            except asyncio.CancelledError:
                logger.info("MQTT reconnect loop cancelled")
                break
            except Exception as e:
                logger.error(f"MQTT reconnect loop error: {e}")
    
    async def publish(self, topic: str, payload: Any, qos: int = None, retain: bool = None) -> bool:
        """发布消息"""
        try:
            if not self.client or not self.is_connected:
                logger.warning("MQTT client not connected, cannot publish message")
                return False
            
            # 使用配置的默认值
            qos = qos if qos is not None else self.mqtt_config.qos
            retain = retain if retain is not None else self.mqtt_config.retain
            
            # 序列化载荷
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, ensure_ascii=False)
            else:
                payload_str = str(payload)
            
            # 发布消息
            result = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log_mqtt_message(topic, payload_str, "out")
                return True
            else:
                logger.warning(f"MQTT publish failed: {mqtt.error_string(result.rc)}")
                return False
                
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False
    
    async def subscribe(self, topic: str, handler: Callable[[str, str], None], qos: int = None) -> bool:
        """订阅主题"""
        try:
            if not self.client or not self.is_connected:
                logger.warning("MQTT client not connected, cannot subscribe")
                return False
            
            qos = qos if qos is not None else self.mqtt_config.qos
            
            # 添加消息处理器
            self.message_handlers[topic] = handler
            
            # 订阅主题
            result = self.client.subscribe(topic, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"MQTT subscribed to topic: {topic}")
                return True
            else:
                logger.warning(f"MQTT subscribe failed: {mqtt.error_string(result[0])}")
                return False
                
        except Exception as e:
            logger.error(f"MQTT subscribe error: {e}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """取消订阅主题"""
        try:
            if not self.client:
                return False
            
            # 移除消息处理器
            self.message_handlers.pop(topic, None)
            
            # 取消订阅
            if self.is_connected:
                result = self.client.unsubscribe(topic)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"MQTT unsubscribed from topic: {topic}")
                    return True
                else:
                    logger.warning(f"MQTT unsubscribe failed: {mqtt.error_string(result[0])}")
                    return False
            else:
                logger.info(f"MQTT client not connected, removed handler for topic: {topic}")
                return True
                
        except Exception as e:
            logger.error(f"MQTT unsubscribe error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取MQTT客户端状态"""
        return {
            "connected": self.is_connected,
            "broker_host": self.mqtt_config.broker_host,
            "broker_port": self.mqtt_config.broker_port,
            "client_id": self.mqtt_config.client_id,
            "subscribed_topics": list(self.message_handlers.keys()),
            "timestamp": datetime.now().isoformat()
        }


# 全局MQTT客户端实例
_mqtt_client_instance: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """获取MQTT客户端实例（单例）"""
    global _mqtt_client_instance
    if _mqtt_client_instance is None:
        _mqtt_client_instance = MQTTClient()
    return _mqtt_client_instance