"""
Silkhaus Finance Hub — Bills API
Handles: config, Gmail OAuth+sync, bill extraction+CRUD, admin users, NetSuite CSV export.
"""
from flask import Flask, request, jsonify, Response, redirect
import json, os, io, csv, base64, re, mimetypes, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

app = Flask(__name__)

# ── Env vars (set in Vercel project settings) ────────────────────────────────
SUPABASE_URL         = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ANON_KEY    = os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY        = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
BASE_URL             = os.environ.get("BASE_URL") or os.environ.get("VERCEL_URL", "http://localhost:5000")
if BASE_URL and not BASE_URL.startswith("http"):
    BASE_URL = f"https://{BASE_URL}"

GMAIL_REDIRECT_URI = f"{BASE_URL}/api/gmail/callback"

UTILITY_CATEGORIES = [
    "Utilities - Electricity",
    "Utilities - Water",
    "Utilities - Gas",
    "Maintenance",
    "Repairs",
    "Cleaning",
]

EXTRACTION_PROMPT = f"""You are an accounts payable specialist for Silkhaus, a short-term rental property company in the UAE (Dubai/Abu Dhabi).

Read the attached bill or invoice document and extract structured data.

ACCEPTED CATEGORIES (only these):
{chr(10).join(f'- {c}' for c in UTILITY_CATEGORIES)}

These correspond to:
- Utilities - Electricity: DEWA, SEWA, or similar electricity providers
- Utilities - Water: DEWA Water, municipality water, sewerage charges
- Utilities - Gas: gas utility bills
- Maintenance: AC servicing, lift/elevator, pest control, building M&E, annual contracts
- Repairs: one-off repair work, plumbing, electrical repairs, contractor fix jobs
- Cleaning: cleaning services, housekeeping, janitorial, laundry

If the document is NOT one of these categories, return:
{{"error": "out_of_scope", "detected_category": "<what you think it is>"}}

Return ONLY valid JSON (no markdown):
{{
  "vendor_name": string or null,
  "bill_number": string or null,
  "bill_date": "YYYY-MM-DD" or null,
  "due_date": "YYYY-MM-DD" or null,
  "currency": "AED" or other ISO code,
  "amount": number (total amount due, net of tax) or null,
  "tax_amount": number (VAT amount if shown separately) or null,
  "category": one of the exact category strings above or null,
  "expense_nature": "Opex",
  "property_name": string (unit/building/property this bill covers, if visible) or null,
  "suggested_debit_account": string (e.g. "Utilities Expense", "Repairs & Maintenance Expense", "Cleaning Expense"),
  "suggested_credit_account": "Accounts Payable",
  "netsuite_memo": string (concise memo for NetSuite, include vendor + period if visible) or null,
  "confidence_notes": string (anything you are unsure about) or null
}}
"""


# ── Supabase client ──────────────────────────────────────────────────────────

def _sb():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ── Auth helpers ─────────────────────────────────────────────────────────────

