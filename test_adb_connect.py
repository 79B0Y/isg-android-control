#!/usr/bin/env python3
"""
测试ADB连接功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_adb_connect():
    """测试ADB连接功能"""
    print("🔌 测试ADB连接功能")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 测试1: 断开ADB连接
        print("1. 断开ADB连接...")
        import subprocess
        try:
            result = subprocess.run(['adb', 'disconnect', '192.168.188.221:5555'], 
                                 capture_output=True, text=True)
            print(f"   ✅ ADB断开: {result.stdout.strip()}")
        except Exception as e:
            print(f"   ❌ ADB断开失败: {e}")
        
        # 测试2: 检查断开后的状态
        print("\n2. 检查断开后的状态...")
        try:
            async with session.get('http://localhost:3003/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        adb_connected = data['data'].get('adb_connected', False)
                        print(f"   📊 ADB连接状态: {'✅ 已连接' if adb_connected else '❌ 已断开'}")
                    else:
                        print("   ❌ 状态API失败")
                else:
                    print(f"   ❌ 状态API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 状态API异常: {e}")
        
        # 测试3: 使用Web API连接ADB
        print("\n3. 使用Web API连接ADB...")
        try:
            async with session.post('http://localhost:3003/api/connect-adb', 
                                  json={'host': '192.168.188.221', 'port': 5555}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ ADB连接成功!")
                        print(f"   📝 消息: {data.get('message', '')}")
                    else:
                        print("   ❌ ADB连接失败")
                        print(f"   📝 错误: {data.get('error', '')}")
                else:
                    print(f"   ❌ ADB连接API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ ADB连接API异常: {e}")
        
        # 测试4: 验证连接后的状态
        print("\n4. 验证连接后的状态...")
        try:
            async with session.get('http://localhost:3003/api/status') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        status_data = data['data']
                        adb_connected = status_data.get('adb_connected', False)
                        device_powered = status_data.get('device_powered_on', False)
                        current_app = status_data.get('current_app', 'Unknown')
                        
                        print(f"   📊 ADB连接状态: {'✅ 已连接' if adb_connected else '❌ 已断开'}")
                        print(f"   📱 设备电源: {'✅ 开启' if device_powered else '❌ 关闭'}")
                        print(f"   📱 当前应用: {current_app}")
                    else:
                        print("   ❌ 状态API失败")
                else:
                    print(f"   ❌ 状态API错误: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 状态API异常: {e}")
        
        # 测试5: 验证系统ADB连接
        print("\n5. 验证系统ADB连接...")
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if '192.168.188.221:5555' in result.stdout:
                print("   ✅ 系统ADB连接正常")
                print(f"   📱 设备列表:\n{result.stdout}")
            else:
                print("   ❌ 系统ADB连接异常")
                print(f"   📱 设备列表:\n{result.stdout}")
        except Exception as e:
            print(f"   ❌ 系统ADB检查失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 ADB连接功能测试完成！")
    print("\n📱 现在您可以:")
    print("   1. 打开浏览器访问 http://localhost:3003")
    print("   2. 在Dashboard页面点击'Connect ADB'按钮")
    print("   3. 查看连接状态和结果提示")
    print("   4. 连接成功后状态会自动更新")
    print("   5. 如果连接失败，会显示错误信息")

if __name__ == "__main__":
    asyncio.run(test_adb_connect())

