from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
from urllib.parse import urlparse, parse_qs

ALLOWED_KEYS = {"finance", "opmodel", "opmodel-reviews"}
GIST_DESC = "silkhaus-dashboard-data"


def _gh_headers():
    return {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "silkhaus-opmodel",
    }


def _find_gist_id():
    req = urllib.request.Request("https://api.github.com/gists", headers=_gh_headers())
    with urllib.request.urlopen(req) as r:
        for g in json.loads(r.read()):
            if g.get("description") == GIST_DESC:
                return g["id"]
    return None


def _read_file(gist_id, filename):
    req = urllib.request.Request(
        f"https://api.github.com/gists/{gist_id}",
        headers=_gh_headers(),
    )
    with urllib.request.urlopen(req) as r:
        files = json.loads(r.read()).get("files", {})
    if filename not in files:
        return None
    raw_req = urllib.request.Request(files[filename]["raw_url"], headers=_gh_headers())
    with urllib.request.urlopen(raw_req) as r:
        return json.loads(r.read())


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("X-API-Key", "") != os.environ.get("DASHBOARD_API_KEY", ""):
            self._json(401, {"error": "unauthorized"})
            return

        qs = parse_qs(urlparse(self.path).query)
        key = qs.get("key", [None])[0]
        if not key or key not in ALLOWED_KEYS:
            self._json(400, {"error": "invalid key"})
            return

        try:
            gist_id = _find_gist_id()
            if not gist_id:
                self._json(404, {"error": "not found"})
                return
            data = _read_file(gist_id, f"{key}.json")
            if data is None:
                self._json(404, {"error": "not found"})
                return
            self._json(200, data)
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass
