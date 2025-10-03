# Environment Files

This folder contains environment-specific configuration files for the Pcloudy Test Case Agent.

## Documentation

- `README.md` - This file (folder overview)
- `ENVIRONMENT.md` - Comprehensive environment configuration guide

## File Structure

- `.env.template` - Template file for setting up new environments
- `.env.development` - Development environment configuration
- `.env.production` - Production environment configuration
- `.env` - Active configuration file (auto-generated, do not edit directly)
- `.env.backup` - Backup of previous configuration (auto-generated)

## Usage

Use the interactive startup script which automatically handles environment selection:

```bash
# Interactive environment selection + start servers
python start.py
```

The script will:

- Show available environments (development/production)
- Ask you to select which environment to start
- Automatically configure the environment
- Start both frontend and backend servers

## Security

- Never commit actual `.env` files (they contain sensitive information)
- The entire `env/` folder is ignored by git except for this README
- Use strong secrets in production
- Set API keys via environment variables in production deployments

## Setup

1. Copy `.env.template` to create your environment file:

   ```bash
   cp .env.template .env.development  # For development
   cp .env.template .env.production   # For production
   ```

2. Edit the copied file with your specific values
3. Start the application with `python start.py` and select your environment
