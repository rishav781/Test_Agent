#!/usr/bin/env python3
"""
Pcloudy Test Case Agent - Server Runner
Main server file that imports all modules and starts the Flask application.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import all backend modules
try:
    from app import app
    from config import config
    from website_analyzer import analyze_website, OPENAI_MODEL_WEBSITE as WEBSITE_MODEL
    from api_test_generator import generate_api_tests_from_file, OPENAI_MODEL_API as API_MODEL
    print("✅ All backend modules imported successfully")
    print(f"📋 Configured Models:")
    print(f"   Text Analysis: {config.openai_model_text}")
    print(f"   Vision Analysis: {config.openai_model_vision}")
    print(f"   Website Analysis: {config.openai_model_website}")
    print(f"   API Analysis: {config.openai_model_api}")
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    sys.exit(1)

def main():
    """Main function to run the Flask application"""
    # Get configuration from config object
    host = config.backend_host
    port = config.backend_port
    debug = config.flask_debug

    print("🚀 Starting Pcloudy Test Case Agent Server...")
    print(f"🌐 Host: {host}:{port}")
    print(f"🔧 Debug mode: {'ENABLED' if debug else 'DISABLED'}")
    print(f"🌍 Environment: {config.env}")
    print("📁 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /analyze - Text/Image analysis")
    print("   POST /generate_api_tests - API document analysis")
    print("   POST /analyze_website - Website analysis")
    print("Press Ctrl+C to stop the server")

    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()