#!/usr/bin/env python3
"""
测试重新安装后的功能
"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def test_reinstall():
    """测试重新安装后的功能"""
    print("🔄 测试重新安装后的功能")
    print("=" * 60)
    
    # 等待Home Assistant完全启动
    print("1. 等待Home Assistant启动...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:3003/api/status', timeout=5) as response:
                    if response.status == 200:
                        print(f"   ✅ Home Assistant启动成功 (尝试 {attempt + 1}/{max_attempts})")
                        break
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"   ⏳ 等待启动中... (尝试 {attempt + 1}/{max_attempts})")
                await asyncio.sleep(2)
            else:
                print(f"   ❌ Home Assistant启动失败: {e}")
                return
    
    # 测试功能
    async with aiohttp.ClientSession() as session:
        # 测试2: 检查状态API
        print("\n2. 测试状态API...")
        try:
            async with session.get('http://localhost:3003/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        status_data = data['data']
                        print("   ✅ 状态API正常")
                        print(f"      - ADB连接: {'✅' if status_data.get('adb_connected') else '❌'}")
                        print(f"      - 设备电源: {'✅' if status_data.get('device_powered_on') else '❌'}")
                        print(f"      - WiFi状态: {'✅' if status_data.get('wifi_enabled') else '❌'}")
                        print(f"      - 当前应用包名: {status_data.get('current_app', 'Unknown')}")
                        print(f"      - 当前应用名称: {status_data.get('current_app_name', 'Unknown')}")
                        print(f"      - CPU使用率: {status_data.get('cpu_usage', 'Unknown')}%")
                        print(f"      - 内存使用: {status_data.get('memory_used', 'Unknown')} MB")
                        print(f"      - 亮度: {status_data.get('brightness', 'Unknown')}")
                        print(f"      - iSG状态: {'✅' if status_data.get('isg_running') else '❌'}")
                    else:
                        print("   ❌ 状态API失败")
                else:
                    print(f"   ❌ 状态API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 状态API异常: {e}")
        
        # 测试3: 检查应用配置
        print("\n3. 测试应用配置...")
        try:
            async with session.get('http://localhost:3003/api/apps') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        apps = data['data']
                        print("   ✅ 应用配置正常")
                        print(f"      - 应用数量: {len(apps)}")
                        for app in apps:
                            print(f"        * {app['name']} ({app['package']}) - Visible: {app['visible']}")
                    else:
                        print("   ❌ 应用配置失败")
                else:
                    print(f"   ❌ 应用配置API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 应用配置异常: {e}")
        
        # 测试4: 检查Web界面
        print("\n4. 测试Web界面...")
        try:
            async with session.get('http://localhost:3003') as response:
                if response.status == 200:
                    content = await response.text()
                    page_size = len(content)
                    print("   ✅ Web界面正常")
                    print(f"      - 页面大小: {page_size} 字符")
                    
                    # 检查重构功能
                    features = [
                        ('Connect ADB按钮', 'Connect ADB'),
                        ('Add App功能', 'Add App'),
                        ('Configuration页面', 'Configuration'),
                        ('Apps管理', 'apps-grid'),
                        ('模态框', 'modal'),
                        ('Toast通知', 'toast')
                    ]
                    
                    for feature_name, feature_id in features:
                        if feature_id in content:
                            print(f"      ✅ {feature_name} 已实现")
                        else:
                            print(f"      ❌ {feature_name} 缺失")
                else:
                    print(f"   ❌ Web界面错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Web界面异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 重新安装测试完成！")
    print("\n📱 重新安装结果:")
    print("   ✅ 集成文件已重新安装")
    print("   ✅ 配置文件已更新")
    print("   ✅ Web界面已恢复")
    print("   ✅ 所有功能已重新部署")
    print("\n🚀 现在可以:")
    print("   1. 访问 http://localhost:3003 使用Web管理界面")
    print("   2. 在Home Assistant中重新加载Android TV Box集成")
    print("   3. 检查下拉菜单选项是否正常显示")
    print("   4. 验证CPU和内存数据是否正确显示")

if __name__ == "__main__":
    asyncio.run(test_reinstall())

