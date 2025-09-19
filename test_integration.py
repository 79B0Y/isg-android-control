#!/usr/bin/env python3
"""
Android TV Box Integration Test Script
测试Android TV Box集成的基本功能
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

class AndroidTVBoxTester:
    def __init__(self, ha_url="http://localhost:8123"):
        self.ha_url = ha_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_ha_connection(self):
        """测试Home Assistant连接"""
        print("🔍 测试Home Assistant连接...")
        try:
            async with self.session.get(f"{self.ha_url}/api/") as response:
                if response.status == 200:
                    print("✅ Home Assistant连接成功")
                    return True
                else:
                    print(f"❌ Home Assistant连接失败: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Home Assistant连接错误: {e}")
            return False
    
    async def test_android_tv_box_entities(self):
        """测试Android TV Box实体"""
        print("\n🔍 测试Android TV Box实体...")
        try:
            async with self.session.get(f"{self.ha_url}/api/states") as response:
                if response.status == 200:
                    states = await response.json()
                    android_entities = [state for state in states if 'android_tv_box' in state['entity_id']]
                    
                    if android_entities:
                        print(f"✅ 找到 {len(android_entities)} 个Android TV Box实体:")
                        for entity in android_entities:
                            print(f"   - {entity['entity_id']}: {entity['state']}")
                        return True
                    else:
                        print("❌ 未找到Android TV Box实体")
                        return False
                else:
                    print(f"❌ 获取实体状态失败: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 测试实体时出错: {e}")
            return False
    
    async def test_adb_connection(self):
        """测试ADB连接"""
        print("\n🔍 测试ADB连接...")
        try:
            import subprocess
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
                devices = [line for line in lines if line.strip() and 'device' in line]
                
                if devices:
                    print(f"✅ ADB连接成功，找到 {len(devices)} 个设备:")
                    for device in devices:
                        print(f"   - {device}")
                    return True
                else:
                    print("❌ ADB未找到连接的设备")
                    return False
            else:
                print(f"❌ ADB命令执行失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ ADB测试出错: {e}")
            return False
    
    async def test_web_interface(self):
        """测试Web管理界面"""
        print("\n🔍 测试Web管理界面...")
        try:
            # 测试端口3003是否开放
            async with self.session.get("http://localhost:3003") as response:
                if response.status == 200:
                    print("✅ Web管理界面可访问 (http://localhost:3003)")
                    return True
                else:
                    print(f"❌ Web管理界面不可访问: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Web管理界面测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Android TV Box集成测试")
        print("=" * 50)
        
        tests = [
            ("Home Assistant连接", self.test_ha_connection),
            ("ADB连接", self.test_adb_connection),
            ("Android TV Box实体", self.test_android_tv_box_entities),
            ("Web管理界面", self.test_web_interface),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results.append((test_name, False))
        
        # 输出测试结果摘要
        print("\n" + "=" * 50)
        print("📊 测试结果摘要:")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！Android TV Box集成运行正常")
            print("\n📱 接下来您可以:")
            print("   1. 打开浏览器访问 http://localhost:8123 使用Home Assistant")
            print("   2. 访问 http://localhost:3003 使用Web管理界面")
            print("   3. 在Home Assistant中添加Android TV Box设备")
        else:
            print("⚠️  部分测试失败，请检查配置")
        
        return passed == total

async def main():
    """主函数"""
    print(f"🕐 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with AndroidTVBoxTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
