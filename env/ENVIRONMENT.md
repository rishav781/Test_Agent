# Environment Configuration Guide

## Overview

This application supports multiple environments (development, production) with separate configuration files and robust environment variable management.

## Environment Files

### `.env.development`
- Development configuration
- Debug mode enabled
- Local URLs and ports
- Relaxed CORS settings

### `.env.production`
- Production configuration
- Debug mode disabled
- Production URLs and SSL
- Strict CORS settings
- Gunicorn configuration

### `.env`
- Active configuration file (copied from environment-specific files)
- **Never commit this file** (it's in .gitignore)

## Environment Management

### Switching Environments

Use the environment switcher script:

```bash
# Switch to development
python switch_env.py development

# Switch to production
python switch_env.py production

# Check current environment
python switch_env.py current

# List available environments
python switch_env.py list
```

### Manual Environment Setup

```bash
# For development
cp .env.development .env

# For production
cp .env.production .env
# Then edit .env with your production values
```

## Configuration System

The application uses a centralized configuration system (`backend/src/config.py`) that:

- ✅ Automatically detects project root from any directory
- ✅ Loads environment variables from multiple possible locations
- ✅ Provides environment-specific CORS settings
- ✅ Validates critical configuration on startup
- ✅ Handles both development and production seamlessly

## Running the Application

### Development
```bash
# Switch to development environment
python switch_env.py development

# Start all services
python start.py
```

### Production
```bash
# Switch to production environment
python switch_env.py production

# Edit .env with your production values
nano .env

# Start with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 --worker-class gevent backend.src.app:app
```

## Key Configuration Differences

| Setting | Development | Production |
|---------|-------------|------------|
| `ENV` | `development` | `production` |
| `FLASK_DEBUG` | `True` | `False` |
| `CORS_ORIGINS` | Multiple dev URLs | Restricted production URLs |
| `FRONTEND_URL` | `http://localhost:8080` | `https://yourdomain.com` |
| `SECRET_KEY` | Dev key | Secure random key |

## Troubleshooting

### Common Issues

1. **Environment not loading**
   ```bash
   python switch_env.py current  # Check current config
   python switch_env.py development  # Reset to development
   ```

2. **CORS errors in production**
   - Check `ALLOWED_ORIGINS` in `.env.production`
   - Ensure `FRONTEND_URL` matches your frontend domain

3. **Port conflicts**
   - Development: 8080 (frontend), 5050 (backend)
   - Production: 443 (frontend), 8000 (backend)

4. **Path issues**
   - The config system automatically finds project root
   - Run from any directory within the project

### Configuration Validation

The application validates critical settings on startup:
- OpenAI API key presence
- Required ports
- Frontend URL in production

Check the startup logs for any validation errors.

## Security Notes

- Never commit `.env` files
- Use strong `SECRET_KEY` in production
- Restrict `ALLOWED_ORIGINS` in production
- Set `OPENAI_API_KEY` via environment variables in production
- Use HTTPS in production (port 443)