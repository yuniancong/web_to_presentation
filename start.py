#!/usr/bin/env python3
"""
Startup script for Web to Presentation Converter
Automatically starts API server and opens frontend in browser
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
API_SERVER_PATH = PROJECT_ROOT / 'src' / 'api_server.py'
FRONTEND_URL = 'http://localhost:5000'
API_URL = 'http://localhost:5000'


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"  ✓ Node.js: {result.stdout.strip()}")
    except FileNotFoundError:
        print("  ❌ Node.js not found! Please install Node.js first.")
        sys.exit(1)

    # Check Python packages
    required_packages = ['flask', 'flask_cors', 'pptx', 'PIL']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package if package != 'PIL' else 'PIL')
            print(f"  ✓ Python package: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ Python package missing: {package}")

    if missing_packages:
        print("\n📦 Installing missing Python packages...")
        pip_packages = {
            'flask': 'flask',
            'flask_cors': 'flask-cors',
            'pptx': 'python-pptx',
            'PIL': 'Pillow'
        }

        for package in missing_packages:
            pip_package = pip_packages.get(package, package)
            print(f"  Installing {pip_package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pip_package])

    # Check Node modules
    node_modules = PROJECT_ROOT / 'node_modules'
    if not node_modules.exists():
        print("\n📦 Installing Node.js dependencies...")
        subprocess.run(['npm', 'install'], cwd=PROJECT_ROOT)
    else:
        print("  ✓ Node.js modules installed")

    print()


def start_api_server():
    """Start the Flask API server in background"""
    print("🚀 Starting API server...")

    # Start server as subprocess
    process = subprocess.Popen(
        [sys.executable, str(API_SERVER_PATH)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    time.sleep(2)

    # Check if server is running
    if process.poll() is None:
        print(f"  ✓ API server started at {API_URL}")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"  ❌ Failed to start API server")
        print(f"  Error: {stderr}")
        sys.exit(1)


def open_frontend():
    """Open frontend in default browser"""
    print("🌐 Opening frontend...")
    time.sleep(1)

    try:
        webbrowser.open(FRONTEND_URL)
        print(f"  ✓ Frontend opened: {FRONTEND_URL}")
    except Exception as e:
        print(f"  ⚠ Could not auto-open browser: {e}")
        print(f"  Please manually open: {FRONTEND_URL}")


def main():
    """Main startup sequence"""
    print("=" * 60)
    print("🎨 Web to Presentation Converter")
    print("=" * 60)
    print()

    # Check dependencies
    check_dependencies()

    # Start API server
    api_process = start_api_server()

    # Open frontend
    open_frontend()

    print()
    print("=" * 60)
    print("✅ Application started successfully!")
    print("=" * 60)
    print()
    print(f"📊 Frontend: {FRONTEND_URL}")
    print(f"🔧 API Server: {API_URL}")
    print()
    print("Press Ctrl+C to stop the application")
    print()

    try:
        # Keep the script running and monitor API server
        while True:
            time.sleep(1)
            if api_process.poll() is not None:
                print("\n⚠ API server stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping application...")
        api_process.terminate()
        api_process.wait()
        print("✅ Application stopped")


if __name__ == '__main__':
    main()
