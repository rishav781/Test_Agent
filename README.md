# Pcloudy Testing Agent

An intelligent testing automation platform that combines AI-powered test generation with comprehensive testing tools.

## Features

- 🤖 AI-powered test case generation
- 🌐 Web-based interface for test management
- 🔧 RESTful API for integration
- 🏭 Production-ready deployment with gunicorn
- 📊 Real-time test execution and reporting

## Quick Start

### Prerequisites

- Python 3.8+
- uv package manager (`pip install uv`)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd Pcloudy-testing-agent
   ```

2. Install dependencies:

   ```bash
   # Install all dependencies (development + production + testing)
   uv sync

   # Or install specific groups
   uv sync --extra development  # Development tools only
   uv sync --extra production   # Production dependencies only
   uv sync --extra testing      # Testing dependencies only
   ```

3. Copy environment configuration:

   ```bash
   cp .env.template .env
   ```

4. Start the development servers:

   ```bash
   python start.py
   ```

The application will be available at:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5000`

## Environment Configuration

### Development

Create a `.env` file with:

```env
ENV=development
FLASK_ENV=development
FLASK_DEBUG=true

# Server URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:5000

# Flask Configuration
FLASK_APP=backend/app.py
SECRET_KEY=your-secret-key-here
```

### Production

For production deployment, update your `.env` file:

```env
ENV=production
FLASK_ENV=production
FLASK_DEBUG=false

# Server URLs (use your domain)
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com

# Flask Configuration
FLASK_APP=backend/app.py
SECRET_KEY=your-production-secret-key-here

# Production Database (if applicable)
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Production Deployment

### Option 1: Using the Deployment Script

1. Install production dependencies:

   ```bash
   uv sync --extra production
   ```

2. Set production environment:

   ```bash
   # Update .env file with ENV=production
   ```

3. Run the deployment script:

   ```bash
   # Start both services
   python deploy/deploy.py

   # Or start individually
   python deploy/deploy.py --backend-only  # Backend only
   python deploy/deploy.py --frontend-only  # Frontend only
   ```

### Option 2: Manual Production Setup

#### Backend (Gunicorn)

```bash
# Install production dependencies
uv sync --extra production

# Start with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 --worker-class gevent backend.app:app
```

#### Frontend (Production Server)

```bash
# Set production environment
export ENV=production

# Start the server
python server_api.py
```

### Production Checklist

- [ ] Set `ENV=production` in `.env`
- [ ] Disable debug mode (`FLASK_DEBUG=false`)
- [ ] Use strong secret keys
- [ ] Configure SSL certificates
- [ ] Set up reverse proxy (nginx recommended)
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Use process manager (systemd/supervisor)

### Nginx Configuration Example

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

## API Documentation

### Endpoints

- `GET /api/health` - Health check
- `POST /api/test/generate` - Generate AI-powered tests
- `GET /api/test/results` - Get test results

### Authentication

API endpoints require authentication. Include the API key in headers:

```http
Authorization: Bearer your-api-key
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend
```

### Local Development Workflow

1. Install development dependencies:

   ```bash
   uv sync --extra development
   ```

2. Run code quality checks:

   ```bash
   # Format code
   black .

   # Sort imports
   isort .

   # Lint and fix issues
   ruff check . --fix

   # Type checking
   mypy .
   ```

### Code Quality Tools

```bash
# Install development dependencies first
uv sync --extra development

# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Fast linting with ruff
ruff check .

# Type checking
mypy .
```

## Project Structure

```text
Pcloudy-testing-agent/
├── backend/           # Flask API server
│   ├── app.py        # Main Flask application
│   └── ...
├── frontend/          # Frontend static files
├── deploy/            # Deployment scripts and docs
│   ├── deploy.py     # Production deployment script
│   └── deploy.md     # Deployment documentation
├── pyproject.toml   # Python project configuration
├── start.py         # Development startup script
├── .env             # Environment variables
├── .env.template    # Environment variables template
├── README.md        # This file (main project README)
└── server_api.py    # Frontend server (legacy)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Documentation

📚 **Complete Documentation:**

- **[Deployment Guide](deploy/deploy.md)** - Production deployment with gunicorn

## License

MIT License - see LICENSE file for details

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Contact the development team
