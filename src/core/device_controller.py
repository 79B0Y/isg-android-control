"""
设备控制器模块
基于ADB控制器实现具体的设备操作功能
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta

from loguru import logger

from src.core.adb_controller import get_adb_controller
from src.models.requests import NavigationDirection, VolumeStream


class PowerAction(str, Enum):
    """电源操作枚举"""
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    REBOOT = "reboot"
    SCREEN_ON = "screen_on"
    SCREEN_OFF = "screen_off"


class DeviceController:
    """设备控制器类"""
    
    def __init__(self):
        self.adb = get_adb_controller()
        self._volume_cache = {}  # 缓存音量状态
        self._screen_cache = {}  # 缓存屏幕状态
        self._cache_ttl = 30  # 缓存30秒
        
        # 按键映射表
        self._keycode_map = {
            NavigationDirection.UP: "KEYCODE_DPAD_UP",
            NavigationDirection.DOWN: "KEYCODE_DPAD_DOWN", 
            NavigationDirection.LEFT: "KEYCODE_DPAD_LEFT",
            NavigationDirection.RIGHT: "KEYCODE_DPAD_RIGHT",
            NavigationDirection.CENTER: "KEYCODE_DPAD_CENTER",
            NavigationDirection.BACK: "KEYCODE_BACK",
            NavigationDirection.HOME: "KEYCODE_HOME",
            NavigationDirection.MENU: "KEYCODE_MENU",
        }
        
        # 音频流映射表
        self._volume_stream_map = {
            VolumeStream.MEDIA: "3",
            VolumeStream.NOTIFICATION: "5", 
            VolumeStream.SYSTEM: "1",
            VolumeStream.RING: "2",
            VolumeStream.ALARM: "4",
            VolumeStream.VOICE_CALL: "0",
        }
        
        logger.info("Device controller initialized")
    
    # 导航控制方法
    async def navigate(self, direction: NavigationDirection, repeat: int = 1) -> bool:
        """导航控制"""
        try:
            keycode = self._keycode_map.get(direction)
            if not keycode:
                logger.error(f"Unknown navigation direction: {direction}")
                return False
            
            success_count = 0
            for i in range(repeat):
                result = await self.adb.execute(f"input keyevent {keycode}")
                if result.success:
                    success_count += 1
                else:
                    logger.warning(f"Navigation {direction} failed on attempt {i+1}: {result.error}")
                
                # 添加小延迟避免命令过快
                if i < repeat - 1:
                    await asyncio.sleep(0.1)
            
            success = success_count == repeat
            logger.info(f"Navigation {direction} x{repeat}: {success_count}/{repeat} successful")
            return success
            
        except Exception as e:
            logger.error(f"Navigation control error: {e}")
            return False
    
    async def press_key(self, keycode: str) -> bool:
        """按下指定按键"""
        try:
            result = await self.adb.execute(f"input keyevent {keycode}")
            if result.success:
                logger.debug(f"Key press successful: {keycode}")
                return True
            else:
                logger.warning(f"Key press failed: {keycode}, error: {result.error}")
                return False
        except Exception as e:
            logger.error(f"Key press error: {e}")
            return False
    
    # 音量控制方法
    async def set_volume(self, stream: VolumeStream, level: int) -> bool:
        """设置音量级别"""
        try:
            if not 0 <= level <= 15:
                logger.error(f"Invalid volume level: {level}, must be 0-15")
                return False
            
            stream_id = self._volume_stream_map.get(stream)
            if not stream_id:
                logger.error(f"Unknown volume stream: {stream}")
                return False
            
            # 使用audio命令设置音量
            result = await self.adb.execute(f"media volume --set {level} --stream {stream_id}")
            
            # 如果media命令不可用，尝试service命令
            if not result.success:
                result = await self.adb.execute(f"service call audio 3 i32 {stream_id} i32 {level} i32 1")
            
            if result.success:
                # 更新缓存
                self._volume_cache[stream] = {
                    'level': level,
                    'timestamp': datetime.now()
                }
                logger.info(f"Volume set successfully: {stream} = {level}")
                return True
            else:
                logger.warning(f"Volume setting failed: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Volume control error: {e}")
            return False
    
    async def get_volume(self, stream: VolumeStream) -> Optional[int]:
        """获取音量级别"""
        try:
            # 检查缓存
            cache_key = stream
            if cache_key in self._volume_cache:
                cache_data = self._volume_cache[cache_key]
                if datetime.now() - cache_data['timestamp'] < timedelta(seconds=self._cache_ttl):
                    return cache_data['level']
            
            stream_id = self._volume_stream_map.get(stream)
            if not stream_id:
                return None
            
            # 获取当前音量
            result = await self.adb.execute(f"media volume --get --stream {stream_id}")
            
            if result.success:
                # 解析音量值
                try:
                    # 尝试从输出中提取数字
                    import re
                    match = re.search(r'(\d+)', result.output)
                    if match:
                        level = int(match.group(1))
                        # 更新缓存
                        self._volume_cache[stream] = {
                            'level': level,
                            'timestamp': datetime.now()
                        }
                        return level
                except ValueError:
                    pass
            
            logger.warning(f"Failed to get volume for stream {stream}")
            return None
            
        except Exception as e:
            logger.error(f"Get volume error: {e}")
            return None
    
    async def volume_up(self, stream: VolumeStream) -> bool:
        """音量增加"""
        current_level = await self.get_volume(stream)
        if current_level is not None and current_level < 15:
            return await self.set_volume(stream, current_level + 1)
        return False
    
    async def volume_down(self, stream: VolumeStream) -> bool:
        """音量降低"""
        current_level = await self.get_volume(stream)
        if current_level is not None and current_level > 0:
            return await self.set_volume(stream, current_level - 1)
        return False
    
    # 屏幕控制方法
    async def set_brightness(self, level: int) -> bool:
        """设置屏幕亮度"""
        try:
            if not 0 <= level <= 255:
                logger.error(f"Invalid brightness level: {level}, must be 0-255")
                return False
            
            # 设置系统亮度
            result = await self.adb.execute(f"settings put system screen_brightness {level}")
            
            if result.success:
                logger.info(f"Brightness set to {level}")
                return True
            else:
                logger.warning(f"Brightness setting failed: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Brightness control error: {e}")
            return False
    
    async def get_brightness(self) -> Optional[int]:
        """获取当前亮度"""
        try:
            result = await self.adb.execute("settings get system screen_brightness")
            
            if result.success:
                try:
                    brightness = int(result.output.strip())
                    return brightness
                except ValueError:
                    logger.warning(f"Invalid brightness value: {result.output}")
                    return None
            else:
                logger.warning(f"Failed to get brightness: {result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Get brightness error: {e}")
            return None
    
    async def screen_on(self) -> bool:
        """打开屏幕"""
        try:
            # 检查屏幕状态
            if await self.is_screen_on():
                logger.debug("Screen is already on")
                return True
            
            # 按电源键唤醒屏幕
            result = await self.adb.execute("input keyevent KEYCODE_WAKEUP")
            
            if result.success:
                logger.info("Screen turned on")
                return True
            else:
                logger.warning(f"Screen on failed: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Screen on error: {e}")
            return False
    
    async def screen_off(self) -> bool:
        """关闭屏幕"""
        try:
            # 按电源键关闭屏幕
            result = await self.adb.execute("input keyevent KEYCODE_SLEEP")
            
            if result.success:
                logger.info("Screen turned off")
                return True
            else:
                logger.warning(f"Screen off failed: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Screen off error: {e}")
            return False
    
    async def is_screen_on(self) -> bool:
        """检查屏幕是否开启"""
        try:
            result = await self.adb.execute("dumpsys power | grep 'Display Power'")
            
            if result.success:
                # 检查输出中是否包含ON状态
                return "state=ON" in result.output or "state=VR" in result.output
            else:
                # 如果命令失败，尝试其他方法
                result = await self.adb.execute("dumpsys deviceidle | grep mScreenOn")
                if result.success:
                    return "mScreenOn=true" in result.output
                
            return False
            
        except Exception as e:
            logger.error(f"Check screen state error: {e}")
            return False
    
    # 电源控制方法
    async def power_action(self, action: PowerAction) -> bool:
        """执行电源操作"""
        try:
            if action == PowerAction.POWER_ON:
                return await self.screen_on()
            elif action == PowerAction.POWER_OFF:
                return await self.screen_off()
            elif action == PowerAction.SCREEN_ON:
                return await self.screen_on()
            elif action == PowerAction.SCREEN_OFF:
                return await self.screen_off()
            elif action == PowerAction.REBOOT:
                result = await self.adb.execute("reboot", shell=False)
                return result.success
            else:
                logger.error(f"Unknown power action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Power action error: {e}")
            return False
    
    # 应用控制方法
    async def launch_app(self, package_name: str, activity: Optional[str] = None, force_stop_current: bool = False) -> bool:
        """启动应用"""
        try:
            # 如果需要，先停止当前应用
            if force_stop_current:
                current_activity = await self.adb.get_current_activity()
                if current_activity:
                    current_package = current_activity.split('/')[0]
                    if current_package != package_name:
                        await self.stop_app(current_package)
            
            # 构建启动命令
            if activity:
                launch_cmd = f"am start -n {package_name}/{activity}"
            else:
                # 获取主Activity
                result = await self.adb.execute(f"pm dump {package_name} | grep -A 1 'android.intent.action.MAIN'")
                if result.success and result.output:
                    import re
                    match = re.search(r'([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.]+)', result.output)
                    if match:
                        activity = match.group(2)
                        launch_cmd = f"am start -n {package_name}/{activity}"
                    else:
                        launch_cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
                else:
                    launch_cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
            
            result = await self.adb.execute(launch_cmd)
            
            if result.success:
                logger.info(f"App launched successfully: {package_name}")
                return True
            else:
                logger.warning(f"App launch failed: {package_name}, error: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Launch app error: {e}")
            return False
    
    async def stop_app(self, package_name: str, force: bool = False) -> bool:
        """停止应用"""
        try:
            if force:
                cmd = f"am force-stop {package_name}"
            else:
                cmd = f"am kill {package_name}"
            
            result = await self.adb.execute(cmd)
            
            if result.success:
                logger.info(f"App stopped successfully: {package_name}")
                return True
            else:
                logger.warning(f"App stop failed: {package_name}, error: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Stop app error: {e}")
            return False
    
    async def get_running_apps(self) -> List[Dict[str, str]]:
        """获取运行中的应用"""
        try:
            result = await self.adb.execute("ps | grep -v 'root'")
            
            if result.success:
                running_apps = []
                for line in result.output.split('\n'):
                    if line.strip():
                        # 简单解析进程信息
                        parts = line.split()
                        if len(parts) > 8:  # 确保有足够的字段
                            process_name = parts[-1]
                            if '.' in process_name and not process_name.startswith('['):
                                running_apps.append({
                                    'package_name': process_name,
                                    'app_name': process_name.split('.')[-1]
                                })
                
                logger.debug(f"Found {len(running_apps)} running apps")
                return running_apps
            else:
                logger.warning(f"Failed to get running apps: {result.error}")
                return []
                
        except Exception as e:
            logger.error(f"Get running apps error: {e}")
            return []
    
    # 系统信息方法
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            info = {}
            
            # 获取基础设备信息
            device_info = await self.adb.get_device_info()
            info.update(device_info)
            
            # 获取电池信息
            battery_info = await self._get_battery_info()
            info.update(battery_info)
            
            # 获取屏幕状态
            info['screen_on'] = await self.is_screen_on()
            
            # 获取当前亮度
            info['brightness'] = await self.get_brightness()
            
            # 获取当前Activity
            info['current_activity'] = await self.adb.get_current_activity()
            
            return info
            
        except Exception as e:
            logger.error(f"Get system info error: {e}")
            return {'error': str(e)}
    
    async def _get_battery_info(self) -> Dict[str, Any]:
        """获取电池信息"""
        try:
            result = await self.adb.execute("dumpsys battery")
            
            battery_info = {}
            if result.success:
                lines = result.output.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'level:' in line:
                        battery_info['battery_level'] = int(line.split(':')[1].strip())
                    elif 'temperature:' in line:
                        # 温度通常以1/10度为单位
                        temp = int(line.split(':')[1].strip()) / 10.0
                        battery_info['battery_temperature'] = temp
                    elif 'status:' in line:
                        battery_info['battery_status'] = line.split(':')[1].strip()
                    elif 'health:' in line:
                        battery_info['battery_health'] = line.split(':')[1].strip()
                    elif 'plugged:' in line:
                        battery_info['battery_plugged'] = line.split(':')[1].strip()
                    elif 'voltage:' in line:
                        battery_info['battery_voltage'] = int(line.split(':')[1].strip())
            
            return battery_info
            
        except Exception as e:
            logger.error(f"Get battery info error: {e}")
            return {}
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            stats = {}
            
            # CPU使用率（简化版）
            result = await self.adb.execute("top -n 1 | head -5")
            if result.success:
                lines = result.output.split('\n')
                for line in lines:
                    if '%cpu' in line.lower() or 'cpu:' in line.lower():
                        # 尝试提取CPU使用率
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)%', line)
                        if match:
                            stats['cpu_usage'] = float(match.group(1))
                            break
            
            # 内存信息
            result = await self.adb.execute("cat /proc/meminfo | head -5")
            if result.success:
                mem_total = mem_free = mem_available = 0
                for line in result.output.split('\n'):
                    if 'MemTotal:' in line:
                        mem_total = int(line.split()[1]) // 1024  # 转换为MB
                    elif 'MemFree:' in line:
                        mem_free = int(line.split()[1]) // 1024
                    elif 'MemAvailable:' in line:
                        mem_available = int(line.split()[1]) // 1024
                
                stats['memory_total'] = mem_total
                stats['memory_free'] = mem_free
                stats['memory_available'] = mem_available if mem_available else mem_free
                stats['memory_usage'] = (mem_total - stats['memory_available']) / mem_total * 100 if mem_total else 0
            
            # 存储信息
            result = await self.adb.execute("df /data | tail -1")
            if result.success:
                parts = result.output.split()
                if len(parts) >= 4:
                    try:
                        total_kb = int(parts[1])
                        used_kb = int(parts[2])
                        stats['storage_total_gb'] = total_kb // (1024 * 1024)
                        stats['storage_used_gb'] = used_kb // (1024 * 1024)
                        stats['storage_free_gb'] = stats['storage_total_gb'] - stats['storage_used_gb']
                        stats['storage_usage'] = (used_kb / total_kb) * 100 if total_kb else 0
                    except ValueError:
                        pass
            
            # 运行时间
            result = await self.adb.execute("cat /proc/uptime")
            if result.success:
                try:
                    uptime_seconds = float(result.output.split()[0])
                    stats['uptime'] = int(uptime_seconds)
                except (ValueError, IndexError):
                    pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Get performance stats error: {e}")
            return {}


# 全局设备控制器实例
_device_controller_instance: Optional[DeviceController] = None


def get_device_controller() -> DeviceController:
    """获取设备控制器实例（单例）"""
    global _device_controller_instance
    if _device_controller_instance is None:
        _device_controller_instance = DeviceController()
    return _device_controller_instance