from flask import Flask, request, jsonify
import json
import os
import urllib.request
import urllib.error

app = Flask(__name__)

ALLOWED_KEYS = {"finance", "opmodel", "opmodel-reviews"}
GIST_DESC = "silkhaus-dashboard-data"


def _check_auth():
    return request.headers.get("X-API-Key", "") == os.environ.get("DASHBOARD_API_KEY", "")


def _gh_headers(content_type=False):
    h = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "silkhaus-opmodel",
    }
    if content_type:
        h["Content-Type"] = "application/json"
    return h


def _find_gist_id():
    req = urllib.request.Request("https://api.github.com/gists", headers=_gh_headers())
    with urllib.request.urlopen(req) as r:
        for g in json.loads(r.read()):
            if g.get("description") == GIST_DESC:
                return g["id"]
    return None


def _read_file(gist_id, filename):
    req = urllib.request.Request(
        f"https://api.github.com/gists/{gist_id}", headers=_gh_headers()
    )
    with urllib.request.urlopen(req) as r:
        files = json.loads(r.read()).get("files", {})
    if filename not in files:
        return None
    raw_req = urllib.request.Request(files[filename]["raw_url"], headers=_gh_headers())
    with urllib.request.urlopen(raw_req) as r:
        return json.loads(r.read())


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
            data=payload, method="POST", headers=_gh_headers(content_type=True),
        )
    else:
        req = urllib.request.Request(
            f"https://api.github.com/gists/{gist_id}",
            data=payload, method="PATCH", headers=_gh_headers(content_type=True),
        )
    with urllib.request.urlopen(req) as r:
        json.loads(r.read())


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/data/load")
def load():
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    key = request.args.get("key")
    if not key or key not in ALLOWED_KEYS:
        return jsonify({"error": "invalid key"}), 400
    try:
        gist_id = _find_gist_id()
        if not gist_id:
            return jsonify({"error": "not found"}), 404
        data = _read_file(gist_id, f"{key}.json")
        if data is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/data/save", methods=["POST", "OPTIONS"])
def save():
    if request.method == "OPTIONS":
        return "", 200
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "invalid body"}), 400
    key = body.get("key")
    data = body.get("data")
    if not key or key not in ALLOWED_KEYS:
        return jsonify({"error": "invalid key"}), 400
    try:
        _upsert(f"{key}.json", json.dumps(data))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
