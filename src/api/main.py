"""
FastAPI主应用模块
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from src.api.middleware import LoggingMiddleware
from src.api.routes import (
    remote,
    audio,
    display,
    apps,
    system,
    screenshot,
    network
)
from src.core.config import get_settings


def create_app(lifespan: Optional[object] = None) -> FastAPI:
    """创建FastAPI应用"""
    
    settings = get_settings()
    
    # 创建FastAPI实例
    app = FastAPI(
        title="Android Controller Service",
        description="iSG Android设备控制服务 - 运行在Termux Ubuntu环境",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # 添加中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(LoggingMiddleware)
    
    # 注册路由
    app.include_router(remote.router, prefix="/api/v1/remote", tags=["Remote Control"])
    app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio Control"])
    app.include_router(display.router, prefix="/api/v1/display", tags=["Display Control"])
    app.include_router(apps.router, prefix="/api/v1/apps", tags=["App Management"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["System Monitoring"])
    app.include_router(screenshot.router, prefix="/api/v1/screenshot", tags=["Screenshot"])
    app.include_router(network.router, prefix="/api/v1/network", tags=["Network Control"])
    
    # 根路径健康检查
    @app.get("/", tags=["Health"])
    async def root():
        """根路径健康检查"""
        return {
            "status": "ok",
            "service": "Android Controller Service",
            "version": "1.0.0",
            "description": "iSG Android设备控制服务"
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """健康检查接口"""
        from src.core.adb_controller import get_adb_controller
        
        adb = get_adb_controller()
        is_connected = await adb.check_connection()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "adb_connected": is_connected,
            "timestamp": "2024-01-01T00:00:00Z"  # 实际应用中使用 datetime.utcnow()
        }
    
    logger.info("FastAPI application created successfully")
    
    return app