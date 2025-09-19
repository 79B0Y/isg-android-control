#!/usr/bin/env python3
"""
测试select实体的选项
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_select_entity():
    """测试select实体"""
    print("📋 测试Select实体选项")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 测试1: 检查应用配置
        print("1. 检查应用配置...")
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
        
        # 测试2: 检查可见应用
        print("\n2. 检查可见应用...")
        try:
            async with session.get('http://localhost:3003/api/config') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        config = data['data']
                        visible_apps = config.get('visible', [])
                        apps = config.get('apps', {})
                        print("   ✅ 配置检查正常")
                        print(f"      - 可见应用: {visible_apps}")
                        print(f"      - 所有应用: {list(apps.keys())}")
                        
                        # 检查可见应用是否在应用列表中
                        valid_visible = [app for app in visible_apps if app in apps]
                        print(f"      - 有效可见应用: {valid_visible}")
                    else:
                        print("   ❌ 配置检查失败")
                else:
                    print(f"   ❌ 配置检查API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 配置检查异常: {e}")
        
        # 测试3: 检查当前应用
        print("\n3. 检查当前应用...")
        try:
            async with session.get('http://localhost:3003/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        status_data = data['data']
                        current_app = status_data.get('current_app')
                        print("   ✅ 状态检查正常")
                        print(f"      - 当前应用包名: {current_app}")
                        
                        # 查找对应的应用名称
                        async with session.get('http://localhost:3003/api/config') as config_response:
                            if config_response.status == 200:
                                config_data = await config_response.json()
                                if config_data.get('success'):
                                    apps = config_data['data'].get('apps', {})
                                    current_app_name = None
                                    for app_name, package_name in apps.items():
                                        if package_name == current_app:
                                            current_app_name = app_name
                                            break
                                    print(f"      - 当前应用名称: {current_app_name}")
                    else:
                        print("   ❌ 状态检查失败")
                else:
                    print(f"   ❌ 状态检查API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 状态检查异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Select实体测试完成！")
    print("\n📱 如果下拉菜单仍然没有选项，可能的原因:")
    print("   1. Home Assistant需要完全重启")
    print("   2. 浏览器缓存需要清除")
    print("   3. select实体需要重新加载")
    print("\n🔧 建议的解决方案:")
    print("   1. 在Home Assistant中: 开发者工具 -> 重新加载 -> 重新加载Android TV Box")
    print("   2. 清除浏览器缓存并刷新页面")
    print("   3. 检查Home Assistant日志中的错误信息")

if __name__ == "__main__":
    asyncio.run(test_select_entity())

