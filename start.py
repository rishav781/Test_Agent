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
from pathlib import Path
from dotenv import load_dotenv

def get_project_root():
    """Get the project root directory"""
    current_path = Path(__file__).resolve()
    for parent in [current_path] + list(current_path.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
    return Path(__file__).parent

# Load environment variables from env/.env file
project_root = get_project_root()
env_file = project_root / 'env' / '.env'
load_dotenv(dotenv_path=env_file)

def select_environment():
    """Ask user to select environment"""
    print("🤖 Pcloudy Test Case Agent - Environment Selection")
    print("=" * 55)

    # Show available environments
    project_root = get_project_root()
    env_dir = project_root / 'env'

    if not env_dir.exists():
        print("❌ No env folder found! Please run from project root.")
        sys.exit(1)

    env_files = list(env_dir.glob('.env.*'))
    if not env_files:
        print("❌ No environment files found in env folder!")
        print("   Please create .env.development and .env.production files")
        sys.exit(1)

    available_envs = [f.name.replace('.env.', '') for f in env_files]
    print(f"📁 Available environments: {', '.join(available_envs)}")

    # Check current environment
    current_env_file = env_dir / '.env'
    current_env = "none"
    if current_env_file.exists():
        try:
            with open(current_env_file, 'r') as f:
                for line in f:
                    if line.startswith('ENV='):
                        current_env = line.split('=')[1].strip()
                        break
        except:
            pass

    print(f"🔧 Current environment: {current_env}")
    print()

    # Ask user for selection
    while True:
        env_input = input("Which environment would you like to start? (development/production): ").strip().lower()

        if env_input in available_envs:
            return env_input
        elif env_input == '':
            # Default to development if user just presses enter
            if 'development' in available_envs:
                print("ℹ️  Defaulting to development environment")
                return 'development'
            else:
                print("❌ No development environment available, please specify")
        else:
            print(f"❌ Invalid environment '{env_input}'. Available: {', '.join(available_envs)}")

def load_configuration():
    """Load configuration after environment is set"""
    # Add backend to path for config import
    backend_path = Path(__file__).parent / "backend" / "src"
    sys.path.insert(0, str(backend_path))

    try:
        from config import config
        print("✅ Configuration loaded successfully")
        print(f"   Environment: {config.env}")
        print(f"   Backend: {config.backend_url}")
        print(f"   Frontend: {config.frontend_url}")
        return config
    except ImportError as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)

def switch_environment(env_name):
    """Switch to the specified environment by copying the appropriate .env file"""
    project_root = get_project_root()
    env_dir = project_root / 'env'
    source_file = env_dir / f'.env.{env_name}'
    target_file = env_dir / '.env'

    try:
        # Copy the environment file
        import shutil
        shutil.copy2(source_file, target_file)
        return True
    except Exception as e:
        print(f"❌ Error switching environment: {e}")
        return False

def start_backend(config):
    """Start the backend Flask API server"""
    print("🚀 Starting Backend API Server...")
    backend_cmd = [sys.executable, "backend/src/server.py"]
    return subprocess.Popen(backend_cmd, cwd=config.project_root)

def start_frontend(config):
    """Start the frontend HTTP server"""
    print("🌐 Starting Frontend Server...")
    frontend_cmd = [sys.executable, "server_api.py"]
    return subprocess.Popen(frontend_cmd, cwd=config.project_root)

def main():
    """Main function to start both servers"""
    # Select environment first
    selected_env = select_environment()

    # Switch to selected environment
    print(f"🔄 Switching to {selected_env} environment...")
    if not switch_environment(selected_env):
        print(f"❌ Failed to switch to {selected_env} environment")
        sys.exit(1)
    print(f"✅ Successfully switched to {selected_env} environment")
    print()

    # Now load configuration
    config = load_configuration()
    print()

    print("🤖 Pcloudy Test Case Agent - Starting Services")
    print("=" * 50)
    print(f"🌍 Environment: {config.env}")
    print(f"🔧 Debug Mode: {'ENABLED' if config.flask_debug else 'DISABLED'}")

    if config.is_production:
        print("🏭 PRODUCTION MODE DETECTED")
        print("⚠️  Using production configuration...")
        print("💡 Production deployment recommendations:")
        print("   1. Use gunicorn: gunicorn --bind 0.0.0.0:8000 --workers 4 backend.src.app:app")
        print("   2. Use nginx as reverse proxy")
        print("   3. Set up SSL certificates")
        print("   4. Configure proper logging")
        print()

    # Start backend server
    backend_process = start_backend(config)
    time.sleep(2)  # Wait for backend to start

    # Start frontend server (only in development)
    if config.is_development:
        frontend_process = start_frontend(config)
        time.sleep(1)  # Wait for frontend to start
    else:
        frontend_process = None
        print("🌐 Frontend served by nginx")

    print("\n✅ Services Started Successfully!")
    print(f"📱 Frontend: {config.frontend_url}")
    print(f"🔧 Backend API: {config.backend_url}")

    if config.is_production:
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
        if frontend_process:
            frontend_process.terminate()

        # Wait for processes to finish
        backend_process.wait()
        if frontend_process:
            frontend_process.wait()

        print("👋 All services stopped. Goodbye!")

if __name__ == "__main__":
    main()