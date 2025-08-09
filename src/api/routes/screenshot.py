"""
截图功能API路由
"""

from typing import List
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from loguru import logger

from src.services.screenshot_service import get_screenshot_service
from src.models.requests import ScreenshotRequest
from src.models.responses import BaseResponse, ResponseStatus, ScreenshotInfo

router = APIRouter()


@router.post("/capture", response_model=BaseResponse[ScreenshotInfo])
async def capture_screenshot(request: ScreenshotRequest = None):
    """
    捕获屏幕截图
    
    - **quality**: 图片质量 1-100 (可选)
    - **format**: 图片格式 JPEG/PNG (可选)
    - **filename**: 自定义文件名 (可选)
    """
    try:
        service = get_screenshot_service()
        
        # 提取请求参数
        quality = None
        format = None
        filename = None
        
        if request:
            quality = request.quality
            format = request.format
            filename = request.filename
        
        # 捕获截图
        screenshot_info = await service.capture_screenshot(
            quality=quality,
            format=format,
            filename=filename
        )
        
        if screenshot_info:
            # 转换为ScreenshotInfo模型
            info = ScreenshotInfo(
                filename=screenshot_info["filename"],
                file_path=screenshot_info["file_path"],
                file_size=screenshot_info["file_size"],
                width=screenshot_info["width"],
                height=screenshot_info["height"],
                format=screenshot_info["format"],
                quality=screenshot_info["quality"],
                created_at=screenshot_info["created_at"]
            )
            
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Screenshot captured successfully",
                data=info
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to capture screenshot"
            )
            
    except Exception as e:
        logger.error(f"Capture screenshot API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=BaseResponse[List[ScreenshotInfo]])
async def get_screenshot_list():
    """获取截图文件列表"""
    try:
        service = get_screenshot_service()
        screenshot_list = await service.get_screenshot_list()
        
        # 转换为ScreenshotInfo模型
        info_list = []
        for item in screenshot_list:
            info = ScreenshotInfo(
                filename=item["filename"],
                file_path=item["file_path"],
                file_size=item["file_size"],
                width=item["width"],
                height=item["height"],
                format=item["format"],
                quality=0,  # 从文件信息中无法获取原始质量
                created_at=item["created_at"]
            )
            info_list.append(info)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(info_list)} screenshots",
            data=info_list
        )
        
    except Exception as e:
        logger.error(f"Get screenshot list API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=BaseResponse[ScreenshotInfo])
async def get_latest_screenshot():
    """获取最新的截图信息"""
    try:
        service = get_screenshot_service()
        latest = await service.get_latest_screenshot()
        
        if latest:
            info = ScreenshotInfo(
                filename=latest["filename"],
                file_path=latest["file_path"],
                file_size=latest["file_size"],
                width=latest["width"],
                height=latest["height"],
                format=latest["format"],
                quality=0,
                created_at=latest["created_at"]
            )
            
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Latest screenshot retrieved",
                data=info
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="No screenshots found"
            )
            
    except Exception as e:
        logger.error(f"Get latest screenshot API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_screenshot(filename: str):
    """下载截图文件"""
    try:
        service = get_screenshot_service()
        file_path = service.storage_path / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Screenshot not found: {filename}"
            )
        
        # 确定MIME类型
        if filename.lower().endswith('.png'):
            media_type = 'image/png'
        else:
            media_type = 'image/jpeg'
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Download screenshot API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/base64/{filename}")
async def get_screenshot_base64(filename: str):
    """获取截图的Base64编码"""
    try:
        service = get_screenshot_service()
        base64_data = await service.get_screenshot_as_base64(filename)
        
        if base64_data:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Screenshot base64 retrieved",
                data={
                    "filename": filename,
                    "base64": base64_data,
                    "size": len(base64_data)
                }
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Screenshot not found: {filename}"
            )
            
    except Exception as e:
        logger.error(f"Get screenshot base64 API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
async def delete_screenshot(filename: str):
    """删除指定的截图文件"""
    try:
        service = get_screenshot_service()
        success = await service.delete_screenshot(filename)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Screenshot deleted successfully",
                data={"filename": filename}
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Screenshot not found: {filename}"
            )
            
    except Exception as e:
        logger.error(f"Delete screenshot API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def clear_all_screenshots():
    """清除所有截图文件"""
    try:
        service = get_screenshot_service()
        deleted_count = await service.clear_all_screenshots()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Cleared {deleted_count} screenshots",
            data={"deleted_count": deleted_count}
        )
        
    except Exception as e:
        logger.error(f"Clear screenshots API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_screenshot_stats():
    """获取截图存储统计信息"""
    try:
        service = get_screenshot_service()
        stats = await service.get_storage_stats()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Screenshot stats retrieved",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Get screenshot stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture-and-get")
async def capture_and_get_screenshot():
    """捕获截图并直接返回文件"""
    try:
        service = get_screenshot_service()
        
        # 捕获截图
        screenshot_info = await service.capture_screenshot()
        
        if screenshot_info:
            file_path = screenshot_info["file_path"]
            filename = screenshot_info["filename"]
            
            # 确定MIME类型
            if filename.lower().endswith('.png'):
                media_type = 'image/png'
            else:
                media_type = 'image/jpeg'
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=filename
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to capture screenshot"
            )
            
    except Exception as e:
        logger.error(f"Capture and get screenshot API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))