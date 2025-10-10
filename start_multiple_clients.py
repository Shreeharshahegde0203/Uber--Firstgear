"""
Start Multiple Client Servers for Testing
Opens browser tabs for 2 drivers and 2 riders automatically
"""

import http.server
import socketserver
import threading
import webbrowser
import time
import os

# Configuration
CLIENT_DIR = os.path.join(os.path.dirname(__file__), 'client')
PORTS = {
    'driver1': 3001,
    'driver2': 3002,
    'rider1': 3003,
    'rider2': 3004
}

print("\n" + "="*70)
print("🚀 Starting Multiple Client Servers")
print("="*70)
print(f"📁 Serving files from: {CLIENT_DIR}")
print(f"🔌 Backend API: http://localhost:8000")
print("="*70)
print()

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CLIENT_DIR, **kwargs)
    
    def log_message(self, format, *args):
        # Suppress most logging
        if '200' in str(args):
            return
        print(f"[{self.address_string()}] {format % args}")

def start_server(port, name):
    """Start a simple HTTP server on the given port"""
    handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"✅ {name} server started on http://localhost:{port}")
        httpd.serve_forever()

def open_browsers():
    """Open browser tabs for all clients"""
    time.sleep(2)  # Wait for servers to start
    
    print("\n🌐 Opening browser tabs...")
    
    # Open driver tabs
    webbrowser.open(f'http://localhost:{PORTS["driver1"]}/driver.html')
    print(f"   ✅ Opened Driver 1: http://localhost:{PORTS['driver1']}/driver.html")
    time.sleep(0.5)
    
    webbrowser.open(f'http://localhost:{PORTS["driver2"]}/driver.html')
    print(f"   ✅ Opened Driver 2: http://localhost:{PORTS['driver2']}/driver.html")
    time.sleep(0.5)
    
    # Open rider tabs
    webbrowser.open(f'http://localhost:{PORTS["rider1"]}/index.html')
    print(f"   ✅ Opened Rider 1: http://localhost:{PORTS['rider1']}/index.html")
    time.sleep(0.5)
    
    webbrowser.open(f'http://localhost:{PORTS["rider2"]}/index.html')
    print(f"   ✅ Opened Rider 2: http://localhost:{PORTS['rider2']}/index.html")
    
    print("   ✅ All browser tabs opened!")

if __name__ == "__main__":
    # Start all servers in separate threads
    threads = []
    
    for name, port in PORTS.items():
        thread = threading.Thread(target=start_server, args=(port, name.capitalize()))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Open browsers
    browser_thread = threading.Thread(target=open_browsers)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\n" + "="*70)
    print("📝 TESTING GUIDE:")
    print("="*70)
    print("1. 🚗 Driver 1 & 2: Click 'Go Online' button in both tabs")
    print("2. 🧑 Rider 1 & 2: Login and request rides in both tabs")
    print("3. ⚡ Watch automatic driver matching happen in real-time!")
    print("4. 🔔 Drivers will receive push notifications for ride offers")
    print("5. ⏱️  Offers auto-expire after 20 seconds if not accepted")
    print("6. ✅ Accept → See persistent ride card → Start → Complete!")
    print()
    
    print("🌐 Active Client Servers:")
    for name, port in PORTS.items():
        print(f"   - {name.capitalize()}: http://localhost:{port}")
    
    print("\nPress CTRL+C to stop all servers")
    print("="*70)
    print()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all servers...")
        print("✅ Goodbye!")
