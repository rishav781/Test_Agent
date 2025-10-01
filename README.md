# Pcloudy Test Case Agent

An intelligent AI-powered test case generation platform that creates comprehensive test scenarios and cases from multiple input sources including text descriptions, images, API documentation, and website analysis.

## Features

- 🤖 **AI-Powered Test Generation**: Generate detailed test scenarios and cases using OpenAI's GPT models
- 📝 **Multi-Input Support**: Create tests from text descriptions, UI screenshots, API documents, and website URLs
- � **Modern Web Interface**: Clean, intuitive frontend with tabbed interface and step-by-step workflow
- 🔧 **RESTful API**: Comprehensive backend API with multiple endpoints for different test generation needs
- 📊 **Comprehensive Analysis**: Website performance analysis, API endpoint extraction, and document parsing
- 🏭 **Production Ready**: Deployment scripts with gunicorn support and proper configuration management
- � **Multi-Format Support**: Handles Swagger/OpenAPI specs, Postman collections, and various image formats

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager (`pip install uv`)
- OpenAI API key

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd Test_Agent
   ```

2. Install dependencies:

   ```bash
   # Install all dependencies (production + development + testing)
   uv sync

   # Or install specific groups
   uv sync --group development    # Development tools + core dependencies
   uv sync --group production     # Production server + core dependencies
   uv sync --group testing        # Testing tools + core dependencies

   # Install only specific groups (without core dependencies)
   uv sync --only-group development
   uv sync --only-group production
   uv sync --only-group testing
   ```

3. Copy and configure environment:

   ```bash
   cp .env.template .env
   ```

   Edit `.env` file and set your OpenAI API key:

   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   ```

4. Start the application:

   ```bash
   python start.py
   ```

   The script will:
   - Show available environments (development/production)
   - Ask you to select which environment to start
   - Automatically configure the environment
   - Start both frontend and backend servers

   **Note:** `start.py` uses Flask's development server suitable for development and testing. For production deployment on Linux servers, use the deployment script:

   ```bash
   python deploy/deploy.py
   ```

   The deployment script uses gunicorn with multiple workers for production workloads.

   **Available Environments:**
   - `development`: Debug mode enabled, local development servers
   - `production`: Optimized for production deployment

The application will be available at (fully configurable in `.env`):

- Frontend: Your configured `FRONTEND_URL` (default: `http://localhost:8080`)
- Backend API: Your configured `BACKEND_URL` (default: `http://localhost:5050`)

## Core Functionality

### Test Generation Modes

1. **Text Description**: Generate test scenarios from natural language descriptions of features
2. **Image Analysis**: Upload screenshots, wireframes, or UI mockups for AI-powered test case generation
3. **API Documentation**: Parse Swagger/OpenAPI specs or Postman collections to create API test cases
4. **Website Analysis**: Analyze live websites for performance testing and UI test case generation

### AI Models Used

- **GPT-4**: Primary model for text analysis and test case generation
- **GPT-4V (Vision)**: Specialized model for image analysis and visual test case generation
- **Configurable Models**: All models can be customized via environment variables

## Environment Configuration

### Development Setup

Create a `.env` file from the template:

```env
# Application Environment
ENV=development

# Server Configuration (fully customizable URLs and ports)
FRONTEND_URL=http://localhost:8080  # Change to your preferred URL/domain
BACKEND_URL=http://localhost:5050   # Change to your preferred URL/domain
FRONTEND_PORT=8080  # Change to any available port
BACKEND_PORT=5050   # Change to any available port

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL_TEXT=gpt-4
OPENAI_MODEL_VISION=gpt-4o
OPENAI_MODEL_WEBSITE=gpt-4
OPENAI_MODEL_API=gpt-4

# Flask Configuration
FLASK_DEBUG=True
FLASK_APP=backend/src/app.py
SECRET_KEY=your-secret-key-here
```

### Production Configuration

```env
# Application Environment
ENV=production

# Server Configuration (use your custom domains/IPs)
FRONTEND_URL=https://yourdomain.com  # Any URL/domain you want
BACKEND_URL=https://api.yourdomain.com  # Any URL/domain you want
FRONTEND_PORT=80  # Any port
BACKEND_PORT=8000  # Any port

# OpenAI Configuration
OPENAI_API_KEY=your-production-openai-key

# Flask Configuration
FLASK_DEBUG=False
SECRET_KEY=your-strong-production-secret-key

# File Upload Limits
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,bmp,webp
```

## Deployment

### Enhanced Universal Deployment (Recommended)

The enhanced deployment script provides universal compatibility and works on any system with Python 3.12+ without requiring UV or external tools.

**🚀 One-Command Deployment:**

```bash
python deploy/deploy.py
```

**What it does automatically:**

- ✅ Creates virtual environment (`.venv`)
- ✅ Installs all dependencies with pip
- ✅ Prompts for frontend/backend ports
- ✅ Starts both servers in production mode
- ✅ Handles graceful shutdown

**Advanced Options:**

```bash
# Setup environment only
python deploy/deploy.py --setup-only

# Skip setup, just start servers
python deploy/deploy.py --skip-setup

# Start individual services
python deploy/deploy.py --backend-only
python deploy/deploy.py --frontend-only

# Custom configuration
python deploy/deploy.py --host 0.0.0.0 --workers 8
```

