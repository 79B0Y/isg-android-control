# 🚀 快速安装指南 - Termux proot Ubuntu

> **一键安装 Android Controller Service 到 Termux proot Ubuntu 环境**

## 💫 一键安装命令

### 方法 1: 完整一键安装

```bash
# 在 Termux 主环境中执行
pkg update && pkg upgrade -y && pkg install proot-distro git -y && \
proot-distro install ubuntu && \
proot-distro login ubuntu -- bash -c "
  cd /tmp && \
  git clone <项目地址> android-controller && \
  cd android-controller && \
  chmod +x install-termux-ubuntu.sh && \
  ./install-termux-ubuntu.sh
"
```

### 方法 2: 分步骤安装

```bash
# 步骤1: 准备Termux环境
pkg update && pkg upgrade -y
pkg install proot-distro git curl -y

# 步骤2: 安装Ubuntu系统  
proot-distro install ubuntu

# 步骤3: 登录并安装服务
proot-distro login ubuntu

# 在Ubuntu环境中执行:
cd /tmp
git clone <项目地址> android-controller
cd android-controller
./install-termux-ubuntu.sh
```

### 方法 3: 本地安装 (已有项目代码)

```bash
# 如果已经有项目文件
proot-distro login ubuntu
cd /path/to/your/android-controller
chmod +x install-termux-ubuntu.sh
./install-termux-ubuntu.sh
```

## 🎯 安装选项

### 标准安装 (推荐)
```bash
./install-termux-ubuntu.sh
```

### 调试模式安装
```bash
./install-termux-ubuntu.sh -d
```

### 跳过系统依赖 (已安装依赖时)
```bash
./install-termux-ubuntu.sh -s
```

### 强制重新安装
```bash
./install-termux-ubuntu.sh -f
```

### 静默安装 (无交互)
```bash
./install-termux-ubuntu.sh -s -d 2>&1 | tee install.log
```

## ⚡ 启动和使用

### 快速启动

```bash
# 连接Android设备
./connect.sh 192.168.1.100:5555

# 启动服务（推荐使用CLI命令）
isg-android-control start          # 后台启动
# 或 isg-android-control start -f  # 前台启动
# 或 ./start.sh                    # 使用脚本

# 检查状态
isg-android-control status

# 访问API文档
# http://localhost:8000/docs
```

### 一键启动脚本

创建 `run.sh` 用于一键启动：

```bash
cat > run.sh << 'EOF'
#!/bin/bash
echo "🚀 启动 Android Controller Service..."

# 激活虚拟环境
source venv/bin/activate

# 连接设备 (修改为你的设备IP)
./connect.sh 192.168.1.100:5555

# 启动服务
./start.sh
EOF

chmod +x run.sh
./run.sh
```

## 🔧 环境检查命令

### 快速环境检查

```bash
# 检查所有环境
./status.sh

# 或手动检查
echo "=== 环境检查 ==="
echo "Python: $(python3 --version 2>/dev/null || echo '未安装')"
echo "ADB: $(adb --version 2>/dev/null | head -1 || echo '未安装')" 
echo "虚拟环境: $([ -d venv ] && echo '✓ 存在' || echo '✗ 不存在')"
echo "配置文件: $([ -f .env ] && echo '✓ 存在' || echo '✗ 不存在')"
echo "ADB设备: $(adb devices 2>/dev/null | grep device$ | wc -l) 台"
```

### 网络连接测试

```bash
# 测试网络连接
echo "=== 网络测试 ==="
curl -s --connect-timeout 5 http://httpbin.org/ip && echo "✓ 网络正常" || echo "✗ 网络异常"
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "✓ DNS正常" || echo "✗ DNS异常"
```

## 🛠️ 常用维护命令

### 服务管理

```bash
# CLI命令方式（推荐）
isg-android-control start           # 启动服务
isg-android-control start -f        # 前台启动
isg-android-control stop            # 停止服务
isg-android-control restart         # 重启服务
isg-android-control status          # 查看状态
isg-android-control status -d       # 详细状态
isg-android-control logs            # 查看日志
isg-android-control logs -f         # 实时跟踪日志
isg-android-control logs --error    # 只看错误日志

# 传统脚本方式
./start.sh                          # 启动服务
./stop.sh                           # 停止服务  
./status.sh                         # 查看状态
tail -f data/logs/android_controller.log  # 查看日志
```

### 更新和维护

```bash
# 更新依赖
source venv/bin/activate
pip install --upgrade -r requirements.txt

# 清理日志
rm -f data/logs/*.log

# 清理截图
rm -f data/screenshots/*.jpg

# 重新安装虚拟环境
rm -rf venv
./install-termux-ubuntu.sh
```

## 🏠 Home Assistant 快速集成

### 一键配置 MQTT

