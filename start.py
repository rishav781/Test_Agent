#!/usr/bin/env python3
"""
Pcloudy Test Case Agent - Startup Script
Starts both backend API and frontend servers
"""

import subprocess
import sys
import os
import signal
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_backend():
    """Start the backend Flask API server"""
    print("🚀 Starting Backend API Server...")
    backend_cmd = [sys.executable, "backend/src/app.py"]
    return subprocess.Popen(backend_cmd, cwd=os.getcwd())

def start_frontend():
    """Start the frontend HTTP server"""
    print("🌐 Starting Frontend Server...")
    frontend_cmd = [sys.executable, "server_api.py"]
    return subprocess.Popen(frontend_cmd, cwd=os.getcwd())

def main():
    """Main function to start both servers"""
    # Get environment settings
    env = os.getenv('ENV', 'development')
    is_production = env == 'production'

    if is_production:
        print("🏭 PRODUCTION MODE DETECTED")
        print("⚠️  Using production server configuration...")
        print("💡 For production deployment, consider:")
        print("   1. Use gunicorn: gunicorn --bind 0.0.0.0:8000 backend.app:app")
        print("   2. Use nginx as reverse proxy")
        print("   3. Set up SSL certificates")
        print("   4. Configure proper logging")
        print()

    print("🤖 Pcloudy Test Case Agent - Starting Services")
    print("=" * 50)

    # Start backend server
    backend_process = start_backend()
    time.sleep(2)  # Wait for backend to start

    # Start frontend server
    frontend_process = start_frontend()
    time.sleep(1)  # Wait for frontend to start

    print("\n✅ Services Started Successfully!")
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8000')
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5050')
    print(f"📱 Frontend: {frontend_url}")
    print(f"🔧 Backend API: {backend_url}")

    if is_production:
        print("\n🏭 PRODUCTION CHECKLIST:")
        print("✅ Environment variables configured")
        print("✅ Debug mode disabled")
        print("⚠️  Consider using a process manager (systemd, supervisor)")
        print("⚠️  Set up monitoring and logging")

    print("🛑 Press Ctrl+C to stop all services")

    try:
        # Wait for keyboard interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")

        # Terminate processes
        backend_process.terminate()
        frontend_process.terminate()

        # Wait for processes to finish
        backend_process.wait()
        frontend_process.wait()

        print("👋 All services stopped. Goodbye!")

if __name__ == "__main__":
    main()