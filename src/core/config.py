"""
配置管理模块
支持从YAML文件和环境变量加载配置
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    port: int = Field(default=8000, env="SERVER_PORT")
    workers: int = Field(default=1, env="SERVER_WORKERS")
    reload: bool = Field(default=False, env="SERVER_RELOAD")


class ADBConfig(BaseSettings):
    """ADB配置"""
    device_serial: str = Field(default="127.0.0.1:5555", env="ADB_DEVICE_SERIAL")
    timeout: int = Field(default=30, env="ADB_TIMEOUT")
    retry_attempts: int = Field(default=3, env="ADB_RETRY_ATTEMPTS")
    retry_delay: float = Field(default=1.0, env="ADB_RETRY_DELAY")
    connection_timeout: int = Field(default=10, env="ADB_CONNECTION_TIMEOUT")


class NetworkConfig(BaseSettings):
    """网络配置"""
    static_ip: str = Field(default="192.168.1.100", env="STATIC_IP")
    netmask: str = Field(default="255.255.255.0", env="NETMASK")
    gateway: str = Field(default="192.168.1.1", env="GATEWAY")
    dns_primary: str = Field(default="8.8.8.8", env="DNS_PRIMARY")
    dns_secondary: str = Field(default="8.8.4.4", env="DNS_SECONDARY")


class ScreenshotConfig(BaseSettings):
    """截图配置"""
    quality: int = Field(default=80, env="SCREENSHOT_QUALITY")
    format: str = Field(default="JPEG", env="SCREENSHOT_FORMAT")
    max_files: int = Field(default=3, env="SCREENSHOT_MAX_FILES")
    storage_path: str = Field(default="data/screenshots", env="SCREENSHOT_STORAGE_PATH")
    auto_cleanup: bool = Field(default=True, env="SCREENSHOT_AUTO_CLEANUP")


class MQTTConfig(BaseSettings):
    """MQTT配置"""
    broker_host: str = Field(default="192.168.1.10", env="MQTT_BROKER_HOST")
    broker_port: int = Field(default=1883, env="MQTT_BROKER_PORT")
    username: str = Field(default="", env="MQTT_USERNAME")
    password: str = Field(default="", env="MQTT_PASSWORD")
    client_id: str = Field(default="android_controller", env="MQTT_CLIENT_ID")
    device_id: str = Field(default="android_controller", env="MQTT_DEVICE_ID")
    base_topic: str = Field(default="homeassistant", env="MQTT_BASE_TOPIC")
    qos: int = Field(default=1, env="MQTT_QOS")
    retain: bool = Field(default=True, env="MQTT_RETAIN")
    keep_alive: int = Field(default=60, env="MQTT_KEEP_ALIVE")


class MonitoringConfig(BaseSettings):
    """监控配置"""
    performance_interval: int = Field(default=5, env="MONITORING_PERFORMANCE_INTERVAL")
    battery_interval: int = Field(default=30, env="MONITORING_BATTERY_INTERVAL")
    network_interval: int = Field(default=10, env="MONITORING_NETWORK_INTERVAL")
    cache_ttl: int = Field(default=60, env="MONITORING_CACHE_TTL")


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="structured", env="LOG_FORMAT")
    file_level: str = Field(default="DEBUG", env="LOG_FILE_LEVEL")
    console_level: str = Field(default="INFO", env="LOG_CONSOLE_LEVEL")
    max_file_size: str = Field(default="50MB", env="LOG_MAX_FILE_SIZE")
    backup_count: int = Field(default=10, env="LOG_BACKUP_COUNT")
    log_dir: str = Field(default="data/logs", env="LOG_DIR")


class Settings(PydanticBaseSettings):
    """主配置类"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    adb: ADBConfig = Field(default_factory=ADBConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    apps: Dict[str, str] = Field(default_factory=dict)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, config_file: str) -> "Settings":
        """从YAML文件加载配置"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 创建配置实例
        settings = cls()
        
        # 更新配置
        if config_data:
            for section_name, section_data in config_data.items():
                if hasattr(settings, section_name) and isinstance(section_data, dict):
                    section_obj = getattr(settings, section_name)
                    if hasattr(section_obj, '__dict__'):
                        for key, value in section_data.items():
                            if hasattr(section_obj, key):
                                setattr(section_obj, key, value)
                elif section_name == "apps":
                    settings.apps = section_data or {}

        return settings

    def validate_config(self) -> bool:
        """验证配置有效性"""
        errors = []
        
        # 验证端口范围
        if not (1 <= self.server.port <= 65535):
            errors.append(f"Invalid server port: {self.server.port}")
            
        if not (1 <= self.mqtt.broker_port <= 65535):
            errors.append(f"Invalid MQTT port: {self.mqtt.broker_port}")
        
        # 验证截图质量
        if not (1 <= self.screenshot.quality <= 100):
            errors.append(f"Invalid screenshot quality: {self.screenshot.quality}")
        
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {self.logging.level}")
        
        if errors:
            raise ValueError("Configuration validation errors: " + "; ".join(errors))
        
        return True


@lru_cache()
def get_settings(config_file: Optional[str] = None) -> Settings:
    """获取配置单例"""
    if config_file:
        return Settings.load_from_yaml(config_file)
    else:
        return Settings()