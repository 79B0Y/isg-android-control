"""
音频控制API路由
"""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from src.core.device_controller import get_device_controller
from src.models.requests import VolumeRequest, VolumeStream
from src.models.responses import BaseResponse, ResponseStatus

router = APIRouter()


@router.post("/volume")
async def set_volume(request: VolumeRequest):
    """
    设置音量
    
    - **stream**: 音频流类型 (media, notification, system, ring, alarm, voice_call)
    - **level**: 音量级别 (0-15)
    """
    try:
        device = get_device_controller()
        success = await device.set_volume(request.stream, request.level)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Volume set successfully",
                data={"stream": request.stream, "level": request.level}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set volume for {request.stream}"
            )
            
    except Exception as e:
        logger.error(f"Set volume API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume/{stream}")
async def get_volume(stream: VolumeStream):
    """
    获取指定流的音量级别
    """
    try:
        device = get_device_controller()
        level = await device.get_volume(stream)
        
        if level is not None:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Volume level retrieved",
                data={"stream": stream, "level": level}
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve volume for {stream}"
            )
            
    except Exception as e:
        logger.error(f"Get volume API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/volume/{stream}/up")
async def volume_up(stream: VolumeStream):
    """
    增加音量
    """
    try:
        device = get_device_controller()
        success = await device.volume_up(stream)
        
        if success:
            current_level = await device.get_volume(stream)
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Volume increased",
                data={"stream": stream, "level": current_level}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to increase volume for {stream}"
            )
            
    except Exception as e:
        logger.error(f"Volume up API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/volume/{stream}/down")
async def volume_down(stream: VolumeStream):
    """
    降低音量
    """
    try:
        device = get_device_controller()
        success = await device.volume_down(stream)
        
        if success:
            current_level = await device.get_volume(stream)
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Volume decreased",
                data={"stream": stream, "level": current_level}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decrease volume for {stream}"
            )
            
    except Exception as e:
        logger.error(f"Volume down API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volume")
async def get_all_volumes():
    """
    获取所有音频流的音量级别
    """
    try:
        device = get_device_controller()
        volumes = {}
        
        for stream in VolumeStream:
            level = await device.get_volume(stream)
            volumes[stream.value] = level
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="All volume levels retrieved",
            data=volumes
        )
        
    except Exception as e:
        logger.error(f"Get all volumes API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streams")
async def get_audio_streams():
    """获取支持的音频流类型"""
    streams = [
        {"stream": "media", "description": "媒体音量"},
        {"stream": "notification", "description": "通知音量"},
        {"stream": "system", "description": "系统音量"},
        {"stream": "ring", "description": "铃声音量"},
        {"stream": "alarm", "description": "闹钟音量"},
        {"stream": "voice_call", "description": "通话音量"},
    ]
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Audio streams retrieved",
        data=streams
    )