"""Local dashboard for Timely. Run with: python dashboard.py

Serves dashboard.html on your own computer only (127.0.0.1) and reads the
same tracker_data.json that voice_agent.py writes. Uses only the standard
library, so no installs are needed.
"""

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
DATA_FILE = HERE / "tracker_data.json"
PAGE = HERE / "dashboard.html"
HOST, PORT = "127.0.0.1", 8765
ALLOWED_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}


def load() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass  # file was mid-write; show an empty view this time
    return {"reminders": [], "habits": [], "log": []}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/data":
            body = json.dumps(load()).encode("utf-8")
            self._send(200, body, "application/json")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin not in ALLOWED_ORIGINS:
            self._send(403, b"Forbidden", "text/plain")
            return
        if self.path != "/api/done":
            self._send(404, b"Not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            index = int(json.loads(self.rfile.read(length) or b"{}")["index"])
        except (ValueError, KeyError, json.JSONDecodeError):
            self._send(400, b"Bad request", "text/plain")
            return
        data = load()
        if 0 <= index < len(data["reminders"]):
            data["reminders"][index]["done"] = True
            DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._send(200, b'{"ok": true}', "application/json")
        else:
            self._send(404, b"No such reminder", "text/plain")

    def log_message(self, *args) -> None:
        pass  # keep the terminal quiet


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"Timely dashboard running at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
