# Android TV Box Integration - 新功能更新

## 🆕 新增功能

### 1. iSG看护功能 (iSG Monitoring)

#### 功能描述
- **自动监控**: 定时检查iSG应用运行状态
- **自动唤醒**: 检测到iSG未运行时自动启动
- **状态报告**: 提供详细的运行状态信息
- **手动控制**: 支持手动唤醒和重启iSG

#### 实现细节
- **包名**: `com.linknlink.app.device.isg`
- **检查间隔**: 默认30秒（可配置）
- **自动恢复**: 检测到进程不存在时自动启动
- **日志记录**: 详细的操作日志和状态变化

#### 配置选项
```yaml
android_tv_box:
  isg_monitoring: true          # 启用iSG监控
  isg_check_interval: 30       # 检查间隔（秒）
```

#### 实体类型
- **二进制传感器**: `binary_sensor.android_tv_box_isg_running`
- **状态属性**: 
  - `wake_attempted`: 是否尝试过自动唤醒
  - `monitoring_enabled`: 监控是否启用
  - `check_interval`: 检查间隔

#### 服务调用
```yaml
# 手动唤醒iSG
service: android_tv_box.wake_isg

# 重启iSG
service: android_tv_box.restart_isg
```

### 2. 应用选择器 (App Selector)

#### 功能描述
- **应用管理**: 支持配置多个Android应用
- **可见性控制**: 可选择在Home Assistant中显示哪些应用
- **一键启动**: 选择应用后自动在前台启动
- **状态同步**: 实时显示当前运行的应用

#### 配置示例
```yaml
android_tv_box:
  apps:
    YouTube: com.google.android.youtube
    Spotify: com.spotify.music
    iSG: com.linknlink.app.device.isg
    # 可以继续添加更多应用
  
  # 可选：限制在HA中显示的应用
  # 如果省略或为空，将显示apps中的所有应用
  visible:
    - YouTube
    - Spotify
    - iSG
```

#### 实体类型
- **选择器**: `select.android_tv_box_app_selector`
- **选项**: 根据`visible`配置显示应用列表
- **当前值**: 显示当前运行的应用名称

#### 使用方法
```yaml
# 通过服务启动应用
service: select.select_option
target:
  entity_id: select.android_tv_box_app_selector
data:
  option: "YouTube"

# 或者直接通过媒体播放器
service: media_player.play_media
target:
  entity_id: media_player.android_tv_box
data:
  media_content_type: app
  media_content_id: com.google.android.youtube
```

## 🔧 技术实现

### ADB服务扩展
在`adb_service.py`中新增了以下方法：

#### iSG监控方法
```python
async def is_isg_running(self) -> bool:
    """检查iSG应用是否运行"""

async def get_isg_process_info(self) -> Dict[str, Any]:
    """获取iSG进程信息"""

async def wake_up_isg(self) -> bool:
    """唤醒iSG应用"""

async def restart_isg(self) -> bool:
    """重启iSG应用"""
```

### 新实体平台

#### 1. Select平台 (`select.py`)
- 应用选择器实体
- 支持动态选项更新
- 实时状态同步

#### 2. Binary Sensor平台 (`binary_sensor.py`)
- iSG运行状态监控
- 自动唤醒功能
- 详细状态属性

### 配置模式更新
在`config.py`中新增了：
- 应用配置模式
- 可见性控制
- iSG监控配置

### 服务扩展
在`services.py`中新增了：
- `wake_isg`服务
- `restart_isg`服务

## 📊 功能对比

| 功能 | 之前 | 现在 |
|------|------|------|
| 应用启动 | 仅通过媒体播放器 | 支持选择器 + 媒体播放器 |
| iSG监控 | 无 | 自动监控 + 自动唤醒 |
| 应用管理 | 硬编码 | 可配置应用列表 |
| 状态监控 | 基础监控 | 详细进程状态 |
| 自动化 | 手动操作 | 自动恢复机制 |

## 🎯 使用场景

### 1. iSG看护场景
```yaml
# 自动化：iSG离线时发送通知
automation:
  - alias: "iSG Offline Alert"
    trigger:
      platform: state
      entity_id: binary_sensor.android_tv_box_isg_running
      to: "off"
    action:
      service: notify.persistent_notification
      data:
        message: "iSG应用已离线，正在尝试自动启动..."

# 自动化：定期检查iSG状态
automation:
  - alias: "iSG Health Check"
    trigger:
      platform: time_pattern
      minutes: "/30"  # 每30分钟检查一次
    action:
      service: android_tv_box.wake_isg
```

### 2. 应用管理场景
```yaml
# 自动化：根据时间启动不同应用
automation:
  - alias: "Morning Routine"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      service: select.select_option
      target:
        entity_id: select.android_tv_box_app_selector
      data:
        option: "YouTube"

  - alias: "Evening Entertainment"
    trigger:
      platform: time
      at: "20:00:00"
    action:
      service: select.select_option
      target:
        entity_id: select.android_tv_box_app_selector
      data:
        option: "Spotify"
```

### 3. 智能看护场景
```yaml
# 自动化：iSG异常时重启
automation:
  - alias: "iSG Recovery"
    trigger:
      platform: state
      entity_id: binary_sensor.android_tv_box_isg_running
      to: "off"
      for:
        minutes: 5  # 离线5分钟后重启
    action:
      service: android_tv_box.restart_isg
```

## 🔄 升级指南

### 从旧版本升级
1. **备份配置**: 备份现有的`configuration.yaml`
2. **更新集成**: 替换`custom_components/android_tv_box/`目录
3. **更新配置**: 添加新的配置选项
4. **重启服务**: 重启Home Assistant

### 配置迁移
旧配置会自动兼容，新功能使用默认配置：
- iSG监控默认启用
- 应用列表使用默认配置
- 所有实体默认启用

## 🐛 故障排除

### iSG监控问题
1. **检查包名**: 确认`com.linknlink.app.device.isg`正确
2. **检查权限**: 确保ADB有启动应用的权限
3. **检查日志**: 查看Home Assistant日志中的iSG相关消息

### 应用选择器问题
1. **检查配置**: 确认`apps`和`visible`配置正确
2. **检查包名**: 确认应用包名正确
3. **检查权限**: 确保ADB有启动应用的权限

### 常见错误
- **"Unknown app"**: 应用名称不在配置列表中
- **"iSG wake up failed"**: iSG应用无法启动
- **"Process not found"**: 应用进程不存在

## 📈 性能优化

### iSG监控优化
- 检查间隔可调整（默认30秒）
- 避免频繁的进程检查
- 智能唤醒机制

### 应用管理优化
- 缓存应用列表
- 异步启动应用
- 状态同步优化

## 🔮 未来计划

### 计划功能
- [ ] 应用使用统计
- [ ] 自定义应用图标
- [ ] 批量应用管理
- [ ] 应用分组功能
- [ ] 更多监控指标

### 扩展性
- 支持更多应用类型
- 可配置的监控策略
- 自定义唤醒规则
- 应用健康检查

---

**更新日期**: 2024年12月  
**版本**: 1.1.0  
**状态**: ✅ 完成
