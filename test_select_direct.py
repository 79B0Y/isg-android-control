#!/usr/bin/env python3
"""直接测试select应用切换功能"""
import asyncio
import sys
import os

# 添加路径以便导入自定义组件
sys.path.append('/home/bo/isg-android-control')

from custom_components.android_tv_box.adb_service import ADBService

async def test_app_switching():
    """测试应用切换功能"""
    print("=== 直接测试应用切换功能 ===")
    
    # 初始化ADB服务
    adb_service = ADBService(host="192.168.188.221", port=5555)
    connected = await adb_service.connect()
    
    if not connected:
        print("❌ ADB连接失败")
        return
    
    print("✅ ADB连接成功")
    
    # 获取当前应用
    current_app = await adb_service.get_current_app()
    print(f"📱 当前应用: {current_app}")
    
    # 测试应用列表
    test_apps = {
        "YouTube": "com.google.android.youtube.tv",
        "Spotify": "com.spotify.music", 
        "Settings": "com.android.tv.settings"
    }
    
    for app_name, package_name in test_apps.items():
        print(f"\n🚀 测试启动 {app_name} ({package_name})")
        
        try:
            success = await adb_service.launch_app(package_name)
            if success:
                print(f"✅ {app_name} 启动命令发送成功")
                
                # 等待应用启动
                await asyncio.sleep(3)
                
                # 验证应用是否切换
                new_app = await adb_service.get_current_app()
                if package_name in (new_app or ""):
                    print(f"🎉 {app_name} 切换成功！当前应用: {new_app}")
                else:
                    print(f"⚠️ {app_name} 可能未成功切换，当前应用: {new_app}")
            else:
                print(f"❌ {app_name} 启动失败")
                
        except Exception as e:
            print(f"💥 {app_name} 启动异常: {e}")
        
        # 短暂等待
        await asyncio.sleep(2)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_app_switching())