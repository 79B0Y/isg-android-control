#!/usr/bin/env python3
"""
依赖检查脚本
检查所有必需的Python包是否正确安装
"""

import sys
import importlib
import subprocess
from typing import List, Tuple, Optional


def check_python_version() -> bool:
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 9):
        print("✓ Python版本满足要求 (>= 3.9)")
        return True
    else:
        print("✗ Python版本过低，需要 >= 3.9")
        return False


def check_package(package_name: str, import_name: Optional[str] = None) -> bool:
    """检查单个包是否可导入"""
    try:
        module_name = import_name or package_name
        importlib.import_module(module_name)
        print(f"✓ {package_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name}: {e}")
        return False


def get_package_version(package_name: str) -> Optional[str]:
    """获取包版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return None


def check_core_dependencies() -> List[Tuple[str, bool]]:
    """检查核心依赖"""
    print("\n检查核心依赖包:")
    print("-" * 40)
    
    dependencies = [
        ("fastapi", None),
        ("uvicorn", None),
        ("pydantic", None),
        ("pydantic-settings", "pydantic_settings"),
        ("redis", None),
        ("paho-mqtt", "paho.mqtt.client"),
        ("asyncio-mqtt", "asyncio_mqtt"),
        ("Pillow", "PIL"),
        ("aiofiles", None),
        ("python-multipart", "multipart"),
        ("httpx", None),
        ("PyYAML", "yaml"),
        ("python-dotenv", "dotenv"),
        ("loguru", None),
        ("click", None),
        ("psutil", None),
    ]
    
    results = []
    for package, import_name in dependencies:
        success = check_package(package, import_name)
        results.append((package, success))
    
    return results


def check_optional_dependencies() -> List[Tuple[str, bool]]:
    """检查可选依赖"""
    print("\n检查可选依赖包 (开发/测试):")
    print("-" * 40)
    
    dependencies = [
        ("pytest", None),
        ("pytest-asyncio", None),
        ("pytest-cov", None),
        ("pytest-mock", None),
        ("black", None),
        ("isort", None),
        ("flake8", None),
        ("mypy", None),
    ]
    
    results = []
    for package, import_name in dependencies:
        success = check_package(package, import_name)
        results.append((package, success))
    
    return results


def check_system_commands() -> List[Tuple[str, bool]]:
    """检查系统命令"""
    print("\n检查系统命令:")
    print("-" * 40)
    
    commands = ["adb", "redis-server", "curl", "wget"]
    results = []
    
    for cmd in commands:
        try:
            result = subprocess.run(
                ["which", cmd],
                capture_output=True,
                text=True
            )
            success = result.returncode == 0
            if success:
                path = result.stdout.strip()
                print(f"✓ {cmd}: {path}")
            else:
                print(f"✗ {cmd}: 未找到")
            results.append((cmd, success))
        except Exception as e:
            print(f"✗ {cmd}: 检查失败 - {e}")
            results.append((cmd, False))
    
    return results


def test_basic_imports():
    """测试基本模块导入"""
    print("\n测试项目模块导入:")
    print("-" * 40)
    
    # 添加项目路径
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    modules_to_test = [
        "src.core.config",
        "src.core.logger",
        "src.core.adb_controller",
        "src.core.device_controller",
        "src.models.requests",
        "src.models.responses",
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
            success_count += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
    
    print(f"\n模块导入测试: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)


def generate_report(core_deps: List[Tuple[str, bool]], 
                   optional_deps: List[Tuple[str, bool]],
                   system_cmds: List[Tuple[str, bool]],
                   modules_ok: bool):
    """生成检查报告"""
    print("\n" + "=" * 50)
    print("依赖检查报告")
    print("=" * 50)
    
    # 核心依赖统计
    core_success = sum(1 for _, success in core_deps if success)
    core_total = len(core_deps)
    print(f"核心依赖: {core_success}/{core_total} 成功")
    
    if core_success < core_total:
        print("缺失的核心依赖:")
        for package, success in core_deps:
            if not success:
                version = get_package_version(package)
                print(f"  - {package} {f'(当前版本: {version})' if version else '(未安装)'}")
    
    # 可选依赖统计
    optional_success = sum(1 for _, success in optional_deps if success)
    optional_total = len(optional_deps)
    print(f"可选依赖: {optional_success}/{optional_total} 成功")
    
    # 系统命令统计
    cmd_success = sum(1 for _, success in system_cmds if success)
    cmd_total = len(system_cmds)
    print(f"系统命令: {cmd_success}/{cmd_total} 可用")
    
    if cmd_success < cmd_total:
        print("缺失的系统命令:")
        for cmd, success in system_cmds:
            if not success:
                print(f"  - {cmd}")
    
    # 模块导入
    print(f"项目模块: {'✓ 通过' if modules_ok else '✗ 失败'}")
    
    # 总体状态
    print("\n" + "-" * 50)
    if core_success == core_total and modules_ok:
        print("✓ 所有必需依赖都已满足，可以启动服务")
        return True
    else:
        print("✗ 存在缺失的依赖，请先安装")
        print("\n安装建议:")
        print("1. 运行: pip install -r requirements.txt")
        print("2. 检查系统包管理器安装缺失的系统命令")
        print("3. 重新运行此脚本验证")
        return False


def main():
    """主函数"""
    print("Android Controller Service - 依赖检查")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查各类依赖
    core_deps = check_core_dependencies()
    optional_deps = check_optional_dependencies()
    system_cmds = check_system_commands()
    modules_ok = test_basic_imports()
    
    # 生成报告
    success = generate_report(core_deps, optional_deps, system_cmds, modules_ok)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()