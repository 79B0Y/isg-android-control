#!/usr/bin/env python3
"""
Start only the API server for ISG Android Control system
This script starts only the FastAPI server without MQTT and other services
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

if __name__ == "__main__":
    try:
        from isg_android_control.api.main import create_app
        import uvicorn
        
        print("Starting ISG Android Control API server...")
        
        # Create the FastAPI app
        app = create_app()
        
        # Start the server
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're in the correct directory and all dependencies are installed.")
        print("Try running: pip3 install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting API server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
