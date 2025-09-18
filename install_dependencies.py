#!/usr/bin/env python3
"""
Install dependencies for ISG Android Control system
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def check_python_packages():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python packages...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pyyaml",
        "asyncio",
        "aiofiles"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - missing")
            missing_packages.append(package)
    
    return missing_packages

def install_python_packages():
    """Install Python packages from requirements.txt"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print(f"📋 Found requirements.txt")
    
    # Install packages
    return run_command("pip3 install -r requirements.txt", "Installing Python packages")

def check_adb():
    """Check if ADB is installed and working"""
    print("🔍 Checking ADB...")
    
    # Check if adb command exists
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ ADB installed: {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ ADB command failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("   ❌ ADB not found in PATH")
        return False

def setup_python_path():
    """Setup Python path for the project"""
    print("🔧 Setting up Python path...")
    
    # Create a simple test to verify Python path
    test_script = """
import sys
from pathlib import Path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
try:
    from isg_android_control.core.adb import ADBController
    print("✅ Python path setup successful")
except ImportError as e:
    print(f"❌ Python path setup failed: {e}")
"""
    
    with open("test_python_path.py", "w") as f:
        f.write(test_script)
    
    try:
        result = subprocess.run([sys.executable, "test_python_path.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   {result.stdout.strip()}")
            os.remove("test_python_path.py")
            return True
        else:
            print(f"   ❌ Python path test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Python path test error: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 ISG Android Control - Dependency Installation")
    print("=" * 50)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in the right directory
    if not (current_dir / "src" / "isg_android_control").exists():
        print("❌ Not in the correct directory. Please run this script from the project root.")
        return 1
    
    print("✅ Project structure looks correct")
    
    # Check Python packages
    missing_packages = check_python_packages()
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        if not install_python_packages():
            print("❌ Failed to install Python packages")
            return 1
    else:
        print("✅ All Python packages are installed")
    
    # Check ADB
    if not check_adb():
        print("\n⚠️  ADB is not installed or not working")
        print("Please install ADB:")
        print("  - Ubuntu/Debian: sudo apt install android-tools-adb")
        print("  - Termux: pkg install android-tools")
        print("  - Or download from: https://developer.android.com/studio/releases/platform-tools")
    
    # Setup Python path
    if not setup_python_path():
        print("❌ Python path setup failed")
        return 1
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("  1. Test ADB connection: python3 test_adb_android_box.py")
    print("  2. Start the system: python3 start_system.py")
    
    return 0

if __name__ == "__main__":
    exit(main())
