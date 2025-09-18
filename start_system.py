#!/usr/bin/env python3
"""
Start script for ISG Android Control system
This script handles Python path issues in Android box Termux environment
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to the project directory
os.chdir(current_dir)

# Import and run the main module
if __name__ == "__main__":
    try:
        from isg_android_control.run import main
        print("Starting ISG Android Control system...")
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're in the correct directory and all dependencies are installed.")
        print("Try running: pip3 install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting system: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
