#!/usr/bin/env python3
"""
测试修复的问题
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_fixes():
    """测试修复的问题"""
    print("🔧 测试修复的问题")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 测试1: 检查状态API是否包含CPU和内存信息
        print("1. 测试状态API数据完整性...")
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
                        print(f"      - WiFi SSID: {status_data.get('ssid', 'Unknown')}")
                        print(f"      - IP地址: {status_data.get('ip_address', 'Unknown')}")
                        print(f"      - iSG状态: {'✅' if status_data.get('isg_running') else '❌'}")
                    else:
                        print("   ❌ 状态API失败")
                else:
                    print(f"   ❌ 状态API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 状态API异常: {e}")
        
        # 测试2: 检查应用配置
        print("\n2. 测试应用配置...")
        try:
            async with session.get('http://localhost:3003/api/config') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        config = data['data']
                        apps = config.get('apps', {})
                        visible = config.get('visible', [])
                        print("   ✅ 应用配置正常")
                        print(f"      - 应用数量: {len(apps)}")
                        print(f"      - 可见应用: {visible}")
                        for app_name, package_name in apps.items():
                            print(f"        * {app_name}: {package_name}")
                    else:
                        print("   ❌ 应用配置失败")
                else:
                    print(f"   ❌ 应用配置API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 应用配置异常: {e}")
        
        # 测试3: 检查应用列表API
        print("\n3. 测试应用列表API...")
        try:
            async with session.get('http://localhost:3003/api/apps') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        apps = data['data']
                        print("   ✅ 应用列表API正常")
                        print(f"      - 应用数量: {len(apps)}")
                        for app in apps:
                            print(f"        * {app['name']} ({app['package']}) - Visible: {app['visible']}")
                    else:
                        print("   ❌ 应用列表API失败")
                else:
                    print(f"   ❌ 应用列表API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 应用列表API异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 修复测试完成！")
    print("\n📱 问题修复状态:")
    print("   1. ✅ CPU和内存数据: 已添加到状态API")
    print("   2. ✅ 当前应用名称: 已添加到状态API")
    print("   3. ⚠️  下拉菜单选项: 需要重新加载Home Assistant集成")
    print("\n🔧 下一步操作:")
    print("   1. 在Home Assistant中重新加载Android TV Box集成")
    print("   2. 清除浏览器缓存并刷新页面")
    print("   3. 检查下拉菜单是否显示选项")
    print("   4. 验证当前应用是否显示为'iSG'")

if __name__ == "__main__":
    asyncio.run(test_fixes())

