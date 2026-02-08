#!/usr/bin/env python3
"""
VibeCoder Backend Launcher
Starts the backend server with proper configuration
"""
import os
import sys
import subprocess

# Change to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Python executable path
PYTHON_EXE = "C:/Users/annam/vibecober/.venv/Scripts/python.exe"

def main():
    print("=" * 60)
    print("🚀 Starting VibeCoder Backend Server")
    print("=" * 60)
    print()
    print("Backend will run on: http://0.0.0.0:8000")
    print("API Status: http://localhost:8000/api/status")
    print("Press CTRL+C to stop the server")
    print()
    print("=" * 60)
    print()
    
    try:
        # Start uvicorn server
        subprocess.run([
            PYTHON_EXE,
            "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"  # Auto-reload on code changes
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user")
    except FileNotFoundError:
        print(f"[ERROR] Python executable not found: {PYTHON_EXE}")
        print("[INFO] Please activate the virtual environment:")
        print("       .venv/Scripts/Activate.ps1")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
