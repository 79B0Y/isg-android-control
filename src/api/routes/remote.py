"""
遥控导航API路由
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.core.device_controller import get_device_controller
from src.models.requests import NavigationRequest, NavigationDirection
from src.models.responses import BaseResponse, ResponseStatus

router = APIRouter()


@router.post("/navigate/{direction}")
async def navigate(direction: NavigationDirection, request: NavigationRequest = None):
    """
    导航控制
    
    - **direction**: 导航方向 (up, down, left, right, center, back, home, menu)
    - **repeat**: 重复次数 (1-10次，默认1次)
    """
    try:
        device = get_device_controller()
        
        repeat = 1
        if request:
            repeat = request.repeat
        
        success = await device.navigate(direction, repeat)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Navigation {direction} executed successfully",
                data={"direction": direction, "repeat": repeat}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Navigation {direction} failed"
            )
            
    except Exception as e:
        logger.error(f"Navigation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/navigate")
async def navigate_with_body(request: NavigationRequest):
    """
    导航控制（使用请求体）
    """
    return await navigate(request.direction, request)


@router.post("/key/{keycode}")
async def press_key(keycode: str):
    """
    按键控制
    
    - **keycode**: Android按键代码 (如: KEYCODE_VOLUME_UP, KEYCODE_POWER)
    """
    try:
        device = get_device_controller()
        success = await device.press_key(keycode)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Key {keycode} pressed successfully",
                data={"keycode": keycode}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Key press {keycode} failed"
            )
            
    except Exception as e:
        logger.error(f"Key press API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys")
async def get_supported_keys():
    """获取支持的按键列表"""
    keys = [
        {"key": "KEYCODE_DPAD_UP", "description": "方向键上"},
        {"key": "KEYCODE_DPAD_DOWN", "description": "方向键下"},
        {"key": "KEYCODE_DPAD_LEFT", "description": "方向键左"},
        {"key": "KEYCODE_DPAD_RIGHT", "description": "方向键右"},
        {"key": "KEYCODE_DPAD_CENTER", "description": "确认键"},
        {"key": "KEYCODE_BACK", "description": "返回键"},
        {"key": "KEYCODE_HOME", "description": "主页键"},
        {"key": "KEYCODE_MENU", "description": "菜单键"},
        {"key": "KEYCODE_POWER", "description": "电源键"},
        {"key": "KEYCODE_VOLUME_UP", "description": "音量增加"},
        {"key": "KEYCODE_VOLUME_DOWN", "description": "音量降低"},
        {"key": "KEYCODE_WAKEUP", "description": "唤醒"},
        {"key": "KEYCODE_SLEEP", "description": "休眠"},
    ]
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Supported keys retrieved",
        data=keys
    )