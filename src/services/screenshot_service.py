"""
截图服务模块
管理屏幕截图的捕获、存储和管理
"""

import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import glob

from PIL import Image
from loguru import logger
import aiofiles

from src.core.adb_controller import get_adb_controller
from src.core.config import get_settings


class ScreenshotService:
    """截图服务类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.adb = get_adb_controller()
        
        # 截图配置
        self.quality = self.settings.screenshot.quality
        self.format = self.settings.screenshot.format
        self.max_files = self.settings.screenshot.max_files
        self.storage_path = Path(self.settings.screenshot.storage_path)
        self.auto_cleanup = self.settings.screenshot.auto_cleanup
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Screenshot service initialized, storage: {self.storage_path}")
    
    async def capture_screenshot(self, quality: Optional[int] = None, 
                               format: Optional[str] = None,
                               filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        捕获屏幕截图
        
        Args:
            quality: 图片质量 1-100，默认使用配置值
            format: 图片格式 JPEG/PNG，默认使用配置值
            filename: 自定义文件名，默认使用时间戳
            
        Returns:
            截图信息字典，包含文件路径、大小、尺寸等信息
        """
        try:
            # 使用参数或配置中的默认值
            quality = quality or self.quality
            format = format or self.format
            
            # 获取原始截图数据
            screenshot_data = await self.adb.screenshot()
            if not screenshot_data:
                logger.error("Failed to capture screenshot from device")
                return None
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}"
            
            # 确保文件扩展名正确
            if format.upper() == "JPEG" or format.upper() == "JPG":
                file_ext = ".jpg"
            elif format.upper() == "PNG":
                file_ext = ".png"
            else:
                file_ext = ".jpg"
                format = "JPEG"
            
            if not filename.endswith(file_ext):
                filename = filename + file_ext
            
            file_path = self.storage_path / filename
            
            # 处理图片
            processed_data = await self._process_screenshot(screenshot_data, quality, format)
            if not processed_data:
                return None
            
            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(processed_data)
            
            # 获取图片信息
            with Image.open(file_path) as img:
                width, height = img.size
                file_size = os.path.getsize(file_path)
            
            # 自动清理旧文件
            if self.auto_cleanup:
                await self._cleanup_old_screenshots()
            
            screenshot_info = {
                "filename": filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "width": width,
                "height": height,
                "format": format,
                "quality": quality,
                "created_at": datetime.now()
            }
            
            logger.info(f"Screenshot captured successfully: {filename} ({file_size} bytes, {width}x{height})")
            return screenshot_info
            
        except Exception as e:
            logger.error(f"Screenshot capture error: {e}")
            return None
    
    async def _process_screenshot(self, screenshot_data: bytes, quality: int, format: str) -> Optional[bytes]:
        """处理截图数据（压缩、格式转换等）"""
        try:
            # 使用PIL处理图片
            import io
            
            # 将字节数据转换为图片对象
            img = Image.open(io.BytesIO(screenshot_data))
            
            # 转换为RGB模式（JPEG需要）
            if format.upper() == "JPEG" and img.mode != "RGB":
                img = img.convert("RGB")
            
            # 保存为指定格式和质量
            output = io.BytesIO()
            if format.upper() in ["JPEG", "JPG"]:
                img.save(output, format="JPEG", quality=quality, optimize=True)
            elif format.upper() == "PNG":
                # PNG不支持quality参数，使用optimize
                img.save(output, format="PNG", optimize=True)
            
            processed_data = output.getvalue()
            output.close()
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Screenshot processing error: {e}")
            return None
    
    async def _cleanup_old_screenshots(self):
        """清理旧的截图文件"""
        try:
            # 获取所有截图文件
            screenshot_files = []
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                pattern = str(self.storage_path / ext)
                screenshot_files.extend(glob.glob(pattern))
            
            # 按修改时间排序
            screenshot_files.sort(key=os.path.getmtime, reverse=True)
            
            # 删除超出最大数量的文件
            if len(screenshot_files) > self.max_files:
                files_to_delete = screenshot_files[self.max_files:]
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                        logger.debug(f"Deleted old screenshot: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete screenshot {file_path}: {e}")
                
                logger.info(f"Cleaned up {len(files_to_delete)} old screenshots")
            
        except Exception as e:
            logger.error(f"Screenshot cleanup error: {e}")
    
    async def get_screenshot_list(self) -> List[Dict[str, Any]]:
        """获取截图文件列表"""
        try:
            screenshot_files = []
            
            # 查找所有截图文件
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                pattern = str(self.storage_path / ext)
                files = glob.glob(pattern)
                screenshot_files.extend(files)
            
            # 按修改时间排序（最新在前）
            screenshot_files.sort(key=os.path.getmtime, reverse=True)
            
            # 构建文件信息列表
            file_list = []
            for file_path in screenshot_files:
                try:
                    stat = os.stat(file_path)
                    
                    # 获取图片尺寸
                    try:
                        with Image.open(file_path) as img:
                            width, height = img.size
                            format = img.format
                    except Exception:
                        width = height = 0
                        format = "unknown"
                    
                    file_info = {
                        "filename": os.path.basename(file_path),
                        "file_path": file_path,
                        "file_size": stat.st_size,
                        "width": width,
                        "height": height,
                        "format": format,
                        "created_at": datetime.fromtimestamp(stat.st_mtime)
                    }
                    file_list.append(file_info)
                    
                except OSError as e:
                    logger.warning(f"Failed to get info for screenshot {file_path}: {e}")
                    continue
            
            logger.debug(f"Found {len(file_list)} screenshots")
            return file_list
            
        except Exception as e:
            logger.error(f"Get screenshot list error: {e}")
            return []
    
    async def get_latest_screenshot(self) -> Optional[Dict[str, Any]]:
        """获取最新的截图"""
        screenshot_list = await self.get_screenshot_list()
        return screenshot_list[0] if screenshot_list else None
    
    async def get_screenshot_as_base64(self, filename: str) -> Optional[str]:
        """获取截图的Base64编码（用于MQTT传输）"""
        try:
            file_path = self.storage_path / filename
            if not file_path.exists():
                logger.warning(f"Screenshot file not found: {filename}")
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                image_data = await f.read()
            
            # 编码为Base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            logger.debug(f"Screenshot {filename} encoded to base64, size: {len(base64_data)} chars")
            
            return base64_data
            
        except Exception as e:
            logger.error(f"Get screenshot base64 error: {e}")
            return None
    
    async def delete_screenshot(self, filename: str) -> bool:
        """删除指定的截图文件"""
        try:
            file_path = self.storage_path / filename
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Screenshot deleted: {filename}")
                return True
            else:
                logger.warning(f"Screenshot file not found: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Delete screenshot error: {e}")
            return False
    
    async def clear_all_screenshots(self) -> int:
        """清除所有截图文件"""
        try:
            screenshot_list = await self.get_screenshot_list()
            deleted_count = 0
            
            for screenshot_info in screenshot_list:
                try:
                    os.remove(screenshot_info["file_path"])
                    deleted_count += 1
                except OSError as e:
                    logger.warning(f"Failed to delete {screenshot_info['filename']}: {e}")
            
            logger.info(f"Cleared {deleted_count} screenshots")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Clear screenshots error: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取截图存储统计信息"""
        try:
            screenshot_list = await self.get_screenshot_list()
            
            total_size = sum(info["file_size"] for info in screenshot_list)
            total_count = len(screenshot_list)
            
            # 按格式统计
            format_stats = {}
            for info in screenshot_list:
                format_name = info["format"]
                if format_name not in format_stats:
                    format_stats[format_name] = {"count": 0, "size": 0}
                format_stats[format_name]["count"] += 1
                format_stats[format_name]["size"] += info["file_size"]
            
            storage_stats = {
                "total_count": total_count,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_files": self.max_files,
                "storage_path": str(self.storage_path),
                "format_stats": format_stats
            }
            
            return storage_stats
            
        except Exception as e:
            logger.error(f"Get storage stats error: {e}")
            return {}


# 全局截图服务实例
_screenshot_service_instance: Optional[ScreenshotService] = None


def get_screenshot_service() -> ScreenshotService:
    """获取截图服务实例（单例）"""
    global _screenshot_service_instance
    if _screenshot_service_instance is None:
        _screenshot_service_instance = ScreenshotService()
    return _screenshot_service_instance