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
    from app import app, OPENAI_MODEL_TEXT, OPENAI_MODEL_VISION, OPENAI_MODEL_WEBSITE, OPENAI_MODEL_API
    from website_analyzer import analyze_website, OPENAI_MODEL_WEBSITE as WEBSITE_MODEL
    from api_test_generator import generate_api_tests_from_file, OPENAI_MODEL_API as API_MODEL
    print("✅ All backend modules imported successfully")
    print(f"📋 Configured Models:")
    print(f"   Text Analysis: {OPENAI_MODEL_TEXT}")
    print(f"   Vision Analysis: {OPENAI_MODEL_VISION}")
    print(f"   Website Analysis: {OPENAI_MODEL_WEBSITE}")
    print(f"   API Analysis: {API_MODEL}")
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    sys.exit(1)

def main():
    """Main function to run the Flask application"""
    # Get configuration from environment
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print("🚀 Starting Pcloudy Test Case Agent Server...")
    print(f"🌐 Host: {host}:{port}")
    print(f"🔧 Debug mode: {'ENABLED' if debug else 'DISABLED'}")
    print("📁 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /analyze - Text/Image analysis")
    print("   POST /generate_api_tests - API document analysis")
    print("   POST /analyze_website - Website analysis")
    print("Press Ctrl+C to stop the server")

    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()