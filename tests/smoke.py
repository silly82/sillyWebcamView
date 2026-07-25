"""Smoke-test: spin up local server, fetch index.html, validate structure."""
import http.server, socketserver, threading, urllib.request, sys, time
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=str(WEB), **kw)

def run():
    with socketserver.TCPServer(("", 0), Handler) as srv:
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        time.sleep(0.3)
        url = f"http://127.0.0.1:{port}/index.html"
        body = urllib.request.urlopen(url).read().decode()
        assert "alpinejs" in body.lower(), "Alpine script missing"
        assert "tailwindcss" in body.lower(), "Tailwind script missing"
        assert "/js/player.js" in body, "player.js reference missing"
        print(f"✓ {url} — all required assets referenced")

if __name__ == "__main__":
    run()
