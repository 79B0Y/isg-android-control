"""
ADB控制器模块
管理ADB连接和命令执行
"""

import asyncio
import json
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from loguru import logger

from src.core.config import get_settings


@dataclass
class ADBResult:
    """ADB命令执行结果"""
    success: bool
    output: str
    error: str
    exit_code: int
    duration: float
    command: str


class ADBConnectionPool:
    """ADB连接池管理"""
    
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.active_connections = 0
        self._connection_lock = asyncio.Semaphore(max_connections)
        self._connection_check_interval = 30  # 秒
        self._last_connection_check = datetime.now()
    
    async def acquire(self):
        """获取连接"""
        await self._connection_lock.acquire()
        self.active_connections += 1
        logger.debug(f"ADB connection acquired, active: {self.active_connections}")
    
    def release(self):
        """释放连接"""
        self.active_connections -= 1
        self._connection_lock.release()
        logger.debug(f"ADB connection released, active: {self.active_connections}")


class ADBController:
    """ADB控制器类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.device_serial = self.settings.adb.device_serial
        self.timeout = self.settings.adb.timeout
        self.retry_attempts = self.settings.adb.retry_attempts
        self.retry_delay = self.settings.adb.retry_delay
        self.connection_timeout = self.settings.adb.connection_timeout
        
        self._connection_pool = ADBConnectionPool()
        self._device_info_cache = None
        self._cache_expiry = None
        self._cache_ttl = 60  # 缓存60秒
        
        logger.info(f"ADB Controller initialized for device: {self.device_serial}")
    
    async def execute(self, command: str, shell: bool = True, timeout: Optional[int] = None) -> ADBResult:
        """执行ADB命令"""
        start_time = datetime.now()
        timeout = timeout or self.timeout
        
        # 构建完整命令
        if shell:
            full_command = f"adb -s {self.device_serial} shell {command}"
        else:
            full_command = f"adb -s {self.device_serial} {command}"
        
        logger.debug(f"Executing ADB command: {full_command}")
        
        # 获取连接
        await self._connection_pool.acquire()
        
        try:
            # 执行命令
            result = await self._execute_with_retry(full_command, timeout)
            
            # 计算执行时间
            duration = (datetime.now() - start_time).total_seconds()
            
            # 记录日志
            from src.core.logger import log_adb_command
            log_adb_command(command, result.success, duration, result.output)
            
            return result
            
        finally:
            self._connection_pool.release()
    
    async def _execute_with_retry(self, command: str, timeout: int) -> ADBResult:
        """带重试的命令执行"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # 执行命令
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    limit=1024 * 1024  # 1MB buffer limit
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=timeout
                    )
                    
                    # 解码输出
                    output = stdout.decode('utf-8', errors='ignore').strip()
                    error = stderr.decode('utf-8', errors='ignore').strip()
                    
                    result = ADBResult(
                        success=process.returncode == 0,
                        output=output,
                        error=error,
                        exit_code=process.returncode,
                        duration=0,  # 将在外层计算
                        command=command
                    )
                    
                    if result.success or attempt == self.retry_attempts - 1:
                        return result
                    
                    logger.warning(f"ADB command failed (attempt {attempt + 1}): {error}")
                    last_error = error
                    
                except asyncio.TimeoutError:
                    # 超时，终止进程
                    try:
                        process.terminate()
                        await process.wait()
                    except:
                        pass
                    
                    error_msg = f"Command timeout after {timeout}s"
                    logger.warning(f"ADB command timeout (attempt {attempt + 1}): {command}")
                    last_error = error_msg
                    
                    if attempt == self.retry_attempts - 1:
                        return ADBResult(
                            success=False,
                            output="",
                            error=error_msg,
                            exit_code=-1,
                            duration=0,
                            command=command
                        )
                
            except Exception as e:
                error_msg = f"Command execution error: {str(e)}"
                logger.error(f"ADB command error (attempt {attempt + 1}): {error_msg}")
                last_error = error_msg
                
                if attempt == self.retry_attempts - 1:
                    return ADBResult(
                        success=False,
                        output="",
                        error=error_msg,
                        exit_code=-1,
                        duration=0,
                        command=command
                    )
            
            # 重试延迟
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数退避
        
        # 所有重试都失败
        return ADBResult(
            success=False,
            output="",
            error=last_error or "All retry attempts failed",
            exit_code=-1,
            duration=0,
            command=command
        )
    
    async def check_connection(self) -> bool:
        """检查设备连接状态"""
        try:
            result = await self.execute("echo 'connection_test'", timeout=5)
            if result.success and "connection_test" in result.output:
                logger.debug("ADB connection check: OK")
                return True
            else:
                logger.warning("ADB connection check failed")
                return False
        except Exception as e:
            logger.error(f"ADB connection check error: {e}")
            return False
    
    async def connect_device(self) -> bool:
        """连接到设备"""
        try:
            # 如果是TCP连接，先尝试连接
            if ":" in self.device_serial:
                result = await self.execute(f"connect {self.device_serial}", shell=False)
                if not result.success:
                    logger.error(f"Failed to connect to device: {result.error}")
                    return False
            
            # 检查设备是否在线
            result = await self.execute("devices", shell=False)
            if result.success and self.device_serial in result.output:
                logger.info(f"Device {self.device_serial} connected successfully")
                return True
            else:
                logger.error(f"Device {self.device_serial} not found in device list")
                return False
                
        except Exception as e:
            logger.error(f"Device connection error: {e}")
            return False
    
    async def get_device_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """获取设备信息（带缓存）"""
        # 检查缓存
        if not force_refresh and self._device_info_cache and self._cache_expiry:
            if datetime.now() < self._cache_expiry:
                return self._device_info_cache
        
        try:
            device_info = {}
            
            # 获取基本信息
            commands = {
                "serial": "getprop ro.serialno",
                "model": "getprop ro.product.model",
                "brand": "getprop ro.product.brand",
                "android_version": "getprop ro.build.version.release",
                "api_level": "getprop ro.build.version.sdk",
                "build_id": "getprop ro.build.id",
                "resolution": "wm size",
                "density": "wm density",
            }
            
            for key, cmd in commands.items():
                result = await self.execute(cmd)
                if result.success:
                    device_info[key] = result.output.strip()
                else:
                    device_info[key] = "unknown"
            
            # 解析分辨率
            if "Physical size:" in device_info["resolution"]:
                resolution_match = re.search(r'Physical size: (\d+x\d+)', device_info["resolution"])
                if resolution_match:
                    device_info["resolution"] = resolution_match.group(1)
            
            # 解析密度
            if "Physical density:" in device_info["density"]:
                density_match = re.search(r'Physical density: (\d+)', device_info["density"])
                if density_match:
                    device_info["density"] = int(density_match.group(1))
            
            # 转换API级别为整数
            try:
                device_info["api_level"] = int(device_info["api_level"])
            except (ValueError, TypeError):
                device_info["api_level"] = 0
            
            # 缓存结果
            self._device_info_cache = device_info
            self._cache_expiry = datetime.now() + timedelta(seconds=self._cache_ttl)
            
            logger.debug(f"Device info updated: {device_info}")
            return device_info
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {"error": str(e)}
    
    async def get_current_activity(self) -> Optional[str]:
        """获取当前Activity"""
        try:
            result = await self.execute("dumpsys activity | grep -E 'mFocusedActivity|mResumedActivity'")
            if result.success:
                # 解析Activity信息
                lines = result.output.split('\n')
                for line in lines:
                    if 'mResumedActivity' in line or 'mFocusedActivity' in line:
                        # 提取包名和Activity名
                        match = re.search(r'([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.]+)', line)
                        if match:
                            return f"{match.group(1)}/{match.group(2)}"
            return None
        except Exception as e:
            logger.error(f"Failed to get current activity: {e}")
            return None
    
    async def screenshot(self, quality: int = 80) -> Optional[bytes]:
        """截取屏幕截图"""
        try:
            # 使用screencap命令
            result = await self.execute("screencap -p", shell=True, timeout=30)
            
            if result.success and result.output:
                # ADB shell输出可能包含CRLF，需要处理
                screenshot_data = result.output.encode('latin1')  # 保持原始字节
                
                # 检查是否是有效的PNG数据
                if screenshot_data.startswith(b'\x89PNG'):
                    logger.debug(f"Screenshot captured successfully, size: {len(screenshot_data)} bytes")
                    return screenshot_data
                else:
                    logger.error("Invalid screenshot data format")
                    return None
            else:
                logger.error(f"Screenshot failed: {result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    async def get_installed_packages(self, include_system: bool = False) -> List[Dict[str, str]]:
        """获取已安装应用包列表"""
        try:
            # 获取包名列表
            if include_system:
                cmd = "pm list packages"
            else:
                cmd = "pm list packages -3"  # 只显示第三方应用
            
            result = await self.execute(cmd)
            if not result.success:
                return []
            
            packages = []
            package_names = []
            
            # 解析包名
            for line in result.output.split('\n'):
                if line.startswith('package:'):
                    package_name = line.replace('package:', '').strip()
                    package_names.append(package_name)
            
            # 获取包的详细信息
            for package_name in package_names[:50]:  # 限制数量避免超时
                try:
                    info_result = await self.execute(f"dumpsys package {package_name} | head -20")
                    if info_result.success:
                        app_info = {"package_name": package_name, "app_name": package_name}
                        
                        # 尝试获取应用名称
                        label_result = await self.execute(f"pm list packages -f {package_name}")
                        if label_result.success:
                            # 解析应用标签，这里简化处理
                            app_info["app_name"] = package_name.split('.')[-1].replace('_', ' ').title()
                        
                        packages.append(app_info)
                except Exception as e:
                    logger.debug(f"Failed to get info for package {package_name}: {e}")
                    continue
            
            logger.debug(f"Found {len(packages)} packages")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return []
    
    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up ADB controller resources")
        # 这里可以添加清理逻辑，比如关闭连接等


# 全局ADB控制器实例
_adb_controller_instance: Optional[ADBController] = None


def get_adb_controller() -> ADBController:
    """获取ADB控制器实例（单例）"""
    global _adb_controller_instance
    if _adb_controller_instance is None:
        _adb_controller_instance = ADBController()
    return _adb_controller_instance