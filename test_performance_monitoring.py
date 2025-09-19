#!/usr/bin/env python3
"""测试性能监控改进"""
import asyncio
import sys
import os

# 添加路径以便导入自定义组件
sys.path.append('/home/bo/isg-android-control')

from custom_components.android_tv_box.adb_service import ADBService

async def test_performance_monitoring():
    """测试性能监控功能改进"""
    print("=== 测试性能监控功能改进 ===")
    
    # 初始化ADB服务
    adb_service = ADBService(host="192.168.188.221", port=5555)
    connected = await adb_service.connect()
    
    if not connected:
        print("❌ ADB连接失败")
        return
    
    print("✅ ADB连接成功")
    
    # 测试系统性能获取
    print("\n🔍 测试系统性能获取...")
    try:
        performance = await adb_service.get_system_performance()
        print(f"📊 性能数据:")
        print(f"  CPU使用率: {performance['cpu_usage_percent']}%")
        print(f"  内存使用率: {performance['memory_usage_percent']}%")
        print(f"  内存总量: {performance['memory_total_mb']} MB")
        print(f"  内存已用: {performance['memory_used_mb']} MB")
        print(f"  最高CPU进程: {performance['highest_cpu_process']}")
        print(f"  最高CPU进程PID: {performance['highest_cpu_pid']}")
        print(f"  最高CPU进程使用率: {performance['highest_cpu_percent']}%")
        print(f"  最高CPU进程服务名: {performance['highest_cpu_service']}")
        
        # 验证数据类型和范围
        success = True
        if not isinstance(performance['cpu_usage_percent'], (int, float)) or performance['cpu_usage_percent'] < 0:
            print("❌ CPU使用率数据类型或范围错误")
            success = False
        
        if not isinstance(performance['memory_usage_percent'], (int, float)) or performance['memory_usage_percent'] < 0 or performance['memory_usage_percent'] > 100:
            print("❌ 内存使用率数据类型或范围错误")
            success = False
        
        if success:
            print("✅ 性能数据获取成功且格式正确")
        else:
            print("❌ 性能数据格式有问题")
            
    except Exception as e:
        print(f"❌ 性能数据获取失败: {e}")
    
    # 测试ADB连接状态检查
    print("\n🔗 测试ADB连接状态检查...")
    try:
        is_connected = await adb_service.is_connected()
        print(f"ADB连接状态: {'✅ 已连接' if is_connected else '❌ 未连接'}")
    except Exception as e:
        print(f"❌ 连接状态检查失败: {e}")
    
    # 测试服务名反查功能
    print("\n🔍 测试服务名反查功能...")
    if performance.get('highest_cpu_pid'):
        try:
            service_name = await adb_service._get_service_name_by_pid(performance['highest_cpu_pid'])
            print(f"PID {performance['highest_cpu_pid']} 对应服务名: {service_name}")
        except Exception as e:
            print(f"❌ 服务名反查失败: {e}")
    else:
        print("⚠️ 没有找到最高CPU进程PID，跳过服务名反查测试")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_performance_monitoring())