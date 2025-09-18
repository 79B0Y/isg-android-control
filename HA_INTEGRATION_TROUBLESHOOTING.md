# Home Assistant集成添加向导故障排除

## 问题：HA Integration里没有出现添加向导

## ✅ 已修复的代码问题

### 1. 修复了__init__.py
- ✅ 添加了正确的Platform导入
- ✅ 修复了async_setup函数以支持configuration.yaml导入
- ✅ 正确的ADB服务初始化和存储

### 2. 修复了config_flow.py
- ✅ 移除了废弃的CONNECTION_CLASS
- ✅ 添加了正确的错误处理
- ✅ 添加了ADB连接测试

### 3. 修复了manifest.json
- ✅ 添加了"config_flow": true字段
- ✅ 所有必需字段都存在

### 4. 添加了必需文件
- ✅ strings.json - 用户界面翻译
- ✅ translations/en.json - 本地化支持

## 🔍 故障排除步骤

### 步骤1：检查文件位置
确保文件在正确位置：
```
/config/custom_components/android_tv_box/
├── __init__.py
├── config_flow.py
├── manifest.json
├── strings.json
├── translations/
│   └── en.json
└── [其他平台文件]
```

### 步骤2：完全重启Home Assistant
**重要**：必须完全重启，而不是重新加载配置！

1. **Docker/Container**:
   ```bash
   docker restart homeassistant
   ```

2. **Supervisor**:
   ```bash
   ha core restart
   ```

3. **手动安装**:
   ```bash
   sudo systemctl restart home-assistant@homeassistant
   ```

### 步骤3：检查Home Assistant日志

1. 进入Home Assistant
2. Settings → System → Logs
3. 搜索"android_tv_box"相关错误

**常见错误模式**：
- `ModuleNotFoundError`: 缺少依赖包
- `ImportError`: 文件路径或导入问题
- `ConfigFlowError`: config_flow.py问题
- `ManifestError`: manifest.json格式问题

### 步骤4：清除缓存（如果需要）

如果集成之前安装过但有问题：

1. 停止Home Assistant
2. 删除 `/config/.storage/core.config_entries`
3. 重启Home Assistant

⚠️ **警告**：这会删除所有config entry配置！

### 步骤5：验证依赖包

检查requirements.txt中的包是否在HA环境中可用：
- `uiautomator2>=2.16.23`
- `aiohttp>=3.8.0`
- `aiohttp-cors>=0.7.0`
- `paho-mqtt>=1.6.0`

### 步骤6：手动检查集成

在Home Assistant中运行：

1. **开发者工具** → **Services**
2. 调用服务：`homeassistant.reload_config_entry`
3. 或者重新加载所有集成

## 🎯 确认集成可见的标志

成功后你应该看到：

1. **Settings** → **Devices & Services** → **Add Integration**
2. 搜索 "Android TV Box" 或 "android"
3. 看到带有图标的集成选项
4. 点击后出现配置表单

## 🔧 代码验证命令

在HA环境中运行（如果可以访问命令行）：

```python
# 在HA Python环境中测试
import sys
sys.path.append('/config/custom_components')

try:
    from android_tv_box.config import DOMAIN
    print(f"✅ Domain: {DOMAIN}")

    import android_tv_box.config_flow
    print("✅ Config flow imported")

    import android_tv_box
    print("✅ Init imported")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 📋 最终检查清单

- [ ] 文件在正确的custom_components路径
- [ ] manifest.json包含"config_flow": true
- [ ] config_flow.py有ConfigFlow类
- [ ] __init__.py有async_setup和async_setup_entry
- [ ] Home Assistant已完全重启
- [ ] 日志中没有相关错误
- [ ] 所有依赖包可用

## 🆘 如果仍然不工作

1. **检查HA版本兼容性**（要求2023.1.0+）
2. **尝试其他已知工作的自定义集成**，确认HACS和custom_components功能正常
3. **创建最小测试集成**验证环境
4. **检查文件权限**（特别是Linux/Docker环境）

## 📝 常见原因总结

1. **没有完全重启HA** - 最常见原因
2. **文件位置错误** - 不在custom_components目录
3. **manifest.json缺少config_flow字段** - 已修复
4. **Python语法错误** - 已验证修复
5. **依赖包缺失** - 检查requirements.txt
6. **权限问题** - 特别是Docker环境

**所有代码问题都已修复，现在主要是部署和配置问题！**