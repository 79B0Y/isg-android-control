"""
API中间件模块
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.core.logger import log_api_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """API请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 记录请求开始
        logger.debug(f"API Request: {request.method} {request.url.path} from {client_ip}")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        log_api_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration=process_time,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "")
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response