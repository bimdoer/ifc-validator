#!/usr/bin/env python3
"""
Einfacher HTTP-Server zum Starten des IFC Viewers.
Öffne http://localhost:8000/viewer.html im Browser.
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Setze CORS-Header für WASM-Dateien und Workers
        # WICHTIG: require-corp kann zu restriktiv sein - verwende unsafely-none für lokale Entwicklung
        self.send_header('Cross-Origin-Embedder-Policy', 'unsafe-none')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        
        # WICHTIG: Setze MIME-Types für verschiedene Dateitypen
        if self.path.endswith('.wasm'):
            self.send_header('Content-Type', 'application/wasm')
        elif self.path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript')
        elif self.path.endswith('.html'):
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        elif self.path.endswith('.mjs'):
            self.send_header('Content-Type', 'application/javascript')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Reduziere Logging für bessere Lesbarkeit
        if 'favicon.ico' not in args[0]:
            super().log_message(format, *args)

def main():
    # Wechsle ins Projektverzeichnis
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/viewer.html"
        print(f"Server läuft auf http://localhost:{PORT}")
        print(f"Öffne {url} im Browser...")
        print("Drücke Ctrl+C zum Beenden")
        
        # Öffne Browser automatisch
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer wird beendet...")

if __name__ == "__main__":
    main()
