# HACS设置指南

## 问题分析

无法添加到HACS的原因：
1. ❌ **没有Git仓库** - 代码需要在GitHub仓库中
2. ❌ **GitHub仓库不存在** - hacs.json和manifest.json中的URL无效

## 解决步骤

### 步骤1：创建GitHub仓库

1. 在GitHub上创建新仓库：`android-tv-box`
2. 获取仓库URL，例如：`https://github.com/YOUR_USERNAME/android-tv-box`

### 步骤2：更新配置文件

更新你的GitHub用户名：

```bash
# 编辑 hacs.json - 这个文件已经修复，不需要URLs
# 编辑 manifest.json
sed -i 's|https://github.com/bobo/android-tv-box|https://github.com/YOUR_USERNAME/android-tv-box|g' custom_components/android_tv_box/manifest.json

# 编辑 README.md
sed -i 's|@bobo|@YOUR_USERNAME|g' README.md
```

### 步骤3：初始化Git并推送

```bash
# 初始化git仓库
git init

# 添加所有文件
git add .

# 创建初始提交
git commit -m "Initial commit: Android TV Box Home Assistant Integration"

# 添加远程仓库（替换YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/android-tv-box.git

# 推送到GitHub
git push -u origin main
```

### 步骤4：在HACS中添加

1. 打开Home Assistant
2. 进入HACS → Integrations
3. 点击右上角三个点 → Custom repositories
4. 添加仓库URL：`https://github.com/YOUR_USERNAME/android-tv-box`
5. 类别选择：Integration
6. 点击ADD

### 步骤5：安装集成

1. 在HACS中搜索"Android TV Box"
2. 点击下载
3. 重启Home Assistant
4. 进入Settings → Devices & Services
5. 点击Add Integration
6. 搜索"Android TV Box"并配置

## 当前文件状态

✅ **已修复的文件：**
- `hacs.json` - 移除了不需要的字段
- `custom_components/android_tv_box/__init__.py` - 修复了ADB服务初始化
- `custom_components/android_tv_box/config_flow.py` - 添加了连接验证
- `custom_components/android_tv_box/translations/en.json` - 添加了翻译支持
- `README.md` - 添加了HACS badge

✅ **HACS兼容性验证：**
- 所有必需文件存在
- JSON格式正确
- 文件结构符合要求
- Domain一致性正确

## 需要你完成的：

1. **创建GitHub仓库**
2. **更新URLs为你的GitHub用户名**
3. **推送代码到GitHub**
4. **在HACS中添加仓库**

完成这些步骤后，集成就可以成功添加到HACS了！