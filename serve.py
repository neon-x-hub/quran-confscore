#!/usr/bin/env python3
"""
Simple HTTP Server for Quran Confusability Web Interface
"""

import http.server
import socketserver
import webbrowser
import sys

PORT = 8000

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    Handler = CORSRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[*] Serving Quran Confusability Web Interface on http://localhost:{PORT}")
        print("[*] Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")

if __name__ == "__main__":
    main()
