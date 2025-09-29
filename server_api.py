#!/usr/bin/env python3
"""
Server API - Static Web Server
Serves the frontend static files with API configuration injection
"""

import http.server
import socketserver
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Get the directory relative to this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(script_dir, 'frontend')
        super().__init__(*args, directory=frontend_dir, **kwargs)

    def end_headers(self):
        # Add CORS headers to allow API calls to backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def end_headers(self):
        # Add CORS headers to allow API calls to backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_frontend_server(port=None):
    """Run the frontend HTTP server"""
    # Use environment variable if port not specified
    if port is None:
        port = int(os.getenv('FRONTEND_PORT', 8000))
    try:
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 Frontend server running at http://localhost:{port}")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            frontend_dir = os.path.join(script_dir, 'frontend')
            print(f"📁 Serving files from: {os.path.abspath(frontend_dir)}")
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
            print(f"🔗 Backend API: {backend_url}")
            print("Press Ctrl+C to stop...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python frontend_server.py --port 3001")
        else:
            print(f"❌ Error starting server: {e}")

def main():
    """Main entry point for the frontend server"""
    import sys

    # Get environment settings
    env = os.getenv('ENV', 'development')
    is_production = env == 'production'

    port = int(os.getenv('FRONTEND_PORT', 8000))

    if is_production:
        print("🏭 Starting PRODUCTION frontend server...")
        print("⚠️  Consider using nginx for static files in production")
    else:
        print("🛠️  Starting DEVELOPMENT frontend server...")

    if len(sys.argv) > 1 and sys.argv[1] == '--port' and len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)

    run_frontend_server(port)

if __name__ == "__main__":
    main()