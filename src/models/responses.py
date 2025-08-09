"""
API响应数据模型
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


T = TypeVar('T')


class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    status: ResponseStatus = Field(description="响应状态")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: str = Field(description="错误代码")
    error_message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now)


class DeviceInfo(BaseModel):
    """设备信息模型"""
    serial: str = Field(description="设备序列号")
    model: str = Field(description="设备型号")
    android_version: str = Field(description="Android版本")
    api_level: int = Field(description="API级别")
    battery_level: Optional[int] = Field(description="电池电量")
    screen_resolution: str = Field(description="屏幕分辨率")
    is_connected: bool = Field(description="是否已连接")


class SystemPerformance(BaseModel):
    """系统性能模型"""
    cpu_usage: float = Field(description="CPU使用率百分比")
    memory_usage: float = Field(description="内存使用率百分比")
    memory_total: int = Field(description="总内存MB")
    memory_available: int = Field(description="可用内存MB")
    storage_usage: float = Field(description="存储使用率百分比")
    storage_total: int = Field(description="总存储GB")
    storage_free: int = Field(description="可用存储GB")
    battery_level: int = Field(description="电池电量百分比")
    battery_temperature: float = Field(description="电池温度摄氏度")
    uptime: int = Field(description="系统运行时间秒")


class AppInfo(BaseModel):
    """应用信息模型"""
    package_name: str = Field(description="包名")
    app_name: str = Field(description="应用名称")
    version_name: Optional[str] = Field(description="版本名称")
    version_code: Optional[int] = Field(description="版本代码")
    is_system: bool = Field(description="是否系统应用")
    is_enabled: bool = Field(description="是否已启用")
    install_time: Optional[datetime] = Field(description="安装时间")


class ScreenshotInfo(BaseModel):
    """截图信息模型"""
    filename: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小字节")
    width: int = Field(description="图片宽度")
    height: int = Field(description="图片高度")
    format: str = Field(description="图片格式")
    quality: int = Field(description="压缩质量")
    created_at: datetime = Field(description="创建时间")


class NetworkStatus(BaseModel):
    """网络状态模型"""
    interface: str = Field(description="网络接口")
    ip_address: Optional[str] = Field(description="IP地址")
    netmask: Optional[str] = Field(description="子网掩码")
    gateway: Optional[str] = Field(description="网关")
    dns_servers: List[str] = Field(description="DNS服务器列表")
    is_connected: bool = Field(description="是否已连接")
    connection_type: str = Field(description="连接类型")
    signal_strength: Optional[int] = Field(description="信号强度")
    bytes_sent: int = Field(description="发送字节数")
    bytes_received: int = Field(description="接收字节数")