### Traditional UV Deployment (Alternative)

If you have UV installed and prefer the traditional approach:

1. **Install production dependencies:**

   ```bash
   uv sync --extra production
   ```

2. **Set production environment:**

   Ensure your `.env` file has `ENV=production`.

3. **Manual server startup:**

   ````bash
   # Backend with gunicorn
   gunicorn --bind 0.0.0.0:8000 --workers 4 backend.src.app:app

   # Frontend (separate terminal)
   python server_api.py
   ```### Manual Production Setup
   ````

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
        proxy_s        proxy_pass http://127.0.0.1:8080;
warded_for;
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

- `GET /health` - Health check endpoint
- `POST /analyze` - Analyze input (text/image) and generate test scenarios
- `POST /generate` - Generate detailed test cases from scenarios or direct input
- `POST /analyze_website` - Analyze website and generate test cases
- `POST /generate_api_tests` - Generate test cases from API documentation (Swagger/Postman)

### Request Examples

#### Generate Test Scenarios from Description

```bash
curl -X POST http://localhost:5050/analyze \
  -F "description=User login functionality with email validation"
```

#### Generate Test Cases from Image

```bash
curl -X POST http://localhost:5050/generate \
  -F "image=@screenshot.png"
```

#### Analyze Website

```bash
curl -X POST http://localhost:5050/analyze_website \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

#### Generate API Tests

```bash
curl -X POST http://localhost:5050/generate_api_tests \
  -F "api_file=@swagger.json"
```

### Authentication

No authentication required for development. Configure API keys through environment variables for production use.

## Development Workflow

### Local Development

1. Install development dependencies:

   ```bash
   uv sync --extra development
   ```

2. Start development servers:

   ```bash
   python start.py
   ```

3. Run code quality checks:

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

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**

   - Ensure `OPENAI_API_KEY` is set in your `.env` file
   - Verify your OpenAI account has available credits

2. **Port Already in Use**

   - **Enhanced Deployment**: The script will prompt for alternative ports automatically
   - **Manual Fix**: Change `FRONTEND_PORT` and `BACKEND_PORT` in `.env` file
   - **Kill Processes**: `netstat -ano | findstr :8080` (Windows) or `lsof -i :8080` (Linux/Mac)

3. **Dependency Installation Issues**

   - **Enhanced Deployment**: Script has multiple fallback strategies
   - **UV Issues**: Use enhanced deployment instead: `python deploy/deploy.py`
   - **Manual Install**: `pip install Flask openai Pillow python-dotenv requests gunicorn`

4. **Python Version Compatibility**

   - Requires Python 3.12+
   - Enhanced deployment script will check and warn about version issues

5. **Virtual Environment Issues**

   - Delete `.venv` folder and run `python deploy/deploy.py` again
   - Ensure sufficient disk space for environment creation

6. **File Upload Issues**

   - Check file size limits in `MAX_CONTENT_LENGTH`
   - Verify file extension is in `ALLOWED_EXTENSIONS`

### Enhanced Deployment Benefits

The new `deploy.py` script solves common deployment issues:

- ✅ **No UV Required**: Works with standard Python + pip
- ✅ **Automatic Environment**: Creates isolated virtual environment
- ✅ **Smart Port Selection**: Interactive port configuration
- ✅ **Robust Installation**: Multiple dependency installation strategies
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS

### Logging

Application logs are stored in the `logs/` directory. Check these files for detailed error information.

## Project Structure

```text
Test_Agent/
├── backend/                    # Flask API backend
│   ├── src/                   # Source code
│   │   ├── app.py            # Main Flask application with all endpoints
│   │   ├── api_test_generator.py  # API document test generation logic
│   │   ├── website_analyzer.py    # Website analysis and performance testing
│   │   └── server.py         # Additional server utilities
├── frontend/                 # Static frontend files
│   ├── index.html           # Main web interface
│   ├── css/                 # Stylesheets
│   │   └── global.css       # Main styling
│   ├── js/                  # JavaScript files
│   │   └── script.js        # Frontend logic
│   └── assets/              # Static assets
│       └── images/          # Images and icons
├── deploy/                  # Production deployment
│   ├── deploy.py           # Interactive deployment script
│   └── deploy.md           # Deployment documentation
├── logs/                   # Application logs directory
├── pyproject.toml         # Python project configuration with dependencies
├── uv.lock               # UV lock file for reproducible builds
├── start.py              # Interactive startup script (environment selection + starts both servers)
├── server_api.py         # Frontend HTTP server with API injection
├── .env.template         # Environment variables template
└── README.md            # Project documentation
```

## Technology Stack

- **Backend**: Flask, OpenAI API, Pillow (image processing), Requests
- **Frontend**: Vanilla HTML/CSS/JavaScript with modern UI design
- **AI Models**: GPT-4 for text analysis, GPT-4V for image analysis
- **Development**: UV package manager, Black/Ruff for code quality
- **Deployment**: Gunicorn WSGI server, custom deployment scripts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run code quality checks (`black .`, `ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:

- Create an issue on GitHub
- Check the troubleshooting section above
- Review the deployment documentation in `deploy/deploy.md`
