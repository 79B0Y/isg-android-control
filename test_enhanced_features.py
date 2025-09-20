#!/usr/bin/env python3
"""
测试增强版Android TV Box管理页面功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_enhanced_features():
    """测试增强版功能"""
    print("🚀 测试增强版Android TV Box管理页面")
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
                        
                        # 检查新功能
                        new_features = [
                            ('Add App Button', 'showAddAppModal'),
                            ('Edit App Modal', 'edit-app-modal'),
                            ('ADB Host Input', 'adb-host'),
                            ('ADB Port Input', 'adb-port'),
                            ('Save Configuration', 'saveConfiguration'),
                            ('Test ADB Connection', 'testAdbConnection'),
                            ('App Management Grid', 'apps-grid'),
                            ('Configuration Sections', 'config-sections')
                        ]
                        
                        for feature_name, feature_id in new_features:
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
        
        # 测试应用管理功能
        print("\n2. 测试应用管理功能...")
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
                        
                        # 测试编辑应用
                        edit_data = {
                            'name': 'Test App Updated',
                            'package': 'com.test.app.updated',
                            'visible': False
                        }
                        
                        async with session.put('http://localhost:3003/api/apps/Test%20App', 
                                             json=edit_data) as edit_response:
                            if edit_response.status == 200:
                                edit_result = await edit_response.json()
                                if edit_result.get('success'):
                                    print("   ✅ 编辑应用功能正常")
                                else:
                                    print("   ❌ 编辑应用失败")
                            else:
                                print("   ❌ 编辑应用API失败")
                        
                        # 测试删除应用
                        async with session.delete('http://localhost:3003/api/apps/Test%20App%20Updated') as del_response:
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
        print("\n3. 测试配置管理功能...")
        try:
            # 测试保存配置
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
        
        # 测试ADB连接测试功能
        print("\n4. 测试ADB连接测试功能...")
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
            print(f"   ❌ ADB连接测试功能错误: {e}")
        
        # 测试应用启动功能
        print("\n5. 测试应用启动功能...")
        try:
            launch_data = {
                'package_name': 'com.google.android.youtube.tv'
            }
            
            async with session.post('http://localhost:3003/api/launch-app', 
                                  json=launch_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ 应用启动功能正常")
                    else:
                        print("   ❌ 应用启动失败")
                else:
                    print("   ❌ 应用启动API失败")
        except Exception as e:
            print(f"   ❌ 应用启动功能错误: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 增强版功能测试完成！")
    print("\n📱 现在您可以:")
    print("   1. 打开浏览器访问 http://localhost:3003")
    print("   2. 在Apps页面点击'Add App'添加新应用")
    print("   3. 编辑现有应用的名称、包名和可见性")
    print("   4. 删除不需要的应用")
    print("   5. 在Configuration页面修改ADB设备IP和端口")
    print("   6. 保存配置并测试ADB连接")
    print("   7. 启动应用并查看状态更新")

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())

