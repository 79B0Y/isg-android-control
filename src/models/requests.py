"""
API请求数据模型
"""

from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator


class NavigationDirection(str, Enum):
    """导航方向枚举"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    BACK = "back"
    HOME = "home"
    MENU = "menu"


class VolumeStream(str, Enum):
    """音频流类型枚举"""
    MEDIA = "media"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    RING = "ring"
    ALARM = "alarm"
    VOICE_CALL = "voice_call"


class NavigationRequest(BaseModel):
    """导航请求模型"""
    direction: NavigationDirection = Field(description="导航方向")
    repeat: int = Field(default=1, ge=1, le=10, description="重复次数")


class VolumeRequest(BaseModel):
    """音量控制请求模型"""
    stream: VolumeStream = Field(description="音频流类型")
    level: int = Field(ge=0, le=15, description="音量级别 0-15")
    
    @validator('level')
    def validate_level(cls, v):
        if not 0 <= v <= 15:
            raise ValueError('Volume level must be between 0 and 15')
        return v


class BrightnessRequest(BaseModel):
    """亮度控制请求模型"""
    level: int = Field(ge=0, le=255, description="亮度级别 0-255")
    
    @validator('level')
    def validate_level(cls, v):
        if not 0 <= v <= 255:
            raise ValueError('Brightness level must be between 0 and 255')
        return v


class ScreenRequest(BaseModel):
    """屏幕控制请求模型"""
    action: str = Field(description="屏幕操作: on/off/toggle")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['on', 'off', 'toggle']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v


class AppLaunchRequest(BaseModel):
    """应用启动请求模型"""
    package_name: Optional[str] = Field(default=None, description="包名")
    app_name: Optional[str] = Field(default=None, description="应用名称")
    activity: Optional[str] = Field(default=None, description="Activity名称")
    force_stop_current: bool = Field(default=False, description="是否强制停止当前应用")
    
    @validator('package_name', 'app_name', always=True)
    def validate_app_identifier(cls, v, values):
        package_name = values.get('package_name')
        app_name = values.get('app_name')
        if not package_name and not app_name:
            raise ValueError('Either package_name or app_name must be provided')
        return v


class AppStopRequest(BaseModel):
    """应用停止请求模型"""
    package_name: str = Field(description="要停止的应用包名")
    force: bool = Field(default=False, description="是否强制停止")


class ScreenshotRequest(BaseModel):
    """截图请求模型"""
    quality: Optional[int] = Field(default=None, ge=1, le=100, description="图片质量 1-100")
    format: Optional[str] = Field(default=None, description="图片格式 JPEG/PNG")
    filename: Optional[str] = Field(default=None, description="自定义文件名")
    
    @validator('format')
    def validate_format(cls, v):
        if v and v.upper() not in ['JPEG', 'JPG', 'PNG']:
            raise ValueError('Format must be JPEG, JPG, or PNG')
        return v.upper() if v else v


class NetworkConfigRequest(BaseModel):
    """网络配置请求模型"""
    ip_address: str = Field(description="静态IP地址")
    netmask: str = Field(default="255.255.255.0", description="子网掩码")
    gateway: str = Field(description="网关地址")
    dns_primary: str = Field(default="8.8.8.8", description="主DNS服务器")
    dns_secondary: str = Field(default="8.8.4.4", description="备用DNS服务器")
    interface: str = Field(default="wlan0", description="网络接口")


class CommandRequest(BaseModel):
    """自定义命令请求模型"""
    command: str = Field(description="要执行的ADB命令")
    timeout: Optional[int] = Field(default=None, ge=1, le=300, description="超时时间秒")
    shell: bool = Field(default=True, description="是否使用shell执行")


class BulkRequest(BaseModel):
    """批量操作请求模型"""
    operations: List[Dict[str, Any]] = Field(description="操作列表")
    fail_fast: bool = Field(default=False, description="遇到错误时是否立即停止")
    
    @validator('operations')
    def validate_operations(cls, v):
        if not v:
            raise ValueError('Operations list cannot be empty')
        if len(v) > 20:
            raise ValueError('Too many operations, maximum 20 allowed')
        return v