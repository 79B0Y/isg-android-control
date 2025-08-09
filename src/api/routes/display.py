"""
显示控制API路由
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.core.device_controller import get_device_controller, PowerAction
from src.models.requests import BrightnessRequest, ScreenRequest
from src.models.responses import BaseResponse, ResponseStatus

router = APIRouter()


@router.post("/brightness")
async def set_brightness(request: BrightnessRequest):
    """
    设置屏幕亮度
    
    - **level**: 亮度级别 (0-255)
    """
    try:
        device = get_device_controller()
        success = await device.set_brightness(request.level)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Brightness set to {request.level}",
                data={"level": request.level}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set brightness to {request.level}"
            )
            
    except Exception as e:
        logger.error(f"Set brightness API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brightness")
async def get_brightness():
    """获取当前屏幕亮度"""
    try:
        device = get_device_controller()
        level = await device.get_brightness()
        
        if level is not None:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Brightness level retrieved",
                data={"level": level}
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Could not retrieve brightness level"
            )
            
    except Exception as e:
        logger.error(f"Get brightness API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen")
async def control_screen(request: ScreenRequest):
    """
    屏幕开关控制
    
    - **action**: 屏幕操作 (on, off, toggle)
    """
    try:
        device = get_device_controller()
        
        if request.action == "on":
            success = await device.power_action(PowerAction.SCREEN_ON)
            action_desc = "turned on"
        elif request.action == "off":
            success = await device.power_action(PowerAction.SCREEN_OFF)
            action_desc = "turned off"
        elif request.action == "toggle":
            # 检查当前状态并切换
            is_on = await device.is_screen_on()
            if is_on:
                success = await device.power_action(PowerAction.SCREEN_OFF)
                action_desc = "turned off"
            else:
                success = await device.power_action(PowerAction.SCREEN_ON)
                action_desc = "turned on"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid action. Must be 'on', 'off', or 'toggle'"
            )
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Screen {action_desc}",
                data={"action": request.action, "result": action_desc}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to {request.action} screen"
            )
            
    except Exception as e:
        logger.error(f"Screen control API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screen/status")
async def get_screen_status():
    """获取屏幕状态"""
    try:
        device = get_device_controller()
        is_on = await device.is_screen_on()
        brightness = await device.get_brightness()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Screen status retrieved",
            data={
                "screen_on": is_on,
                "brightness": brightness
            }
        )
        
    except Exception as e:
        logger.error(f"Get screen status API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen/on")
async def screen_on():
    """打开屏幕"""
    try:
        device = get_device_controller()
        success = await device.power_action(PowerAction.SCREEN_ON)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Screen turned on",
                data={"screen_on": True}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to turn on screen"
            )
            
    except Exception as e:
        logger.error(f"Screen on API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen/off")
async def screen_off():
    """关闭屏幕"""
    try:
        device = get_device_controller()
        success = await device.power_action(PowerAction.SCREEN_OFF)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Screen turned off",
                data={"screen_on": False}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to turn off screen"
            )
            
    except Exception as e:
        logger.error(f"Screen off API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))