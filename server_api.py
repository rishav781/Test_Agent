#!/usr/bin/env python3
"""
Server API - Static Web Server
Serves the frontend static files with API configuration injection
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Get the directory relative to this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.frontend_dir = os.path.join(script_dir, 'frontend')
        super().__init__(*args, directory=self.frontend_dir, **kwargs)

    def end_headers(self):
        # Add CORS headers to allow API calls to backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        # For index.html, inject the backend URL
        if self.path == '/' or self.path == '/index.html':
            try:
                # Get backend URL from environment
                backend_url = os.getenv('BACKEND_URL')
                if not backend_url:
                    self.send_error(500, "Error: BACKEND_URL environment variable not set.")
                    return

                # Path to the original index.html
                index_path = os.path.join(self.frontend_dir, 'index.html')
                
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Inject the backend URL into a script tag in the head
                injection_script = f"<script>window.BACKEND_URL = '{backend_url}';</script>"
                content = content.replace('</head>', f'{injection_script}</head>')
                
                # Serve the modified content
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "Error: index.html not found.")
            except Exception as e:
                self.send_error(500, f"Error processing index.html: {e}")
        else:
            # For all other files, use the default handler
            super().do_GET()

def run_frontend_server(port):
    """Run the frontend HTTP server"""
    try:
        with socketserver.TCPServer(('', port), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 Frontend server running at http://localhost:{port}")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            frontend_dir = os.path.join(script_dir, 'frontend')
            print(f"📁 Serving files from: {os.path.abspath(frontend_dir)}")
            backend_url = os.getenv('BACKEND_URL')
            print(f"🔗 Backend API configured to: {backend_url}")
            print("Press Ctrl+C to stop...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Please try a different port.")
        else:
            print(f"❌ Error starting server: {e}")

def main():
    """Main entry point for the frontend server"""
    # Get environment settings
    env = os.getenv('ENV', 'development')
    is_production = env == 'production'

    port_str = os.getenv('FRONTEND_PORT')
    if not port_str:
        print("❌ Error: FRONTEND_PORT is not set in the .env file.", file=sys.stderr)
        sys.exit(1)

    try:
        port = int(port_str)
    except ValueError:
        print(f"❌ Error: Invalid FRONTEND_PORT '{port_str}'. Must be a number.", file=sys.stderr)
        sys.exit(1)

    if is_production:
        print("🏭 Starting PRODUCTION frontend server...")
    else:
        print("🛠️  Starting DEVELOPMENT frontend server...")

    run_frontend_server(port)

if __name__ == "__main__":
    main()