def _auth():
    """Validate Supabase JWT from Authorization header. Returns (user_id, role)."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, None
    token = header[7:]
    try:
        sb = _sb()
        res = sb.auth.get_user(token)
        if not res or not res.user:
            return None, None
        uid = res.user.id
        prof = sb.table("profiles").select("role").eq("id", uid).single().execute()
        role = (prof.data or {}).get("role", "viewer")
        return uid, role
    except Exception:
        return None, None


def _preflight():
    if request.method == "OPTIONS":
        return "", 200
    return None


def _require(allowed_roles=None):
    uid, role = _auth()
    if not uid:
        return uid, role, (jsonify({"error": "unauthorized"}), 401)
    if allowed_roles and role not in allowed_roles:
        return uid, role, (jsonify({"error": "forbidden"}), 403)
    return uid, role, None


# ── Google / Gmail helpers ───────────────────────────────────────────────────

def _google_get(url, access_token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _google_get_bytes(url, access_token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _drive_file_id(url):
    patterns = [
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"docs\.google\.com/\w+/d/([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _sheets_id(url):
    m = re.search(r"spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else None


SUPPORTED_MIMES = {
    "application/pdf",
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/webp", "image/tiff", "image/bmp", "image/heic",
}


def _google_post(url, data):
    enc = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=enc, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _refresh_token():
    """Get stored Gmail refresh token from Supabase settings."""
    try:
        row = _sb().table("settings").select("value").eq("key", "gmail_refresh_token").single().execute()
        return (row.data or {}).get("value")
    except Exception:
        return None


def _get_access_token():
    """Exchange stored refresh token for a fresh access token."""
    rt = _refresh_token()
    if not rt:
        return None
    resp = _google_post("https://oauth2.googleapis.com/token", {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": rt,
        "grant_type": "refresh_token",
    })
    return resp.get("access_token")


# ── Claude extraction ────────────────────────────────────────────────────────

def _extract_from_bytes(file_bytes, filename):
    """Send file to Claude, return structured dict."""
    import anthropic
    media_type = mimetypes.guess_type(filename)[0] or "application/pdf"
    is_pdf = media_type == "application/pdf"
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    doc = {
        "type": "document" if is_pdf else "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.b64encode(file_bytes).decode(),
        },
    }
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": [doc, {"type": "text", "text": EXTRACTION_PROMPT}]}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)


def _build_je(extracted):
    amount = extracted.get("amount") or 0
    tax = extracted.get("tax_amount") or 0
    debit = extracted.get("suggested_debit_account", "Expense Account")
    lines = [{"type": "DR", "account": debit, "amount": amount}]
    if tax:
        lines.append({"type": "DR", "account": "VAT Recoverable", "amount": tax})
    lines.append({"type": "CR", "account": "Accounts Payable", "amount": amount + tax})
    return {
        "lines": lines,
        "memo": extracted.get("netsuite_memo") or f"Bill from {extracted.get('vendor_name', 'Unknown')}",
    }


# ── Config (public) ──────────────────────────────────────────────────────────

@app.route("/api/config")
def config():
    gmail_connected = bool(_refresh_token()) if SUPABASE_URL else False
    last_sync = None
    if gmail_connected:
        try:
            row = _sb().table("settings").select("value").eq("key", "gmail_last_sync").single().execute()
            last_sync = (row.data or {}).get("value")
        except Exception:
            pass
    return jsonify({
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
        "configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        "gmail_connected": gmail_connected,
        "gmail_last_sync": last_sync,
        "google_client_id": GOOGLE_CLIENT_ID,
    })


# ── Gmail OAuth ──────────────────────────────────────────────────────────────

@app.route("/api/gmail/auth-url")
def gmail_auth_url():
    uid, role, err = _require(["admin"])
    if err:
        return err
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join([
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
        ]),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return jsonify({"url": url})


@app.route("/api/gmail/callback")
def gmail_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error or not code:
        return redirect("/bills?gmail_error=1")
    try:
        tokens = _google_post("https://oauth2.googleapis.com/token", {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GMAIL_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return redirect("/bills?gmail_error=no_refresh_token")
        sb = _sb()
        sb.table("settings").upsert({
            "key": "gmail_refresh_token",
            "value": refresh_token,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        # Also store which account was authorized
        if tokens.get("id_token"):
            import base64 as b64
            parts = tokens["id_token"].split(".")
            if len(parts) >= 2:
                payload = json.loads(b64.b64decode(parts[1] + "=="))
                sb.table("settings").upsert({
                    "key": "gmail_account",
                    "value": payload.get("email", ""),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
    except Exception as e:
        return redirect(f"/bills?gmail_error={urllib.parse.quote(str(e))}")
    return redirect("/bills?gmail_connected=1")


@app.route("/api/gmail/sync", methods=["POST", "OPTIONS"])
def gmail_sync():
    p = _preflight()
    if p:
        return p
    uid, role, err = _require(["admin", "preparer"])
    if err:
        return err

    access_token = _get_access_token()
    if not access_token:
        return jsonify({"error": "gmail_not_connected"}), 400

    sb = _sb()

    # Incremental sync: use last_sync timestamp, fall back to 2026/06/01.
    # Pass {"from_date": "2026/06/01"} in the request body to force a full re-scan.
    body_data = request.get_json(silent=True) or {}
    from_date_override = body_data.get("from_date")
    if from_date_override:
        after_date = from_date_override
    else:
        try:
            row = sb.table("settings").select("value").eq("key", "gmail_last_sync").single().execute()
            last_val = (row.data or {}).get("value")
            if last_val:
                last_dt = datetime.fromisoformat(last_val.replace("Z", "+00:00"))
                after_date = last_dt.strftime("%Y/%m/%d")
            else:
                after_date = "2026/06/01"
        except Exception:
            after_date = "2026/06/01"

    query = f"has:attachment after:{after_date} -in:sent"

    try:
        msgs = _google_get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages?"
            + urllib.parse.urlencode({"q": query, "maxResults": 200}),
            access_token,
        ).get("messages", [])
    except Exception as e:
        return jsonify({"error": "gmail_read_failed", "detail": str(e)}), 500

    found, dupes, out_of_scope, errors = 0, 0, 0, 0

    def _save_bill(extracted, msg_id, subject, sender, dedup_key=None):
        nonlocal found, dupes, out_of_scope, errors
        if "error" in extracted:
            out_of_scope += 1
            return
        key = dedup_key or msg_id
        existing = sb.table("bills").select("id").eq("source_email_id", key).execute()
        if existing.data:
            dupes += 1
            return
        je = _build_je(extracted)
        try:
            sb.table("bills").insert({
                "vendor_name": extracted.get("vendor_name"),
                "bill_number": extracted.get("bill_number"),
                "bill_date": extracted.get("bill_date"),
                "due_date": extracted.get("due_date"),
                "currency": extracted.get("currency") or "AED",
                "amount": extracted.get("amount"),
                "tax_amount": extracted.get("tax_amount"),
                "category": extracted.get("category"),
                "expense_nature": "Opex",
                "property_name": extracted.get("property_name"),
                "suggested_debit_account": extracted.get("suggested_debit_account"),
                "suggested_credit_account": "Accounts Payable",
                "netsuite_memo": extracted.get("netsuite_memo"),
                "suggested_je": json.dumps(je),
                "extracted_data": json.dumps(extracted),
                "confidence_notes": extracted.get("confidence_notes"),
                "source": "gmail_sync",
                "source_email_id": key,
                "source_email_subject": subject,
                "source_email_from": sender,
                "status": "pending_review",
            }).execute()
            found += 1
        except Exception:
            errors += 1

    for msg_ref in msgs:
        msg_id = msg_ref["id"]

        try:
            msg = _google_get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full",
                access_token,
            )
        except Exception:
            errors += 1
            continue

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("subject", "")
        sender = headers.get("from", "")

        # ── 1. Direct PDF / image attachments ────────────────────────────────
        attachments = []
        def _walk(parts):
            for part in parts:
                mime = part.get("mimeType", "")
                if mime in SUPPORTED_MIMES and (part.get("body") or {}).get("attachmentId"):
                    attachments.append(part)
                if part.get("parts"):
                    _walk(part["parts"])

        _walk(msg.get("payload", {}).get("parts", []))

        for part in attachments:
            att_id = (part.get("body") or {}).get("attachmentId")
            filename = part.get("filename") or "attachment.pdf"
            dedup = f"{msg_id}:{att_id}"
            existing = sb.table("bills").select("id").eq("source_email_id", dedup).execute()
            if existing.data:
                dupes += 1
                continue
            try:
                att = _google_get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/attachments/{att_id}",
                    access_token,
                )
                file_bytes = base64.urlsafe_b64decode(att["data"] + "==")
                extracted = _extract_from_bytes(file_bytes, filename)
            except Exception:
                errors += 1
                continue
            _save_bill(extracted, msg_id, subject, sender, dedup_key=dedup)

        # ── 2. Google Sheets links in email body ──────────────────────────────
        # Extract plain text body from the message payload
        def _body_text(payload):
            """Recursively extract plain text from a Gmail message payload."""
            data = (payload.get("body") or {}).get("data", "")
            text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore") if data else ""
            for part in payload.get("parts", []):
                text += _body_text(part)
            return text

        body_text = _body_text(msg.get("payload", {}))
        sheet_urls = re.findall(r"https://docs\.google\.com/spreadsheets/d/[^\s\"'>]+", body_text)

        for sheet_url in set(sheet_urls):
            sid = _sheets_id(sheet_url)
            if not sid:
                continue
            try:
                sheet_data = _google_get(
                    f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/A:Z",
                    access_token,
                )
                rows = sheet_data.get("values", [])
            except Exception:
                errors += 1
                continue

            # Find all Drive file URLs within cell values
            drive_urls = []
            for row in rows:
                for cell in row:
                    if "drive.google.com" in str(cell) or "docs.google.com" in str(cell):
                        drive_urls.append(str(cell))

            for durl in drive_urls:
                fid = _drive_file_id(durl)
                if not fid:
                    continue
                dedup = f"{msg_id}:drive:{fid}"
                existing = sb.table("bills").select("id").eq("source_email_id", dedup).execute()
                if existing.data:
                    dupes += 1
                    continue
                try:
                    # Get file metadata to determine MIME type and filename
                    meta = _google_get(
                        f"https://www.googleapis.com/drive/v3/files/{fid}?fields=name,mimeType",
                        access_token,
                    )
                    fname = meta.get("name", "invoice.pdf")
                    file_bytes = _google_get_bytes(
                        f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media",
                        access_token,
                    )
                    extracted = _extract_from_bytes(file_bytes, fname)
                except Exception:
                    errors += 1
                    continue
                _save_bill(extracted, msg_id, subject, sender, dedup_key=dedup)

    # Update last sync timestamp
    sb.table("settings").upsert({
        "key": "gmail_last_sync",
        "value": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    return jsonify({"ok": True, "found": found, "dupes": dupes,
                    "out_of_scope": out_of_scope, "errors": errors,
                    "synced_from": after_date})


# ── Bill extraction (no DB save — used for manual upload review) ─────────────

@app.route("/api/bills/extract", methods=["POST", "OPTIONS"])
def extract():
    p = _preflight()
    if p:
        return p
    uid, role, err = _require(["admin", "preparer"])
    if err:
        return err

    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400

    try:
        extracted = _extract_from_bytes(f.read(), f.filename or "bill.pdf")
    except json.JSONDecodeError:
        return jsonify({"error": "extraction_parse_failed"}), 500
    except Exception as e:
        return jsonify({"error": "extraction_failed", "detail": str(e)}), 500

    if "error" in extracted:
        return jsonify(extracted), 422

    return jsonify({"ok": True, "extracted": extracted, "suggested_je": _build_je(extracted)})


# ── Bills CRUD ───────────────────────────────────────────────────────────────

@app.route("/api/bills", methods=["GET", "POST"])
def bills():
    uid, role, err = _require()
    if err:
        return err

    if request.method == "GET":
        sb = _sb()
        q = sb.table("bills").select("*").order("created_at", desc=True)
        for param, col in [("status", "status"), ("category", "category")]:
            if request.args.get(param):
                q = q.eq(col, request.args[param])
        if request.args.get("from"):
            q = q.gte("bill_date", request.args["from"])
        if request.args.get("to"):
            q = q.lte("bill_date", request.args["to"])
        result = q.execute()
        return jsonify({"bills": result.data or []})

    if role not in ("admin", "preparer"):
        return jsonify({"error": "forbidden"}), 403
    body = request.get_json(silent=True) or {}
    je = body.get("suggested_je")
    row = {
        "vendor_name": body.get("vendor_name"),
        "bill_number": body.get("bill_number"),
        "bill_date": body.get("bill_date"),
        "due_date": body.get("due_date"),
        "currency": body.get("currency") or "AED",
        "amount": body.get("amount"),
        "tax_amount": body.get("tax_amount"),
        "category": body.get("category"),
        "expense_nature": "Opex",
        "property_name": body.get("property_name"),
        "suggested_debit_account": body.get("suggested_debit_account"),
        "netsuite_memo": body.get("netsuite_memo"),
        "suggested_je": json.dumps(je) if isinstance(je, dict) else je,
        "extracted_data": json.dumps(body.get("extracted_data") or {}),
        "confidence_notes": body.get("confidence_notes"),
        "source": "manual_upload",
        "status": "pending_review",
    }
    result = _sb().table("bills").insert(row).execute()
    return jsonify({"ok": True, "bill": result.data[0] if result.data else row})


@app.route("/api/bills/<bill_id>", methods=["PATCH", "OPTIONS"])
def update_bill(bill_id):
    p = _preflight()
    if p:
        return p
    uid, role, err = _require(["admin", "preparer", "approver"])
    if err:
        return err

    body = request.get_json(silent=True) or {}
    updates = {}
    for k in ["vendor_name", "bill_number", "bill_date", "due_date", "amount",
              "tax_amount", "currency", "category", "property_name",
              "suggested_debit_account", "netsuite_memo", "review_notes", "status"]:
        if k in body:
            updates[k] = body[k]
    if "suggested_je" in body:
        je = body["suggested_je"]
        updates["suggested_je"] = json.dumps(je) if isinstance(je, dict) else je

    new_status = updates.get("status", "")
    if new_status in ("approved", "rejected", "exported"):
        updates["reviewed_by"] = uid
        updates["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    result = _sb().table("bills").update(updates).eq("id", bill_id).execute()
    return jsonify({"ok": True, "bill": result.data[0] if result.data else {}})


@app.route("/api/bills/export.csv")
def export_csv():
    uid, role, err = _require()
    if err:
        return err

    sb = _sb()
    q = sb.table("bills").select("*").order("bill_date", desc=True)
    for param, col in [("status", "status"), ("category", "category")]:
        if request.args.get(param):
            q = q.eq(col, request.args[param])
    if request.args.get("from"):
        q = q.gte("bill_date", request.args["from"])
    if request.args.get("to"):
        q = q.lte("bill_date", request.args["to"])

    bills_data = q.execute().data or []

    # NetSuite bill import format
    cols = [
        "External ID", "Type", "Vendor", "Date", "Due Date",
        "Account", "Amount (net)", "VAT Amount", "Currency",
        "Memo", "Category", "Property", "Status",
    ]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(cols)
    for b in bills_data:
        w.writerow([
            b.get("id", ""),
            "VendBill",
            b.get("vendor_name", ""),
            b.get("bill_date", ""),
            b.get("due_date", ""),
            b.get("suggested_debit_account", ""),
            b.get("amount", ""),
            b.get("tax_amount", ""),
            b.get("currency", "AED"),
            b.get("netsuite_memo", ""),
            b.get("category", ""),
            b.get("property_name", ""),
            b.get("status", ""),
        ])

    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=silkhaus-bills.csv"},
    )


# ── Admin ────────────────────────────────────────────────────────────────────

@app.route("/api/admin/users", methods=["GET"])
def list_users():
    uid, role, err = _require(["admin"])
    if err:
        return err
    result = _sb().table("profiles").select("*").order("created_at").execute()
    return jsonify({"users": result.data or []})


@app.route("/api/admin/users/<target_id>", methods=["PATCH", "OPTIONS"])
def update_user(target_id):
    p = _preflight()
    if p:
        return p
    uid, role, err = _require(["admin"])
    if err:
        return err
    body = request.get_json(silent=True) or {}
    new_role = body.get("role")
    if new_role not in ("admin", "preparer", "approver", "viewer"):
        return jsonify({"error": "invalid role"}), 400
    _sb().table("profiles").update({"role": new_role}).eq("id", target_id).execute()
    return jsonify({"ok": True})


@app.route("/api/admin/invite", methods=["POST", "OPTIONS"])
def invite_user():
    p = _preflight()
    if p:
        return p
    uid, role, err = _require(["admin"])
    if err:
        return err
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip()
    if not email:
        return jsonify({"error": "email required"}), 400
    try:
        _sb().auth.admin.invite_user_by_email(email)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
