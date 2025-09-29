#!/usr/bin/env python3
"""
Production Deployment Script for Pcloudy Test Case Agent
This script handles production deployment with gunicorn and proper configuration
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_environment():
    """Check if production environment is properly configured"""
    env = os.getenv('ENV', 'development')
    if env != 'production':
        print("⚠️  WARNING: ENV is not set to 'production'")
        print("   Current ENV:", env)
        print("   Set ENV=production in your .env file for production deployment")
        return False
    return True

def install_dependencies(dep_group):
    """Install dependencies for specified group"""
    print(f"📦 Installing {dep_group} dependencies...")
    try:
        if dep_group == 'all':
            subprocess.run([
                sys.executable, "-m", "uv", "sync"
            ], check=True, cwd=Path(__file__).parent)
        else:
            subprocess.run([
                sys.executable, "-m", "uv", "sync", "--extra", dep_group
            ], check=True, cwd=Path(__file__).parent)
        print(f"✅ {dep_group.title()} dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {dep_group} dependencies: {e}")
        return False

def start_production_backend(host='0.0.0.0', port=8000, workers=4):
    """Start the backend with gunicorn for production"""
    print(f"🚀 Starting production backend server on {host}:{port}")
    print(f"   Workers: {workers}")

    cmd = [
        sys.executable, "-m", "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
        "--worker-class", "gevent",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "backend.app:app"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Production server stopped")

def start_production_frontend(host='0.0.0.0', port=3000):
    """Start the frontend with production settings"""
    print(f"🌐 Starting production frontend server on {host}:{port}")

    # Set production environment variables
    env = os.environ.copy()
    env['ENV'] = 'production'

    cmd = [sys.executable, "server_api.py"]
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production frontend: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Production frontend stopped")

def main():
    parser = argparse.ArgumentParser(description='Production deployment for Pcloudy Test Case Agent')
    parser.add_argument('--backend-only', action='store_true',
                       help='Start only the backend server')
    parser.add_argument('--frontend-only', action='store_true',
                       help='Start only the frontend server')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--backend-port', type=int, default=8000,
                       help='Backend port (default: 8000)')
    parser.add_argument('--frontend-port', type=int, default=3000,
                       help='Frontend port (default: 3000)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of gunicorn workers (default: 4)')
    parser.add_argument('--install-deps', choices=['production', 'development', 'testing'],
                       help='Install specific dependency group (production/development/testing)')
    parser.add_argument('--install-all', action='store_true',
                       help='Install all dependency groups')

    args = parser.parse_args()

    print("🏭 Pcloudy Test Case Agent - Production Deployment")
    print("=" * 50)

    # Check environment
    if not check_environment():
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            sys.exit(1)

    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies(args.install_deps):
            sys.exit(1)
    elif args.install_all:
        if not install_dependencies('all'):
            sys.exit(1)

    # Start services
    if args.backend_only:
        start_production_backend(args.host, args.backend_port, args.workers)
    elif args.frontend_only:
        start_production_frontend(args.host, args.frontend_port)
    else:
        print("🚀 Starting both backend and frontend in production mode...")
        print("💡 For production, consider running backend and frontend separately")
        print("   Backend: python deploy.py --backend-only")
        print("   Frontend: python deploy.py --frontend-only")
        print()

        # Start backend in background
        backend_cmd = [
            sys.executable, "-m", "gunicorn",
            "--bind", f"{args.host}:{args.backend_port}",
            "--workers", str(args.workers),
            "--worker-class", "gevent",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "backend.app:app"
        ]

        backend_process = subprocess.Popen(backend_cmd)
        print(f"✅ Backend started on {args.host}:{args.backend_port}")

        # Start frontend
        start_production_frontend(args.host, args.frontend_port)

if __name__ == "__main__":
    main()