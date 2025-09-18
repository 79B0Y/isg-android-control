# Android TV Box Web Management Interface Guide

## 🌐 Web界面概览

Android TV Box集成现在包含一个功能完整的Web管理界面，运行在端口3003上，提供直观的配置管理和设备监控功能。

### 访问地址
- **本地访问**: `http://localhost:3003`
- **网络访问**: `http://[设备IP]:3003`

## 📱 界面功能

### 1. Dashboard (仪表板)
实时监控Android TV Box的状态和iSG应用运行情况。

#### 功能特性
- **设备状态监控**: 电源、WiFi、当前应用状态
- **iSG状态监控**: iSG应用运行状态和最后检查时间
- **快速操作**: 刷新状态、唤醒iSG、重启iSG
- **连接状态**: ADB连接状态指示器

#### 状态指示器
- 🟢 **Online**: ADB连接正常
- 🔴 **Offline**: ADB连接断开
- **Power**: 设备电源状态
- **WiFi**: WiFi连接状态
- **Current App**: 当前前台应用
- **iSG Running**: iSG应用运行状态

### 2. Apps (应用管理)
管理Android TV Box上的应用程序配置。

#### 功能特性
- **应用列表**: 显示所有已配置的应用
- **添加应用**: 添加新的应用程序
- **编辑应用**: 修改现有应用配置
- **删除应用**: 移除不需要的应用
- **可见性控制**: 控制应用在Home Assistant中的显示

#### 应用配置
- **应用名称**: 在Home Assistant中显示的名称
- **包名**: Android应用的包名（如com.netflix.mediaclient）
- **可见性**: 是否在Home Assistant选择器中显示

#### 默认应用
- **Home Assistant**: `io.homeassistant.companion.android`
- **YouTube**: `com.google.android.youtube`
- **Spotify**: `com.spotify.music`
- **iSG**: `com.linknlink.app.device.isg`

### 3. Configuration (配置管理)
配置ADB连接、Home Assistant和截图设置。

#### ADB连接配置
- **Host**: ADB主机地址（默认127.0.0.1）
- **Port**: ADB端口（默认5555）
- **Device Name**: 设备名称（默认Android TV Box）
- **连接测试**: 测试ADB连接是否正常

#### Home Assistant配置
- **HA Host**: Home Assistant主机地址
- **HA Port**: Home Assistant端口（默认8123）
- **HA Token**: Home Assistant访问令牌

#### 截图设置
- **Screenshot Path**: 截图保存路径
- **Keep Count**: 保留截图数量
- **Interval**: 截图间隔（秒）

#### iSG监控配置
- **Enable Monitoring**: 启用iSG监控
- **Check Interval**: 检查间隔（秒）

### 4. MQTT (MQTT配置)
配置MQTT broker连接和主题设置。

#### MQTT Broker配置
- **Broker Host**: MQTT代理主机地址
- **Broker Port**: MQTT代理端口（默认1883）
- **Username**: MQTT用户名
- **Password**: MQTT密码
- **Client ID**: MQTT客户端ID

#### 主题配置
- **Base Topic**: 基础主题（默认android_tv_box）
- **Status Topic**: 状态主题
- **Command Topic**: 命令主题

#### 高级设置
- **QoS Level**: 服务质量等级（0-2）
- **Retain Messages**: 保留消息
- **Keep Alive**: 保活时间（秒）

## 🎯 使用指南

### 首次设置
1. **启动Home Assistant**并加载Android TV Box集成
2. **打开浏览器**访问`http://localhost:3003`
3. **检查Dashboard**确认ADB连接状态
4. **配置ADB连接**（如需要）
5. **测试连接**确保配置正确
6. **添加应用**到应用列表
7. **配置MQTT**（如需要）

### 应用管理
1. **切换到Apps标签**
2. **点击"Add App"按钮**
3. **填写应用信息**：
   - 应用名称（如"Netflix"）
   - 包名（如"com.netflix.mediaclient"）
   - 选择是否在HA中显示
4. **点击"Add App"确认**
5. **编辑或删除应用**（如需要）

