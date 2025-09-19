# 修复下拉选择菜单问题

## 问题描述
Android TV Box App Selector下拉菜单没有显示选项。

## 解决方案

### 方法1: 在Home Assistant中重新加载集成
1. 打开Home Assistant Web界面
2. 进入 **设置** -> **设备与服务**
3. 找到 **Android TV Box** 集成
4. 点击 **重新加载** 按钮
5. 等待重新加载完成
6. 刷新页面查看下拉菜单

### 方法2: 清除浏览器缓存
1. 按 `Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac) 强制刷新
2. 或者按 `F12` 打开开发者工具
3. 右键点击刷新按钮，选择"清空缓存并硬性重新加载"

### 方法3: 检查Home Assistant日志
1. 进入 **设置** -> **系统** -> **日志**
2. 查看是否有Android TV Box相关的错误信息
3. 特别关注select实体的错误

### 方法4: 重启Home Assistant
如果以上方法都不行，可以重启Home Assistant容器：
```bash
docker restart homeassistant
```

## 验证步骤
1. 检查下拉菜单是否显示选项：YouTube, Netflix, iSG, Spotify
2. 尝试选择一个应用
3. 检查当前应用是否正确更新

## 技术说明
- select实体的options属性应该返回可见应用列表
- 当前应用应该显示为"iSG"
- 如果仍有问题，可能需要检查coordinator的初始化

