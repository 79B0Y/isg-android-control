# Termux 环境设置指南

本指南说明如何在 Android 设备的 Termux 环境中正确配置 ISG Android Control 系统。

## 问题诊断

如果你看到以下错误：
```
ADB command failed (exit 1): adb: device '127.0.0.1:5555' not found
```

这通常是因为：
1. ADB 连接配置不正确（IP 地址错误）
2. Android 设备未启用 ADB 调试
3. 设备不在同一网络中

## 快速设置

### 1. 运行自动设置脚本

```bash
# 在 Termux 中运行
./scripts/setup_termux.sh
```

脚本会自动：
- 检查 Termux 环境
- 安装必要的包（adb, python3, pip3）
- 更新设备配置文件
- 测试 ADB 连接

### 2. 手动配置

如果自动脚本失败，可以手动配置：

#### 更新设备配置

编辑 `configs/device.yaml`：
```yaml
adb_host: 192.168.188.221  # 你的 Android 设备 IP
adb_port: 5555
adb_serial: ""  # 可选；如果设置会覆盖 host:port
```

#### 测试 ADB 连接

```bash
# 连接设备
adb connect 192.168.188.221:5555

# 测试连接
adb shell echo "Test successful"

# 查看连接的设备
adb devices
```

## Android 设备设置

### 1. 启用开发者选项

1. 进入 **设置** > **关于手机**
2. 连续点击 **版本号** 7 次
3. 返回设置，找到 **开发者选项**

### 2. 启用 ADB 调试

1. 在 **开发者选项** 中启用 **USB 调试**
2. 启用 **网络 ADB** 或 **无线调试**
3. 记录设备的 IP 地址

### 3. 获取设备 IP

```bash
# 在 Android 设备上运行
ip addr show wlan0 | grep inet
```

或者在设置中查看：
- **设置** > **Wi-Fi** > 点击当前网络 > **高级** > **IP 地址**

## Termux 环境要求

### 必需包

```bash
pkg update
pkg install -y android-tools python python-pip
```

### 可选包（用于性能监控）

```bash
pkg install -y procps-ng  # 提供 top, ps 等命令
```

## 环境检测

系统会自动检测 Termux 环境：

- 检查 `$PREFIX` 环境变量
- 检查 `/system/build.prop` 文件
- 检查 `/data/data/com.termux` 目录

## 性能监控

在 Termux 环境中，系统会：

1. **优先使用本地命令**：
   - 使用 `top` 命令监控 CPU 使用率
   - 使用 `/proc/meminfo` 监控内存使用率
   - 使用 `/proc/loadavg` 监控系统负载

2. **回退到 ADB**：
   - 如果本地命令不可用，回退到 ADB 命令
   - 确保在 ADB 连接失败时系统仍能运行

## 故障排除

### ADB 连接失败

如果看到错误 `adb: device '127.0.0.1:5555' not found`，这通常是因为 ADB 服务器缓存了错误的连接信息。

#### 快速修复

运行自动修复脚本：
```bash
./scripts/fix_adb_connection.sh
```

#### 手动修复

1. **清理 ADB 缓存**：
   ```bash
   adb kill-server
   adb start-server
   ```

2. **重新连接设备**：
   ```bash
   adb connect 192.168.188.221:5555
   ```

3. **验证连接**：
   ```bash
   adb devices
   adb shell echo "Test successful"
   ```

#### 诊断工具

运行诊断脚本检查所有组件：
```bash
python3 scripts/diagnose_adb.py
```

#### 其他检查

1. **检查网络连接**：
   ```bash
   ping 192.168.188.221
   ```

2. **检查防火墙**：
   - 确保 Android 设备防火墙允许 5555 端口
   - 确保路由器没有阻止设备间通信

### 性能监控不工作

1. **检查 top 命令**：
   ```bash
   top -b -n 1
   ```

2. **检查 proc 文件系统**：
   ```bash
   ls -la /proc/loadavg /proc/meminfo
   ```

3. **查看日志**：
   ```bash
   tail -f var/log/isg-android-control.log
   ```

## 配置验证

运行以下命令验证配置：

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from isg_android_control.core.adb import ADBController
import asyncio

async def test():
    adb = ADBController()
    try:
        result = await adb._run('shell', 'echo', 'Test')
        print('✅ ADB connection working:', result)
    except Exception as e:
        print('❌ ADB connection failed:', e)

asyncio.run(test())
"
```

## 启动系统

配置完成后，启动系统：

```bash
# 启动完整系统
python3 -m isg_android_control.run

# 或只启动 API 服务器
python3 -m isg_android_control.api.main
```

## 注意事项

1. **网络稳定性**：确保 Android 设备和 Termux 在同一稳定网络中
2. **电池优化**：在 Android 设备上禁用 Termux 的电池优化
3. **权限管理**：确保 Termux 有必要的系统权限
4. **定期检查**：定期检查 ADB 连接状态，必要时重新连接

## 支持

如果遇到问题：

1. 检查日志文件：`var/log/isg-android-control.log`
2. 运行诊断脚本：`./scripts/setup_termux.sh`
3. 查看 API 状态：`curl http://localhost:8000/status`
4. 检查 MQTT 连接：查看 Home Assistant 中的设备状态
