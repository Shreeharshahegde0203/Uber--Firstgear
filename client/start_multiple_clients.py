"""
Start multiple client servers on different ports for testing
This allows you to test multiple riders and drivers simultaneously
"""
import http.server
import socketserver
import os
import webbrowser
import threading
import time

# Client directory
CLIENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Port configuration for different clients
PORTS_CONFIG = [
    {"port": 3001, "type": "driver", "name": "Driver 1"},
    {"port": 3002, "type": "driver", "name": "Driver 2"},
    {"port": 3003, "type": "rider", "name": "Rider 1"},
    {"port": 3004, "type": "rider", "name": "Rider 2"},
    {"port": 3005, "type": "rider", "name": "Rider 3"},
    {"port": 3006, "type": "rider", "name": "Rider 4"},
    {"port": 3007, "type": "rider", "name": "Rider 5"},
    {"port": 3008, "type": "rider", "name": "Rider 6"}
]
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CLIENT_DIR, **kwargs)
    
    def log_message(self, format, *args):
        # Simplified logging
        print(f"[{self.address_string()}] {format % args}")

def start_server(port, name):
    """Start HTTP server on specified port"""
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"✅ {name} server started on http://localhost:{port}")
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Error starting {name} on port {port}: {e}")

def open_browsers():
    """Open browser tabs after servers start"""
    time.sleep(2)  # Wait for servers to fully start
    
    print("\n🌐 Opening browser tabs...")
    
    for config in PORTS_CONFIG:
        port = config["port"]
        client_type = config["type"]
        name = config["name"]
        
        if client_type == "driver":
            url = f"http://localhost:{port}/driver.html"
        else:
            url = f"http://localhost:{port}/index.html"
        
        webbrowser.open(url)
        print(f"   ✅ Opened {name}: {url}")
        time.sleep(0.5)  # Small delay between opening tabs
    
    print("✅ All browser tabs opened!")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Starting Multiple Client Servers")
    print("=" * 70)
    print(f"📁 Serving files from: {CLIENT_DIR}")
    print(f"🔌 Backend API: http://localhost:8000")
    print("=" * 70)
    print()
    
    # Start servers in separate threads
    threads = []
    for config in PORTS_CONFIG:
        thread = threading.Thread(
            target=start_server, 
            args=(config["port"], config["name"]), 
            daemon=True
        )
        thread.start()
        threads.append(thread)
        time.sleep(0.2)  # Small delay between starting servers
    
    print()
    
    # Open browsers after servers start
    browser_thread = threading.Thread(target=open_browsers, daemon=True)
    browser_thread.start()
    
    # Show testing guide
    time.sleep(3)
    print()
    print("=" * 70)
    print("📝 TESTING GUIDE:")
    print("=" * 70)
    print("1. 🚗 Driver 1 & 2: Click 'Go Online' button in both tabs")
    print("2. 🧑 Rider 1 & 2: Login and request rides in both tabs")
    print("3. ⚡ Watch automatic driver matching happen in real-time!")
    print("4. 🔔 Drivers will receive push notifications for ride offers")
    print("5. ⏱️  Offers auto-expire after 15 seconds if not accepted")
    print()
    print("🌐 Active Client Servers:")
    for config in PORTS_CONFIG:
        print(f"   - {config['name']}: http://localhost:{config['port']}")
    print()
    print("Press CTRL+C to stop all servers")
    print("=" * 70)
    print()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all servers...")
        print("✅ Goodbye!")
