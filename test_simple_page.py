#!/usr/bin/env python3
"""
测试简化版Android TV Box管理页面
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_simple_page():
    """测试简化版页面功能"""
    print("🚀 测试简化版Android TV Box管理页面")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 测试主页面加载
        print("1. 测试主页面加载...")
        try:
            async with session.get('http://localhost:3003') as response:
                if response.status == 200:
                    content = await response.text()
                    if 'Android TV Box Management' in content:
                        print("   ✅ 主页面加载成功")
                        print(f"   📄 页面大小: {len(content)} 字符")
                        
                        # 检查关键功能
                        features = [
                            ('Dashboard', 'dashboard'),
                            ('Apps', 'apps'),
                            ('Configuration', 'config'),
                            ('MQTT', 'mqtt'),
                            ('JavaScript Functions', 'refreshStatus'),
                            ('Toast Notifications', 'toast'),
                            ('Loading Indicator', 'loading')
                        ]
                        
                        for feature_name, feature_id in features:
                            if feature_id in content:
                                print(f"   ✅ {feature_name} 功能已实现")
                            else:
                                print(f"   ❌ {feature_name} 功能缺失")
                    else:
                        print("   ❌ 主页面内容不完整")
                else:
                    print(f"   ❌ 主页面加载失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 主页面加载错误: {e}")
        
        # 测试API端点
        print("\n2. 测试API端点...")
        try:
            async with session.get('http://localhost:3003/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        status_data = data['data']
                        print("   ✅ 设备状态 API正常")
                        print(f"      - ADB连接: {'✅' if status_data.get('adb_connected') else '❌'}")
                        print(f"      - 设备电源: {'✅' if status_data.get('device_powered_on') else '❌'}")
                        print(f"      - WiFi状态: {'✅' if status_data.get('wifi_enabled') else '❌'}")
                        print(f"      - 当前应用: {status_data.get('current_app', 'Unknown')}")
                        print(f"      - iSG状态: {'✅' if status_data.get('isg_running') else '❌'}")
                    else:
                        print("   ❌ API返回错误")
                else:
                    print(f"   ❌ API失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ API错误: {e}")
        
        # 测试应用API
        print("\n3. 测试应用API...")
        try:
            async with session.get('http://localhost:3003/api/apps') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        apps = data['data']
                        print("   ✅ 应用列表 API正常")
                        print(f"      - 应用数量: {len(apps)}")
                        for app in apps:
                            print(f"        * {app['name']} ({app['package']})")
                    else:
                        print("   ❌ 应用API返回错误")
                else:
                    print(f"   ❌ 应用API失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 应用API错误: {e}")
        
        # 测试配置API
        print("\n4. 测试配置API...")
        try:
            async with session.get('http://localhost:3003/api/config') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        config = data['data']
                        print("   ✅ 配置 API正常")
                        print(f"      - ADB主机: {config.get('host', 'Unknown')}")
                        print(f"      - ADB端口: {config.get('port', 'Unknown')}")
                        device_name = config.get('name') or config.get('device_name', 'Unknown')
                        print(f"      - 设备名称: {device_name}")
                    else:
                        print("   ❌ 配置API返回错误")
                else:
                    print(f"   ❌ 配置API失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 配置API错误: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 简化版页面测试完成！")
    print("\n📱 现在您可以:")
    print("   1. 打开浏览器访问 http://localhost:3003")
    print("   2. 查看Dashboard页面显示设备状态")
    print("   3. 使用Apps页面查看应用列表")
    print("   4. 使用Configuration页面查看配置")
    print("   5. 点击按钮测试各种功能")
    print("   6. 查看浏览器控制台的调试信息")

if __name__ == "__main__":
    asyncio.run(test_simple_page())

