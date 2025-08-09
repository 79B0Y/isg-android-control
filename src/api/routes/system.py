"""
系统监控API路由
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.core.device_controller import get_device_controller
from src.core.adb_controller import get_adb_controller
from src.models.responses import BaseResponse, ResponseStatus, DeviceInfo, SystemPerformance

router = APIRouter()


@router.get("/info", response_model=BaseResponse[DeviceInfo])
async def get_device_info():
    """获取设备基础信息"""
    try:
        adb = get_adb_controller()
        device_info = await adb.get_device_info()
        
        # 检查连接状态
        is_connected = await adb.check_connection()
        
        # 构建DeviceInfo对象
        info = DeviceInfo(
            serial=device_info.get("serial", "unknown"),
            model=device_info.get("model", "unknown"),
            android_version=device_info.get("android_version", "unknown"),
            api_level=device_info.get("api_level", 0),
            battery_level=None,  # 需要从性能统计中获取
            screen_resolution=device_info.get("resolution", "unknown"),
            is_connected=is_connected
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Device info retrieved successfully",
            data=info
        )
        
    except Exception as e:
        logger.error(f"Get device info API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=BaseResponse[SystemPerformance])
async def get_system_performance():
    """获取系统性能统计"""
    try:
        device = get_device_controller()
        
        # 获取性能统计
        perf_stats = await device.get_performance_stats()
        
        # 获取系统信息（包含电池信息）
        system_info = await device.get_system_info()
        
        # 构建SystemPerformance对象
        performance = SystemPerformance(
            cpu_usage=perf_stats.get("cpu_usage", 0.0),
            memory_usage=perf_stats.get("memory_usage", 0.0),
            memory_total=perf_stats.get("memory_total", 0),
            memory_available=perf_stats.get("memory_available", 0),
            storage_usage=perf_stats.get("storage_usage", 0.0),
            storage_total=perf_stats.get("storage_total_gb", 0),
            storage_free=perf_stats.get("storage_free_gb", 0),
            battery_level=system_info.get("battery_level", 0),
            battery_temperature=system_info.get("battery_temperature", 0.0),
            uptime=perf_stats.get("uptime", 0)
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="System performance retrieved successfully",
            data=performance
        )
        
    except Exception as e:
        logger.error(f"Get system performance API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/battery")
async def get_battery_info():
    """获取电池信息"""
    try:
        device = get_device_controller()
        system_info = await device.get_system_info()
        
        battery_info = {
            key: value for key, value in system_info.items()
            if key.startswith("battery_")
        }
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Battery info retrieved successfully",
            data=battery_info
        )
        
    except Exception as e:
        logger.error(f"Get battery info API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status():
    """获取系统综合状态"""
    try:
        device = get_device_controller()
        adb = get_adb_controller()
        
        # 获取各种状态信息
        system_info = await device.get_system_info()
        is_connected = await adb.check_connection()
        current_activity = await adb.get_current_activity()
        
        status = {
            "device_connected": is_connected,
            "screen_on": system_info.get("screen_on", False),
            "brightness": system_info.get("brightness"),
            "battery_level": system_info.get("battery_level"),
            "battery_status": system_info.get("battery_status"),
            "current_app": current_activity,
            "android_version": system_info.get("android_version"),
            "model": system_info.get("model")
        }
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="System status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Get system status API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uptime")
async def get_system_uptime():
    """获取系统运行时间"""
    try:
        device = get_device_controller()
        perf_stats = await device.get_performance_stats()
        
        uptime_seconds = perf_stats.get("uptime", 0)
        
        # 转换为可读格式
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        uptime_info = {
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s",
            "days": int(days),
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds)
        }
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="System uptime retrieved successfully",
            data=uptime_info
        )
        
    except Exception as e:
        logger.error(f"Get system uptime API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reboot")
async def reboot_device():
    """重启设备"""
    try:
        device = get_device_controller()
        success = await device.power_action(device.PowerAction.REBOOT)
        
        if success:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="Device reboot initiated",
                data={"action": "reboot"}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initiate device reboot"
            )
            
    except Exception as e:
        logger.error(f"Reboot device API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes")
async def get_running_processes():
    """获取运行中的进程"""
    try:
        adb = get_adb_controller()
        result = await adb.execute("ps aux")
        
        processes = []
        if result.success:
            lines = result.output.split('\n')[1:]  # 跳过表头
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "name": parts[-1]
                        })
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(processes)} running processes",
            data=processes[:50]  # 限制返回数量
        )
        
    except Exception as e:
        logger.error(f"Get processes API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))