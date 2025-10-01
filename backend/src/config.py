"""
Configuration management for Pcloudy Test Case Agent
Handles environment variables, paths, and settings for both development and production
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration class that handles environment-specific settings"""

    def __init__(self):
        # Get the project root directory (works from any subdirectory)
        self.project_root = self._get_project_root()

        # Load environment variables first
        self._load_environment()

        # Set environment - use the loaded environment variable
        self.env = os.getenv('ENV', 'development').lower()
        self.is_production = self.env == 'production'
        self.is_development = not self.is_production

        # Load configuration values
        self._load_config()

    def _get_project_root(self):
        """Get the project root directory reliably"""
        # Try to find the project root by looking for pyproject.toml or .env
        current_path = Path(__file__).resolve()

        # Go up until we find a marker file
        for parent in [current_path] + list(current_path.parents):
            if (parent / 'pyproject.toml').exists() or (parent / '.env').exists():
                return parent

        # Fallback: assume we're in backend/src and go up two levels
        return Path(__file__).parent.parent.parent

    def _load_environment(self):
        """Load environment variables from appropriate .env file"""
        # Get environment from system (before loading .env files)
        current_env = os.getenv('ENV', 'development').lower()

        # Try multiple possible .env file locations (including env folder)
        possible_env_files = [
            self.project_root / 'env' / '.env',
            self.project_root / 'env' / f'.env.{current_env}',
            self.project_root / '.env',
            self.project_root / f'.env.{current_env}',
            Path('.env'),
            Path('..') / '.env',
        ]

        env_loaded = False
        for env_file in possible_env_files:
            if env_file.exists():
                load_dotenv(env_file)
                print(f"✅ Loaded environment from: {env_file}")
                env_loaded = True
                break

        if not env_loaded:
            print("⚠️  No .env file found, using system environment variables")

    def _load_config(self):
        """Load all configuration values"""

        # Server Configuration
        self.backend_host = os.getenv('BACKEND_HOST', '0.0.0.0')
        self.backend_port = int(os.getenv('BACKEND_PORT', '5050'))
        self.frontend_port = int(os.getenv('FRONTEND_PORT', '8080'))

        # URLs
        self.backend_url = os.getenv('BACKEND_URL', f'http://{self.backend_host}:{self.backend_port}')
        self.frontend_url = os.getenv('FRONTEND_URL', f'http://localhost:{self.frontend_port}')

        # CORS Origins - Support multiple environments
        cors_origins = []
        if self.is_development:
            cors_origins.extend([
                f'http://localhost:{self.frontend_port}',
                f'http://127.0.0.1:{self.frontend_port}',
                f'http://0.0.0.0:{self.frontend_port}',
                'http://localhost:3000',  # Common dev port
                'http://localhost:8080',  # Common dev port
            ])
        else:
            # Production CORS - more restrictive
            cors_origins.extend([
                os.getenv('FRONTEND_URL', '').rstrip('/'),
                os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else []
            ])
            # Remove empty strings
            cors_origins = [origin for origin in cors_origins if origin]

        self.cors_origins = cors_origins or ['*']  # Fallback to allow all in dev

        # Flask Configuration
        self.flask_debug = os.getenv('FLASK_DEBUG', 'True' if self.is_development else 'False').lower() == 'true'
        self.flask_env = os.getenv('FLASK_ENV', 'development' if self.is_development else 'production')

        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model_text = os.getenv('OPENAI_MODEL_TEXT', 'gpt-4')
        self.openai_model_vision = os.getenv('OPENAI_MODEL_VISION', 'gpt-4o')
        self.openai_model_website = os.getenv('OPENAI_MODEL_WEBSITE', 'gpt-4')
        self.openai_model_api = os.getenv('OPENAI_MODEL_API', 'gpt-4')

        # File Upload Configuration
        self.max_content_length = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
        self.allowed_extensions = set(
            os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,bmp,webp').split(',')
        )

        # Security
        self.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Paths
        self.project_root = str(self.project_root)
        self.backend_dir = os.path.join(self.project_root, 'backend')
        self.frontend_dir = os.path.join(self.project_root, 'frontend')
        self.logs_dir = os.path.join(self.project_root, 'logs')

        # Ensure directories exist
        os.makedirs(self.logs_dir, exist_ok=True)

    def get_cors_origins(self):
        """Get CORS origins based on environment"""
        return self.cors_origins

    def get_flask_config(self):
        """Get Flask-specific configuration"""
        return {
            'DEBUG': self.flask_debug,
            'ENV': self.flask_env,
            'SECRET_KEY': self.secret_key,
            'MAX_CONTENT_LENGTH': self.max_content_length,
        }

    def validate(self):
        """Validate critical configuration"""
        errors = []

        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")

        if not self.frontend_port:
            errors.append("FRONTEND_PORT is required")

        if self.is_production and not os.getenv('FRONTEND_URL'):
            errors.append("FRONTEND_URL is required in production")

        return errors


# Global config instance
config = Config()

# Validate configuration on import
validation_errors = config.validate()
if validation_errors:
    print("❌ Configuration validation errors:")
    for error in validation_errors:
        print(f"   - {error}")
    if config.is_production:
        print("🚨 Critical configuration errors in production!")
        sys.exit(1)
else:
    print("✅ Configuration loaded successfully")
    print(f"   Environment: {config.env}")
    print(f"   Backend: {config.backend_url}")
    print(f"   Frontend: {config.frontend_url}")
    print(f"   CORS Origins: {len(config.cors_origins)} configured")