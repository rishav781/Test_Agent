#!/usr/bin/env python3
"""
Enhanced Production Deployment Script for Pcloudy Test Case Agent
This script creates virtual environment, installs dependencies with UV (preferred) or pip, and starts servers
Works on any system with Python 3.12+ with automatic fallback from UV to pip
"""

import os
import sys
import subprocess
import argparse
import platform
import venv
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent

def get_venv_path():
    """Get the virtual environment path"""
    return get_project_root() / ".venv"

def get_python_executable():
    """Get the Python executable path for the virtual environment"""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_pip_executable():
    """Get the pip executable path for the virtual environment"""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 12):
        print(f"❌ Python 3.12+ is required. Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = get_venv_path()
    
    if venv_path.exists():
        print(f"✅ Virtual environment already exists at: {venv_path}")
        return True
    
    print(f"🔧 Creating virtual environment at: {venv_path}")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies_with_uv():
    """Install dependencies using UV (preferred method)"""
    project_root = get_project_root()
    
    # Check if UV is available
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ℹ️  UV not available, falling back to pip")
        return False
    
    print("📦 Installing dependencies with UV...")
    
    try:
        # Install production dependencies with UV
        subprocess.run([
            "uv", "sync", "--group", "production"
        ], check=True, cwd=project_root)
        print("✅ All dependencies installed with UV")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to install with UV: {e}")
        print("ℹ️  Falling back to pip")
        return False

def install_dependencies_with_pip():
    """Install dependencies using pip from pyproject.toml (primary) or fallback methods"""
    project_root = get_project_root()
    pip_executable = get_pip_executable()
    
    if not pip_executable.exists():
        print(f"❌ Pip executable not found: {pip_executable}")
        return False
    
    print("📦 Installing dependencies with pip...")
    
    # First upgrade pip itself
    try:
        subprocess.run([
            str(pip_executable), "install", "--upgrade", "pip"
        ], check=True, cwd=project_root)
        print("✅ Pip upgraded to latest version")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to upgrade pip: {e}")
    
    # Primary: Try to install from pyproject.toml (editable mode)
    pyproject_toml = project_root / "pyproject.toml"
    if pyproject_toml.exists():
        print("📋 Installing from pyproject.toml (editable mode)...")
        try:
            subprocess.run([
                str(pip_executable), "install", "-e", "."
            ], check=True, cwd=project_root)
            print("✅ All dependencies installed from pyproject.toml")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to install from pyproject.toml: {e}")
            print("ℹ️  Falling back to manual dependency installation")
    
    # Fallback: Install core dependencies directly (if pyproject.toml fails)
    print("📦 Installing core dependencies directly...")
    core_deps = [
        "Flask>=2.3.0",
        "Flask-CORS>=4.0.0", 
        "openai>=1.3.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "gunicorn>=21.2.0",
        "gevent>=23.9.0"
    ]
    
    try:
        subprocess.run([
            str(pip_executable), "install"
        ] + core_deps, check=True, cwd=project_root)
        print("✅ Core dependencies installed directly")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install core dependencies: {e}")
        return False
    
    return True

def check_environment():
    """Check if production environment is properly configured"""
    env = os.getenv('ENV', 'development')
    if env != 'production':
        print("⚠️  WARNING: ENV is not set to 'production'")
        print("   Current ENV:", env)
        print("   Set ENV=production in your .env file for production deployment")
        return False
    return True

def get_port_from_user(prompt):
    """Prompt the user for a port and validate it."""
    while True:
        port_str = input(f"Enter the {prompt} port: ")
        if not port_str:
            print("❌ Port number is required.")
            continue
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return port
            else:
                print("❌ Invalid port. Please enter a number between 1 and 65535.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def start_production_backend(host='0.0.0.0', port=8000, workers=4):
    """Start the backend with gunicorn for production using virtual environment"""
    print(f"🚀 Starting production backend server on {host}:{port}")
    print(f"   Workers: {workers}")
    
    python_executable = get_python_executable()
    if not python_executable.exists():
        print(f"❌ Python executable not found in virtual environment: {python_executable}")
        return None

    # Set environment variable for the backend port
    os.environ['BACKEND_PORT'] = str(port)
    os.environ['BACKEND_URL'] = f"http://{host}:{port}"
    
    # Set PYTHONPATH to include backend/src
    project_root = get_project_root()
    backend_src = project_root / "backend" / "src"
    os.environ['PYTHONPATH'] = str(backend_src)

    cmd = [
        str(python_executable), "-m", "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
        "--worker-class", "gevent",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "backend.src.app:app"
    ]

    try:
        project_root = get_project_root()
        print(f"📁 Starting from directory: {project_root}")
        # Use Popen for non-blocking process management
        return subprocess.Popen(cmd, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
        return None
    except KeyboardInterrupt:
        print("\n🛑 Production server stopped")
        return None

def start_production_frontend(host='0.0.0.0', port=3000):
    """Start the frontend with production settings using virtual environment"""
    print(f"🌐 Starting production frontend server on {host}:{port}")
    
    python_executable = get_python_executable()
    if not python_executable.exists():
        print(f"❌ Python executable not found in virtual environment: {python_executable}")
        return None

    # Set production environment variables
    env = os.environ.copy()
    env['ENV'] = 'production'
    env['FRONTEND_PORT'] = str(port)
    env['FRONTEND_URL'] = f"http://{host}:{port}"

    cmd = [str(python_executable), "server_api.py"]
    try:
        project_root = get_project_root()
        print(f"📁 Starting from directory: {project_root}")
        # Use Popen for non-blocking process management
        return subprocess.Popen(cmd, cwd=project_root, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production frontend: {e}")
        return None
    except KeyboardInterrupt:
        print("\n🛑 Production frontend stopped")
        return None

def setup_deployment_environment():
    """Set up the complete deployment environment"""
    print("🔧 Setting up deployment environment...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Install dependencies (try UV first, fallback to pip)
    if not install_dependencies_with_uv():
        if not install_dependencies_with_pip():
            return False
    
    print("✅ Deployment environment setup complete!")
    return True

def main():
    parser = argparse.ArgumentParser(description='Enhanced production deployment for Pcloudy Test Case Agent')
    parser.add_argument('--backend-only', action='store_true',
                       help='Start only the backend server')
    parser.add_argument('--frontend-only', action='store_true',
                       help='Start only the frontend server')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of gunicorn workers (default: 4)')
    parser.add_argument('--skip-setup', action='store_true',
                       help='Skip virtual environment and dependency setup')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only setup environment, do not start servers')

    args = parser.parse_args()

    print("🏭 Pcloudy Test Case Agent - Enhanced Production Deployment")
    print("=" * 60)
    print("🔧 Creates virtual environment, installs dependencies, and starts servers")
    print("🌍 Compatible with any system running Python 3.12+")
    print("=" * 60)

    # Setup deployment environment unless skipped
    if not args.skip_setup:
        if not setup_deployment_environment():
            print("❌ Failed to setup deployment environment")
            sys.exit(1)
    
    # If setup-only, exit after setup
    if args.setup_only:
        print("✅ Environment setup complete. Use --skip-setup to start servers.")
        return

    # Check environment configuration
    if not check_environment():
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            sys.exit(1)

    # Get ports from user
    print("\n🔌 Port Configuration")
    print("=" * 30)
    
    backend_port = 8000
    frontend_port = 3000

    if not args.backend_only and not args.frontend_only:
        print("🔧 Configuring ports for both backend and frontend servers...")
        backend_port = get_port_from_user("backend")
        frontend_port = get_port_from_user("frontend")
    elif args.backend_only:
        print("🔧 Configuring port for backend server only...")
        backend_port = get_port_from_user("backend")
    elif args.frontend_only:
        print("🔧 Configuring port for frontend server only...")
        frontend_port = get_port_from_user("frontend")

    # Display configuration summary
    print(f"\n📋 Deployment Configuration")
    print("=" * 30)
    print(f"🌐 Host: {args.host}")
    if not args.frontend_only:
        print(f"🔧 Backend: http://{args.host}:{backend_port}")
        print(f"👥 Workers: {args.workers}")
    if not args.backend_only:
        print(f"🎨 Frontend: http://{args.host}:{frontend_port}")
    print(f"🐍 Python: {get_python_executable()}")
    print(f"📁 Project: {get_project_root()}")

    # Start services
    backend_process = None
    frontend_process = None

    try:
        print(f"\n🚀 Starting Services")
        print("=" * 30)
        
        if args.backend_only:
            backend_process = start_production_backend(args.host, backend_port, args.workers)
            if backend_process:
                print(f"✅ Backend server started successfully!")
                print("🛑 Press Ctrl+C to stop the server")
                backend_process.wait()
        elif args.frontend_only:
            frontend_process = start_production_frontend(args.host, frontend_port)
            if frontend_process:
                print(f"✅ Frontend server started successfully!")
                print("🛑 Press Ctrl+C to stop the server")
                frontend_process.wait()
        else:
            # Start backend first
            backend_process = start_production_backend(args.host, backend_port, args.workers)
            if backend_process:
                print(f"✅ Backend started on http://{args.host}:{backend_port}")
            else:
                print("❌ Failed to start backend server")
                return

            # Start frontend
            frontend_process = start_production_frontend(args.host, frontend_port)
            if frontend_process:
                print(f"✅ Frontend started on http://{args.host}:{frontend_port}")
            else:
                print("❌ Failed to start frontend server")
                if backend_process:
                    backend_process.terminate()
                return

            print(f"\n🎉 Both servers are running!")
            print(f"🔗 Frontend: http://{args.host}:{frontend_port}")
            print(f"🔗 Backend API: http://{args.host}:{backend_port}")
            print("🛑 Press Ctrl+C to stop all services")
            
            # Wait for processes
            try:
                if backend_process:
                    backend_process.wait()
            except:
                pass

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        if backend_process and backend_process.poll() is None:
            print("🔄 Stopping backend server...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        if frontend_process and frontend_process.poll() is None:
            print("🔄 Stopping frontend server...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        print("👋 All services stopped. Goodbye!")

if __name__ == "__main__":
    main()