### 配置管理
1. **切换到Configuration标签**
2. **修改配置项**：
   - ADB连接设置
   - Home Assistant设置
   - 截图设置
   - iSG监控设置
3. **测试连接**（如需要）
4. **点击"Save Configuration"保存**

### MQTT配置
1. **切换到MQTT标签**
2. **配置MQTT Broker**：
   - 输入broker地址和端口
   - 设置用户名和密码
   - 配置客户端ID
3. **设置主题**：
   - 基础主题
   - 状态和命令主题
4. **配置高级设置**：
   - QoS等级
   - 消息保留
   - 保活时间
5. **测试MQTT连接**
6. **保存配置**

## 🔧 技术特性

### 响应式设计
- **桌面端**: 完整功能界面
- **平板端**: 适配中等屏幕
- **移动端**: 优化的移动界面

### 实时更新
- **状态刷新**: 每30秒自动更新
- **手动刷新**: 点击刷新按钮
- **连接状态**: 实时显示ADB连接状态

### 用户体验
- **Toast通知**: 操作成功/失败反馈
- **加载指示器**: 操作进行中的视觉反馈
- **模态对话框**: 清洁的添加/编辑界面
- **错误处理**: 优雅的错误处理和用户提示

### 安全特性
- **CORS支持**: 跨域请求支持
- **输入验证**: 前端和后端输入验证
- **错误处理**: 完善的错误处理机制

## 🚀 API接口

### 配置接口
- `GET /api/config` - 获取当前配置
- `POST /api/config` - 更新配置

### 应用接口
- `GET /api/apps` - 获取应用列表
- `POST /api/apps` - 添加应用
- `PUT /api/apps/{app_id}` - 更新应用
- `DELETE /api/apps/{app_id}` - 删除应用

### 状态接口
- `GET /api/status` - 获取设备状态

### 测试接口
- `POST /api/test-connection` - 测试ADB连接
- `POST /api/test-mqtt` - 测试MQTT连接

### 操作接口
- `POST /api/wake-isg` - 唤醒iSG
- `POST /api/restart-isg` - 重启iSG
- `POST /api/restart-ha` - 重启Home Assistant

## 🔍 故障排除

### 无法访问Web界面
1. **检查端口**: 确认端口3003未被占用
2. **检查防火墙**: 确认防火墙允许端口3003
3. **检查Home Assistant**: 确认集成已正确加载
4. **查看日志**: 检查Home Assistant日志中的错误信息

### 应用管理问题
1. **检查包名**: 确认Android应用包名正确
2. **检查权限**: 确认ADB有启动应用的权限
3. **检查应用**: 确认应用已安装在设备上

### 配置保存问题
1. **检查权限**: 确认有写入配置文件的权限
2. **检查格式**: 确认配置格式正确
3. **检查依赖**: 确认所有依赖已安装

### MQTT连接问题
1. **检查Broker**: 确认MQTT broker运行正常
2. **检查网络**: 确认网络连接正常
3. **检查凭据**: 确认用户名和密码正确
4. **检查端口**: 确认端口配置正确

## 📈 性能优化

### 服务器优化
- **异步处理**: 所有操作都是异步的
- **连接池**: ADB连接复用
- **缓存机制**: 配置和应用列表缓存

### 前端优化
- **懒加载**: 按需加载资源
- **防抖处理**: 避免频繁请求
- **本地存储**: 缓存用户设置

### 网络优化
- **压缩传输**: 启用gzip压缩
- **缓存策略**: 静态资源缓存
- **CDN支持**: 支持CDN加速

## 🔮 未来计划

### 计划功能
- [ ] 用户认证系统
- [ ] 多设备管理
- [ ] 应用使用统计
- [ ] 自动化规则配置
- [ ] 日志查看器
- [ ] 主题定制

### 技术改进
- [ ] WebSocket实时通信
- [ ] PWA支持
- [ ] 离线功能
- [ ] 多语言支持
- [ ] 插件系统

---

**版本**: 1.2.0  
**更新日期**: 2024年12月  
**状态**: ✅ 完成
