"""
应用管理API路由
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from src.core.device_controller import get_device_controller
from src.core.adb_controller import get_adb_controller
from src.models.requests import AppLaunchRequest, AppStopRequest
from src.models.responses import BaseResponse, ResponseStatus, AppInfo

router = APIRouter()


@router.get("/installed", response_model=BaseResponse[List[AppInfo]])
async def get_installed_apps(include_system: bool = Query(False, description="是否包含系统应用")):
    """
    获取已安装应用列表
    
    - **include_system**: 是否包含系统应用 (默认false)
    """
    try:
        adb = get_adb_controller()
        packages = await adb.get_installed_packages(include_system=include_system)
        
        # 转换为AppInfo格式
        apps = []
        for pkg in packages:
            app_info = AppInfo(
                package_name=pkg["package_name"],
                app_name=pkg["app_name"],
                version_name=None,  # 简化版，不获取详细版本信息
                version_code=None,
                is_system=False,  # 这里简化处理
                is_enabled=True,
                install_time=None
            )
            apps.append(app_info)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(apps)} installed apps",
            data=apps
        )
        
    except Exception as e:
        logger.error(f"Get installed apps API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/launch")
async def launch_app(request: AppLaunchRequest):
    """
    启动应用
    
    - **package_name**: 包名 (可选，与app_name二选一)
    - **app_name**: 应用名称 (可选，与package_name二选一)
    - **activity**: Activity名称 (可选)
    - **force_stop_current**: 是否强制停止当前应用 (默认false)
    """
    try:
        device = get_device_controller()
        
        # 确定包名
        package_name = request.package_name
        if not package_name and request.app_name:
            # 从配置中查找包名映射
            from src.core.config import get_settings
            settings = get_settings()
            app_name_lower = request.app_name.lower().replace(' ', '_')
            package_name = settings.apps.get(app_name_lower)
            
            if not package_name:
                # 简单的名称匹配（这里可以扩展更复杂的匹配逻辑）
                common_apps = {
                    "youtube": "com.google.android.youtube.tv",
                    "youtube_tv": "com.google.android.youtube.tv",
                    "spotify": "com.spotify.music",
                    "netflix": "com.netflix.mediaclient",
                    "disney": "com.disney.disneyplus",
                    "amazon": "com.amazon.avod.thirdpartyclient"
                }
                package_name = common_apps.get(app_name_lower)
        
        if not package_name:
            raise HTTPException(
                status_code=400,
                detail="Could not determine package name from provided information"
            )
        
        success = await device.launch_app(
            package_name=package_name,
            activity=request.activity,
            force_stop_current=request.force_stop_current
        )
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"App launched successfully",
                data={
                    "package_name": package_name,
                    "app_name": request.app_name,
                    "activity": request.activity
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to launch app: {package_name}"
            )
            
    except Exception as e:
        logger.error(f"Launch app API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_app(request: AppStopRequest):
    """
    停止应用
    
    - **package_name**: 要停止的应用包名
    - **force**: 是否强制停止 (默认false)
    """
    try:
        device = get_device_controller()
        success = await device.stop_app(request.package_name, request.force)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"App stopped successfully",
                data={"package_name": request.package_name, "force": request.force}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop app: {request.package_name}"
            )
            
    except Exception as e:
        logger.error(f"Stop app API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
async def get_current_app():
    """获取当前前台应用"""
    try:
        adb = get_adb_controller()
        current_activity = await adb.get_current_activity()
        
        logger.info(f"DEBUG: get_current_activity returned: {current_activity}")
        
        if current_activity:
            package_name = current_activity.split('/')[0] if '/' in current_activity else current_activity
            activity_name = current_activity.split('/')[1] if '/' in current_activity else ""
            
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Current app retrieved",
                data={
                    "package_name": package_name,
                    "activity": activity_name,
                    "full_activity": current_activity
                }
            )
        else:
            return BaseResponse(
                status=ResponseStatus.WARNING,
                message=f"No current app found (returned: {current_activity})",
                data=None
            )
            
    except Exception as e:
        logger.error(f"Get current app API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/running")
async def get_running_apps():
    """获取正在运行的应用列表"""
    try:
        device = get_device_controller()
        running_apps = await device.get_running_apps()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(running_apps)} running apps",
            data=running_apps
        )
        
    except Exception as e:
        logger.error(f"Get running apps API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shortcuts")
async def get_app_shortcuts():
    """获取常用应用快捷方式配置"""
    from src.core.config import get_settings
    settings = get_settings()
    
    shortcuts = []
    for app_key, package_name in settings.apps.items():
        app_name = app_key.replace('_', ' ').title()
        shortcuts.append({
            "key": app_key,
            "name": app_name,
            "package_name": package_name
        })
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="App shortcuts retrieved",
        data=shortcuts
    )


@router.post("/launch/{app_key}")
async def launch_app_shortcut(app_key: str):
    """
    通过快捷方式启动应用
    
    - **app_key**: 应用快捷键 (如: youtube_tv, spotify, netflix)
    """
    try:
        from src.core.config import get_settings
        settings = get_settings()
        
        package_name = settings.apps.get(app_key)
        if not package_name:
            raise HTTPException(
                status_code=404,
                detail=f"App shortcut not found: {app_key}"
            )
        
        device = get_device_controller()
        success = await device.launch_app(package_name=package_name)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message=f"App {app_key} launched successfully",
                data={"app_key": app_key, "package_name": package_name}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to launch app: {app_key}"
            )
            
    except Exception as e:
        logger.error(f"Launch app shortcut API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))