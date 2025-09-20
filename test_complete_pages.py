#!/usr/bin/env python3
"""
测试完整的Android TV Box管理页面功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_complete_pages():
    """测试所有页面功能"""
    print("🚀 测试完整的Android TV Box管理页面")
    print("=" * 60)
    
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
                            ('Add App Modal', 'add-app-modal'),
                            ('Form Elements', 'form-group'),
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
        apis = [
            ('/api/status', '设备状态'),
            ('/api/apps', '应用列表'),
            ('/api/config', '配置信息')
        ]
        
        for api_path, api_name in apis:
            try:
                async with session.get(f'http://localhost:3003{api_path}') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            print(f"   ✅ {api_name} API正常")
                            if api_path == '/api/status':
                                status_data = data['data']
                                print(f"      - ADB连接: {'✅' if status_data.get('adb_connected') else '❌'}")
                                print(f"      - 设备电源: {'✅' if status_data.get('device_powered_on') else '❌'}")
                                print(f"      - WiFi状态: {'✅' if status_data.get('wifi_enabled') else '❌'}")
                                print(f"      - 当前应用: {status_data.get('current_app', 'Unknown')}")
                                print(f"      - iSG状态: {'✅' if status_data.get('isg_running') else '❌'}")
                            elif api_path == '/api/apps':
                                apps = data['data']
                                print(f"      - 应用数量: {len(apps)}")
                                for app in apps:
                                    print(f"        * {app['name']} ({app['package']})")
                            elif api_path == '/api/config':
                                config = data['data']
                                print(f"      - ADB主机: {config.get('host', 'Unknown')}")
                                print(f"      - ADB端口: {config.get('port', 'Unknown')}")
                                device_name = config.get('name') or config.get('device_name', 'Unknown')
                                print(f"      - 设备名称: {device_name}")
                        else:
                            print(f"   ❌ {api_name} API返回错误: {data.get('error', 'Unknown')}")
                    else:
                        print(f"   ❌ {api_name} API失败: HTTP {response.status}")
            except Exception as e:
                print(f"   ❌ {api_name} API错误: {e}")
        
        # 测试应用管理功能
        print("\n3. 测试应用管理功能...")
        try:
            # 测试添加应用
            test_app = {
                'name': 'Test App',
                'package': 'com.test.app',
                'visible': True
            }
            
            async with session.post('http://localhost:3003/api/apps', 
                                  json=test_app) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ 添加应用功能正常")
                        
                        # 测试删除应用
                        async with session.delete('http://localhost:3003/api/apps/Test%20App') as del_response:
                            if del_response.status == 200:
                                del_data = await del_response.json()
                                if del_data.get('success'):
                                    print("   ✅ 删除应用功能正常")
                                else:
                                    print("   ❌ 删除应用失败")
                            else:
                                print("   ❌ 删除应用API失败")
                    else:
                        print("   ❌ 添加应用失败")
                else:
                    print("   ❌ 添加应用API失败")
        except Exception as e:
            print(f"   ❌ 应用管理功能错误: {e}")
        
        # 测试配置管理功能
        print("\n4. 测试配置管理功能...")
        try:
            test_config = {
                'host': '192.168.188.221',
                'port': 5555,
                'name': 'Test Device',
                'screenshot_path': '/tmp/screenshots/',
                'screenshot_keep_count': 3,
                'screenshot_interval': 3,
                'performance_check_interval': 500,
                'cpu_threshold': 50,
                'termux_mode': False
            }
            
            async with session.post('http://localhost:3003/api/config', 
                                  json=test_config) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ 配置保存功能正常")
                    else:
                        print("   ❌ 配置保存失败")
                else:
                    print("   ❌ 配置保存API失败")
        except Exception as e:
            print(f"   ❌ 配置管理功能错误: {e}")
        
        # 测试连接测试功能
        print("\n5. 测试连接测试功能...")
        try:
            test_connection = {
                'host': '192.168.188.221',
                'port': 5555
            }
            
            async with session.post('http://localhost:3003/api/test-connection', 
                                  json=test_connection) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ ADB连接测试功能正常")
                    else:
                        print("   ❌ ADB连接测试失败")
                else:
                    print("   ❌ ADB连接测试API失败")
        except Exception as e:
            print(f"   ❌ 连接测试功能错误: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 完整页面功能测试完成！")
    print("\n📱 现在您可以:")
    print("   1. 打开浏览器访问 http://localhost:3003")
    print("   2. 使用Dashboard查看设备状态")
    print("   3. 在Apps页面管理Android应用")
    print("   4. 在Configuration页面调整设置")
    print("   5. 在MQTT页面配置MQTT连接")
    print("   6. 使用所有交互功能（添加/编辑/删除应用）")
    print("   7. 测试各种连接和配置功能")

if __name__ == "__main__":
    asyncio.run(test_complete_pages())

