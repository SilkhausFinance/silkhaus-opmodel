from http.server import BaseHTTPRequestHandler
import json
import os

from upstash_redis import Redis

ALLOWED_KEYS = {"finance", "opmodel", "opmodel-reviews"}


def get_redis():
    return Redis(
        url=os.environ["KV_REST_API_URL"],
        token=os.environ["KV_REST_API_TOKEN"],
    )


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        api_key = self.headers.get("X-API-Key", "")
        if api_key != os.environ.get("DASHBOARD_API_KEY", ""):
            self._send_json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json(400, {"error": "invalid body"})
            return

        key = body.get("key")
        data = body.get("data")
        if not key or key not in ALLOWED_KEYS:
            self._send_json(400, {"error": "invalid key"})
            return

        try:
            r = get_redis()
            r.set(key, json.dumps(data))
            self._send_json(200, {"ok": True})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
