import http.server
import socketserver
import os
import webbrowser
import argparse

# Configure server
PORT = 3001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server(open_driver=False):
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Rider interface: http://localhost:{PORT}/index.html")
        print(f"Driver interface: http://localhost:{PORT}/driver.html")
        
        # Open browser automatically
        if open_driver:
            webbrowser.open(f"http://localhost:{PORT}/driver.html")
            print("Opening driver interface in browser")
        else:
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            print("Opening rider interface in browser")
        
        # Keep the server running
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Mini-Uber client server")
    parser.add_argument("--driver", action="store_true", help="Open driver interface instead of rider interface")
    args = parser.parse_args()
    
    run_server(open_driver=args.driver)