```bash
# 快速配置MQTT (修改为你的配置)
cat >> .env << EOF

# Home Assistant MQTT 配置
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
MQTT_USERNAME=homeassistant
MQTT_PASSWORD=your_password
MQTT_CLIENT_ID=android_controller_$(date +%s)
EOF

# 重启服务生效
./stop.sh && ./start.sh
```

### 测试 MQTT 连接

```bash
# 安装MQTT客户端工具 (可选)
apt install mosquitto-clients -y

# 测试MQTT连接
mosquitto_sub -h 192.168.1.100 -p 1883 -u homeassistant -P your_password -t "homeassistant/#" -v
```

## 📱 设备连接快捷方式

### 常用设备连接

```bash
# 创建设备连接快捷方式
echo "alias connect-tv='./connect.sh 192.168.1.100:5555'" >> ~/.bashrc
echo "alias connect-tablet='./connect.sh 192.168.1.101:5555'" >> ~/.bashrc
echo "alias connect-phone='./connect.sh 192.168.1.102:5555'" >> ~/.bashrc

# 重新加载配置
source ~/.bashrc

# 使用快捷方式
connect-tv
```

### 自动设备发现

```bash
# 创建设备发现脚本
cat > discover-devices.sh << 'EOF'
#!/bin/bash
echo "🔍 扫描网络中的Android设备..."

for ip in 192.168.1.{100..200}; do
  if timeout 1 bash -c "</dev/tcp/$ip/5555" 2>/dev/null; then
    echo "发现设备: $ip:5555"
    adb connect $ip:5555 2>/dev/null
  fi
done

echo ""
echo "当前连接的设备:"
adb devices
EOF

chmod +x discover-devices.sh
./discover-devices.sh
```

## 🔄 自动化脚本

### 开机自启脚本

```bash
# 创建自启脚本 (在Termux主环境中)
cat > ~/.termux/boot/android-controller-boot.sh << 'EOF'
#!/bin/bash
sleep 30  # 等待网络连接

# 进入proot环境并启动服务
proot-distro login ubuntu -- bash -c "
  cd /path/to/android-controller && \
  ./run.sh > boot.log 2>&1 &
"
EOF

chmod +x ~/.termux/boot/android-controller-boot.sh

# 或在Ubuntu中创建cron任务
(crontab -l 2>/dev/null; echo "@reboot cd $(pwd) && ./run.sh") | crontab -
```

### 健康检查脚本

```bash
cat > health-check.sh << 'EOF'
#!/bin/bash
API_URL="http://localhost:8000"

# 检查API健康状态
if curl -s --connect-timeout 5 $API_URL/health >/dev/null; then
  echo "✅ 服务运行正常"
else
  echo "❌ 服务异常，尝试重启..."
  ./stop.sh
  sleep 5
  ./start.sh
  
  # 等待启动
  sleep 10
  if curl -s --connect-timeout 5 $API_URL/health >/dev/null; then
    echo "✅ 服务重启成功"
  else
    echo "❌ 服务重启失败，需要手动检查"
  fi
fi
EOF

chmod +x health-check.sh

# 添加到cron (每5分钟检查一次)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd $(pwd) && ./health-check.sh") | crontab -
```

## 🚨 应急恢复

### 快速恢复脚本

```bash
cat > emergency-reset.sh << 'EOF'
#!/bin/bash
echo "🚨 紧急恢复 Android Controller Service..."

# 停止所有相关进程
pkill -f "src.main" 2>/dev/null || true

# 备份配置
cp .env .env.backup.$(date +%s) 2>/dev/null || true
cp -r configs configs.backup.$(date +%s) 2>/dev/null || true

# 清理并重新安装
rm -rf venv
./install-termux-ubuntu.sh -f

echo "✅ 紧急恢复完成"
EOF

chmod +x emergency-reset.sh
```

### 数据备份脚本

```bash
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份配置和数据
cp .env "$BACKUP_DIR/" 2>/dev/null || true
cp -r configs "$BACKUP_DIR/" 2>/dev/null || true  
cp -r data/logs "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ 备份完成: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
EOF

chmod +x backup.sh
```

---

## 📞 快速支持

**遇到问题？使用这些快速诊断命令:**

```bash
# 一键诊断
echo "=== 快速诊断 ===" && \
./status.sh && \
echo "=== 最近错误 ===" && \
tail -20 data/logs/*.log 2>/dev/null | grep -i error && \
echo "=== 网络测试 ===" && \
curl -I http://localhost:8000/health 2>/dev/null && \
echo "=== ADB设备 ===" && \
adb devices
```

**其他资源:**
- 详细文档: `README-TERMUX-UBUNTU.md`
- API文档: http://localhost:8000/docs
- 配置说明: `configs/config.yaml`

---

*💡 提示: 将常用命令添加到 `.bashrc` 中，下次使用更方便！*