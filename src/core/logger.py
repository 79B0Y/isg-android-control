"""
日志管理模块
基于loguru实现结构化日志记录
"""

import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger


def setup_logging(debug: bool = False, log_dir: str = "data/logs") -> None:
    """设置日志配置"""
    
    # 清除默认处理器
    logger.remove()
    
    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 控制台处理器
    console_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        format=console_format,
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 文件处理器 - 所有日志
    logger.add(
        f"{log_dir}/android_controller.log",
        format=file_format,
        level="DEBUG",
        rotation="50 MB",
        retention="10 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )
    
    # 错误日志文件
    logger.add(
        f"{log_dir}/errors.log",
        format=file_format,
        level="ERROR",
        rotation="50 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )
    
    # API访问日志
    logger.add(
        f"{log_dir}/access.log",
        format=file_format,
        level="INFO",
        rotation="50 MB",
        retention="7 days",
        compression="gz",
        filter=lambda record: record["name"].startswith("src.api"),
    )
    
    logger.info("Logging system initialized")


def get_logger(name: str = None):
    """获取指定名称的logger"""
    if name:
        return logger.bind(name=name)
    return logger


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """记录API请求日志"""
    logger.bind(name="src.api.access").info(
        f"{method} {path} - {status_code} - {duration:.3f}s",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            **kwargs
        }
    )


def log_adb_command(command: str, success: bool, duration: float, output: str = None):
    """记录ADB命令执行日志"""
    level = "INFO" if success else "WARNING"
    message = f"ADB command: {command} - {'SUCCESS' if success else 'FAILED'} - {duration:.3f}s"
    
    logger.bind(name="src.core.adb").log(
        level,
        message,
        extra={
            "command": command,
            "success": success,
            "duration": duration,
            "output": output[:200] if output else None  # 限制输出长度
        }
    )


def log_mqtt_message(topic: str, payload: str, direction: str = "out"):
    """记录MQTT消息日志"""
    logger.bind(name="src.mqtt").debug(
        f"MQTT {direction.upper()}: {topic}",
        extra={
            "topic": topic,
            "payload": payload[:100] if payload else None,  # 限制载荷长度
            "direction": direction
        }
    )


def log_error_with_context(error: Exception, context: Dict[str, Any] = None):
    """记录带上下文的错误日志"""
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        extra={"context": context or {}}
    )