from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs

from upstash_redis import Redis

ALLOWED_KEYS = {"finance", "opmodel", "opmodel-reviews"}


def get_redis():
    return Redis(
        url=os.environ["KV_REST_API_URL"],
        token=os.environ["KV_REST_API_TOKEN"],
    )


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        api_key = self.headers.get("X-API-Key", "")
        if api_key != os.environ.get("DASHBOARD_API_KEY", ""):
            self._send_json(401, {"error": "unauthorized"})
            return

        qs = parse_qs(urlparse(self.path).query)
        key = qs.get("key", [None])[0]
        if not key or key not in ALLOWED_KEYS:
            self._send_json(400, {"error": "invalid key"})
            return

        try:
            r = get_redis()
            val = r.get(key)
            if val is None:
                self._send_json(404, {"error": "not found"})
                return
            data = json.loads(val) if isinstance(val, str) else val
            self._send_json(200, data)
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
