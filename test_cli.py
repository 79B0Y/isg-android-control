#!/usr/bin/env python3
"""
测试CLI命令功能
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, timeout=10):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def test_cli_commands():
    """测试CLI命令"""
    print("🧪 测试iSG Android Controller CLI命令")
    print("=" * 50)
    
    # 检查命令是否存在
    cli_path = Path("./isg-android-control")
    if not cli_path.exists():
        print("❌ CLI命令文件不存在")
        return False
    
    if not cli_path.is_file():
        print("❌ CLI命令不是文件")
        return False
    
    # 测试帮助命令
    print("\n📋 测试帮助信息:")
    code, stdout, stderr = run_command("./isg-android-control --help")
    if code == 0:
        print("✅ 帮助命令正常")
        print("输出:")
        print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
    else:
        print(f"❌ 帮助命令失败: {stderr}")
        return False
    
    # 测试status命令（服务未运行时）
    print("\n📊 测试状态命令 (服务停止时):")
    code, stdout, stderr = run_command("./isg-android-control status")
    if code == 3:  # 3表示服务未运行
        print("✅ 状态命令正常 (服务未运行)")
    elif code == 0:
        print("ℹ️ 服务正在运行")
    else:
        print(f"❌ 状态命令失败: {stderr}")
    
    # 测试详细状态
    print("\n📊 测试详细状态:")
    code, stdout, stderr = run_command("./isg-android-control status -d")
    if code in [0, 3]:
        print("✅ 详细状态命令正常")
        print("输出:")
        lines = stdout.split('\n')[:10]  # 只显示前10行
        for line in lines:
            if line.strip():
                print(f"  {line}")
    else:
        print(f"❌ 详细状态命令失败: {stderr}")
    
    # 测试start命令的参数解析（不实际启动）
    print("\n🚀 测试start命令参数:")
    code, stdout, stderr = run_command("./isg-android-control start --help")
    if code == 0:
        print("✅ start命令帮助正常")
    else:
        print(f"❌ start命令帮助失败: {stderr}")
    
    # 测试stop命令的参数解析
    print("\n🛑 测试stop命令参数:")
    code, stdout, stderr = run_command("./isg-android-control stop --help")
    if code == 0:
        print("✅ stop命令帮助正常")
    else:
        print(f"❌ stop命令帮助失败: {stderr}")
    
    # 测试uninstall命令的参数解析
    print("\n🗑️ 测试uninstall命令参数:")
    code, stdout, stderr = run_command("./isg-android-control uninstall --help")
    if code == 0:
        print("✅ uninstall命令帮助正常")
    else:
        print(f"❌ uninstall命令帮助失败: {stderr}")
    
    print("\n" + "=" * 50)
    print("🎉 CLI命令测试完成!")
    print("使用方法:")
    print("  isg-android-control start     # 启动服务")
    print("  isg-android-control status    # 查看状态")
    print("  isg-android-control stop      # 停止服务")
    print("  isg-android-control restart   # 重启服务")
    print("  isg-android-control uninstall # 卸载服务")
    
    return True

def test_environment():
    """测试运行环境"""
    print("🔍 检查运行环境:")
    
    # 检查Python版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  Python版本: {python_version}")
    
    # 检查依赖模块
    required_modules = ['psutil', 'pathlib']
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} (缺失)")
    
    # 检查文件权限
    cli_path = Path("./isg-android-control")
    if cli_path.exists():
        import stat
        mode = cli_path.stat().st_mode
        if mode & stat.S_IEXEC:
            print("  ✅ CLI命令有执行权限")
        else:
            print("  ❌ CLI命令无执行权限")
            print("  修复: chmod +x ./isg-android-control")
    
    return True

if __name__ == "__main__":
    print("iSG Android Controller - CLI测试工具")
    print("=" * 50)
    
    # 检查环境
    test_environment()
    print()
    
    # 测试CLI命令
    test_cli_commands()