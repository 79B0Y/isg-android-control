#!/usr/bin/env python3
"""
Android Controller Service - Main Entry Point
运行在Termux Ubuntu环境中的Android设备控制服务
"""

import asyncio
import signal
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import click
import uvicorn
from fastapi import FastAPI
from loguru import logger

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.api.main import create_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"Starting Android Controller Service on {settings.server.host}:{settings.server.port}")
    
    # 启动时初始化
    try:
        # 这里可以添加启动时的初始化逻辑
        # 比如检查ADB连接、初始化MQTT等
        yield
    finally:
        # 清理资源
        logger.info("Shutting down Android Controller Service")


def create_application() -> FastAPI:
    """创建FastAPI应用"""
    return create_app(lifespan=lifespan)


@click.command()
@click.option("--config", "-c", default="configs/config.yaml", help="Configuration file path")
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", "-p", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def main(config: str, host: str, port: int, reload: bool, debug: bool):
    """启动Android Controller Service"""
    
    # 设置日志
    setup_logging(debug=debug)
    
    # 检查配置文件
    config_path = Path(config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config}")
        sys.exit(1)
    
    # 获取设置
    settings = get_settings(config_file=config)
    
    # 覆盖命令行参数
    if host:
        settings.server.host = host
    if port:
        settings.server.port = port
    if reload:
        settings.server.reload = reload
    
    logger.info(f"Configuration loaded from: {config}")
    logger.info(f"Server will start on {settings.server.host}:{settings.server.port}")
    
    # 创建必要的目录
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data/screenshots").mkdir(parents=True, exist_ok=True)
    
    # 创建应用
    app = create_application()
    
    # 启动服务器
    try:
        uvicorn.run(
            "src.main:create_application",
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload or reload,
            factory=True,
            log_config=None,  # 使用我们自己的日志配置
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()