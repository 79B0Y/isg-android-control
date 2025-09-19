#!/usr/bin/env python3
"""
测试重构后的Android TV Box管理页面
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_refactored_page():
    """测试重构后的页面功能"""
    print("🚀 测试重构后的Android TV Box管理页面")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 测试主页面加载
        print("1. 测试主页面加载...")
        try:
            async with session.get('http://localhost:3003') as response:
                if response.status == 200:
                    content = await response.text()
                    if 'Android TV Box Management' in content and 'connection-status' in content:
                        print("   ✅ 主页面加载成功")
                        print(f"   📄 页面大小: {len(content)} 字符")
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
                    if data.get('success') and 'data' in data:
                        status_data = data['data']
                        print("   ✅ API端点正常")
                        print(f"   📊 设备状态:")
                        print(f"      - ADB连接: {'✅' if status_data.get('adb_connected') else '❌'}")
                        print(f"      - 设备电源: {'✅' if status_data.get('device_powered_on') else '❌'}")
                        print(f"      - WiFi状态: {'✅' if status_data.get('wifi_enabled') else '❌'}")
                        print(f"      - 当前应用: {status_data.get('current_app', 'Unknown')}")
                        print(f"      - iSG状态: {'✅' if status_data.get('isg_running') else '❌'}")
                    else:
                        print("   ❌ API返回数据格式错误")
                else:
                    print(f"   ❌ API端点失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ API端点错误: {e}")
        
        # 测试静态资源
        print("\n3. 测试静态资源...")
        try:
            async with session.get('http://localhost:3003/static/test_web_api.html') as response:
                if response.status == 200:
                    print("   ✅ 静态资源访问正常")
                else:
                    print(f"   ❌ 静态资源访问失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 静态资源错误: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 重构后的页面测试完成！")
    print("\n📱 现在您可以:")
    print("   1. 打开浏览器访问 http://localhost:3003")
    print("   2. 查看实时设备状态更新")
    print("   3. 使用快速操作按钮")
    print("   4. 检查浏览器控制台的调试信息")

if __name__ == "__main__":
    asyncio.run(test_refactored_page())

