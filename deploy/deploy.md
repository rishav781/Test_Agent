# Enhanced Deployment Guide

This folder contains the enhanced **production deployment** script for Linux servers. For development and testing on any platform, use `python start.py` instead.

**When to use this script:**

- ✅ Production deployment on Linux servers
- ✅ Need for gunicorn WSGI server with multiple workers
- ✅ Automated virtual environment and dependency setup
- ✅ Proper production server configuration

**When to use `start.py`:**

- ✅ Development and testing on any platform (Windows/Mac/Linux)
- ✅ Quick environment switching and server startup
- ✅ Flask development server for debugging

## Files

- `deploy.py` - Enhanced production deployment script with automatic virtual environment setup
- `deploy.md` - This deployment documentation

## Key Features

🚀 **Universal Compatibility**: Works on any system with Python 3.12+ without requiring UV or external tools  
🔧 **Automatic Setup**: Creates virtual environment and installs dependencies automatically  
🎯 **Interactive Configuration**: User-friendly port selection and configuration  
🛡️ **Robust Fallbacks**: Multiple dependency installation strategies ensure success  
📦 **Self-Contained**: Single script handles entire deployment lifecycle

## Quick Start

### Simple Deployment (Recommended)

Just run the deployment script - it handles everything automatically:

```bash
python deploy/deploy.py
```

The script will:

1. ✅ Check Python 3.12+ compatibility
2. 🔧 Create virtual environment (`.venv`)
3. 📦 Install all dependencies with pip
4. 🎯 Prompt for frontend and backend ports
5. 🚀 Start both servers in production mode

### Advanced Deployment Options

```bash
# Setup environment only (no server start)
python deploy/deploy.py --setup-only

# Skip setup, just start servers (if already setup)
python deploy/deploy.py --skip-setup

# Start backend only
python deploy/deploy.py --backend-only

# Start frontend only
python deploy/deploy.py --frontend-only

# Custom host and worker configuration
python deploy/deploy.py --host 192.168.1.100 --workers 8

# Help and all options
python deploy/deploy.py --help
```

### Deployment Workflow

The enhanced deployment script follows this workflow:

1. **Environment Validation** 🔍

   - Checks Python 3.12+ compatibility
   - Validates system requirements

2. **Virtual Environment Setup** 🏗️

   - Creates `.venv` directory if not exists
   - Uses Python's built-in `venv` module

3. **Dependency Installation** 📦

   - Primary: Installs from `pyproject.toml` (editable mode)
   - Fallback: Direct pip installation of core dependencies
   - Last resort: Installs core dependencies directly

4. **Server Configuration** ⚙️

   - Interactive port selection for frontend/backend
   - Environment variable configuration
   - Production settings validation

5. **Service Startup** 🚀
   - Starts gunicorn backend with gevent workers
   - Starts production frontend server
   - Graceful shutdown handling

## Production Checklist

- [ ] Set `ENV=production` in `.env`
- [ ] Disable debug mode (`FLASK_DEBUG=false`)
- [ ] Use strong secret keys
- [ ] Configure SSL certificates
- [ ] Set up reverse proxy (nginx recommended)
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Use process manager (systemd/supervisor)

## Architecture

### Backend (Gunicorn + Gevent)

- **WSGI Server**: Gunicorn for production-ready WSGI serving
- **Workers**: Gevent for async processing
- **Configuration**: Multiple workers for scalability
- **Logging**: Access and error logs to stdout

### Frontend (Production HTTP Server)

- **Server**: Python HTTP server optimized for production
- **Environment**: Production settings applied
- **Static Files**: Efficient serving of frontend assets

## Environment Variables

### Required for Production

```env
ENV=production
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-production-secret-key
```

### Optional Configuration

```env
# Server binding (deployment script will prompt for ports interactively)
BACKEND_HOST=0.0.0.0
FRONTEND_HOST=0.0.0.0

# These ports can be overridden by interactive deployment
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Gunicorn worker configuration
WORKERS=4
```

## No External Dependencies Required

The enhanced deployment script uses only Python built-in modules and pip:

- ✅ **Python 3.12+**: Only requires standard Python installation
- ✅ **Built-in venv**: Uses Python's native virtual environment
- ✅ **Standard pip**: No UV, poetry, or other tools required
- ✅ **Cross-platform**: Works on Windows, Linux, and macOS
- ✅ **Automatic fallbacks**: Multiple dependency installation strategies

## Nginx Configuration

Example reverse proxy configuration:

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Common Issues

1. **Python Version Compatibility**

   - Ensure Python 3.12+ is installed: `python --version`
   - The script will automatically check and warn about version issues

2. **Port Already in Use**

   - The deployment script will prompt for different ports interactively
   - Check for existing services: `netstat -ano | findstr :8080` (Windows) or `lsof -i :8080` (Linux/Mac)

3. **Virtual Environment Issues**

   - Delete `.venv` folder and run `python deploy/deploy.py` again
   - Ensure sufficient disk space for virtual environment creation

4. **Dependency Installation Failures**

   - The script has multiple fallback strategies for dependency installation
   - Check internet connectivity for package downloads
   - Manually install dependencies:
     - With UV: `uv sync --group production`
     - With pip: `pip install -e .`

5. **Permission Denied**

   - Ensure proper file permissions in project directory
   - Ports < 1024 may require administrator/root access
   - Use ports > 1024 for non-privileged deployment

6. **Environment Configuration**
   - Copy `.env.template` to `.env` and configure
   - Set `ENV=production` for production deployment
   - Ensure OpenAI API key is configured

### Debug Steps

1. **Run Setup Only**: `python deploy/deploy.py --setup-only`
2. **Check Virtual Environment**: Verify `.venv` directory exists
3. **Test Manual Start**: Activate venv and test individual components
4. **Check Logs**: Review console output for specific error messages

## Performance Tuning

### Worker Configuration

- **CPU-bound**: Use sync workers (default)
- **I/O-bound**: Use gevent workers (current setup)
- **Memory usage**: Adjust worker count based on RAM

### Scaling Recommendations

- **Small app**: 2-4 workers
- **Medium app**: 4-8 workers
- **Large app**: 8-16 workers

### Monitoring

- Use access/error logs for debugging
- Monitor memory and CPU usage
- Set up health checks on `/health` endpoint
