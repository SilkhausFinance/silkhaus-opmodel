from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

ALLOWED_KEYS = {"finance", "opmodel", "opmodel-reviews"}
GIST_DESC = "silkhaus-dashboard-data"


def _gh_headers():
    return {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "silkhaus-opmodel",
        "Content-Type": "application/json",
    }


def _find_gist_id():
    req = urllib.request.Request("https://api.github.com/gists", headers=_gh_headers())
    with urllib.request.urlopen(req) as r:
        for g in json.loads(r.read()):
            if g.get("description") == GIST_DESC:
                return g["id"]
    return None


def _upsert(filename, content):
    gist_id = _find_gist_id()
    payload = json.dumps({
        "description": GIST_DESC,
        "public": False,
        "files": {filename: {"content": content}},
    }).encode()
    if gist_id is None:
        req = urllib.request.Request(
            "https://api.github.com/gists",
            data=payload, method="POST", headers=_gh_headers(),
        )
    else:
        req = urllib.request.Request(
            f"https://api.github.com/gists/{gist_id}",
            data=payload, method="PATCH", headers=_gh_headers(),
        )
    with urllib.request.urlopen(req) as r:
        json.loads(r.read())


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get("X-API-Key", "") != os.environ.get("DASHBOARD_API_KEY", ""):
            self._json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "invalid body"})
            return

        key = body.get("key")
        data = body.get("data")
        if not key or key not in ALLOWED_KEYS:
            self._json(400, {"error": "invalid key"})
            return

        try:
            _upsert(f"{key}.json", json.dumps(data))
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass
