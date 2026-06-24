#!/usr/bin/env python3
"""
build_je.py — turn Silkhaus property-cost invoices into balanced, reviewable journal entries.

The model (Claude) extracts and classifies invoices into the invoice-master schema; this script
does the deterministic, error-prone part: pick the GL accounts per the f7 rules, do the VAT/RCM
math, and PROVE each entry balances. It exits non-zero if any entry fails to balance.

Inputs (one of):
  --in   invoice_master.csv      CSV with the invoice-master header (see assets/ template)
  --json '<single invoice JSON>' one classified invoice as a JSON object
  --json-file path.json          a JSON list (or single object) of classified invoices

Output:
  Markdown to stdout, or to --out FILE.

Invoice fields used: vendor, category, unit_id, premise_ref, unit_type (lease|revshare|unknown),
recoverable (Y|N|unknown|''), vat_treatment (standard|rcm|none|unknown), gross, vat, net,
invoice_no, invoice_date, period_start, period_end, currency, notes.

Source of truth for codes/treatment: ../references/posting_rules.md
"""
import argparse, csv, json, sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

CENT = Decimal("0.01")
def D(x):
    if x is None or x == "":
        return None
    try:
        return Decimal(str(x).replace(",", "").strip())
    except InvalidOperation:
        return None
def q(x):
    return (x if isinstance(x, Decimal) else Decimal(str(x))).quantize(CENT, ROUND_HALF_UP)

# --- GL map (property costs) — keep in sync with references/posting_rules.md ---
GL = {
    "640004": "DEWA Consumption",
    "640005": "DEWA Municipality Fee",
    "630024": "Cooling Charges",
    "630025": "Gas Charges",
    "630026": "Mobile & Internet",
    "620012": "Repairs & Maintenance",
    "620013": "Unit Cleaning Expenses",
    "620011": "Guest Experience Expenses",
    "630061": "Apology / Booking Refund",
    "120060": "Landlord Receivable — Utilities",
    "120059": "Landlord Receivable — R&M",
    "110001": "Accounts Payable",
    "110038": "VAT on Purchases AE",
    "110040": "VAT on Sales AE",
    "120023": "Bank — ENBD Opex",
}
def acct(code):
    return f"{GL.get(code, '??')} ({code})"

# category -> Silkhaus-borne P&L expense account
EXPENSE = {
    "utility-dewa": "640004",
    "utility-municipality": "640005",
    "utility-cooling": "630024",
    "utility-gas": "630025",
    "connectivity": "630026",
    "repairs-maintenance": "620012",
    "cleaning": "620013",
    "guest-experience": "620011",
    "other": None,            # must be confirmed
}
# categories eligible to be recharged to the landlord (rev-share)
RECOVERABLE_ELIGIBLE = {
    "utility-dewa", "utility-municipality", "utility-cooling",
    "utility-gas", "connectivity", "repairs-maintenance",
}
def receivable_acct(category):
    return "120059" if category == "repairs-maintenance" else "120060"

VAT_RATE = Decimal("0.05")


def classify(inv):
    """Return (debit_account_code, recoverable_bool, flags[])."""
    flags = []
    cat = (inv.get("category") or "other").strip().lower()
    unit_type = (inv.get("unit_type") or "unknown").strip().lower()
    rec_raw = (str(inv.get("recoverable") or "")).strip().lower()

    if cat not in EXPENSE:
        flags.append(f"unknown category '{cat}' — account mapping is a guess; confirm")
        cat = "other"

    # 1) cleaning: always Silkhaus-borne
    if cat == "cleaning":
        return "620013", False, flags
    # 2) guest-experience / make-good: always Silkhaus-borne
    if cat == "guest-experience":
        return "620011", False, flags
    # 3) lease unit: Silkhaus-borne by definition
    if unit_type == "lease":
        code = EXPENSE.get(cat)
        if not code:
            flags.append("category 'other' on a lease unit — pick the right P&L account, confirm")
        return code or "620012", False, flags
    # 4/5) rev-share (or unknown -> default rev-share)
    if unit_type == "unknown":
        flags.append("unit_type unknown — defaulted to rev-share; confirm lease vs rev-share")
    eligible = cat in RECOVERABLE_ELIGIBLE
    if rec_raw in ("y", "yes", "true", "1"):
        recoverable = True
    elif rec_raw in ("n", "no", "false", "0"):
        recoverable = False
    else:  # unknown
        recoverable = eligible
        if eligible:
            flags.append("recoverable unknown — defaulted to RECOVERABLE (rev-share recharge); confirm")
        else:
            flags.append("recoverable unknown — defaulted to Silkhaus-borne for this category; confirm")
    if recoverable and not eligible:
        flags.append(f"'{cat}' is not normally recharged — forcing Silkhaus-borne")
        recoverable = False
    if recoverable:
        return receivable_acct(cat), True, flags
    code = EXPENSE.get(cat)
    if not code:
        flags.append("category 'other' — pick the right P&L account, confirm")
    return code or "620012", False, flags


def vat_split(inv, flags):
    """Return (net, vat, gross, treatment). For RCM, 'net'==bill and vat is the self-accounted amount."""
    treatment = (inv.get("vat_treatment") or "unknown").strip().lower()
    gross = D(inv.get("gross"))
    vat = D(inv.get("vat"))
    net = D(inv.get("net"))

    if treatment == "rcm":
        bill = gross if gross is not None else net
        if bill is None:
            flags.append("RCM but no amount given")
            return None, None, None, treatment
        v = q(bill * VAT_RATE)
        return q(bill), v, q(bill), treatment

    if treatment == "none":
        amt = gross if gross is not None else (q((net or 0) + (vat or 0)) if (net or vat) else None)
        return amt, Decimal("0.00"), amt, treatment

    if treatment == "standard":
        if net is not None and vat is not None:
            g = q(net + vat)
            if gross is not None and q(gross) != g:
                flags.append(f"printed gross {q(gross)} ≠ net+VAT {g}; used printed net/VAT")
            return q(net), q(vat), g, treatment
        if gross is not None:
            n = q(gross / (Decimal("1") + VAT_RATE))
            return n, q(gross - n), q(gross), treatment
        flags.append("standard VAT but no amounts given")
        return None, None, None, treatment

    # unknown
    flags.append("vat_treatment unknown — posted at gross with no VAT line; confirm")
    amt = gross if gross is not None else net
    return amt, Decimal("0.00"), amt, "unknown"


def build_entry(inv):
    flags = []
    debit_code, recoverable, cflags = classify(inv)
    flags += cflags
    net, vat, gross, treatment = vat_split(inv, flags)
    lines = []  # (drcr, code, amount, narration)

    unit = inv.get("unit_id") or inv.get("premise_ref") or "unit ?"
    if not (inv.get("unit_id") or inv.get("premise_ref")):
        flags.append("no unit/premise mapped — confirm which unit this belongs to")
    period = inv.get("period_start") or inv.get("invoice_date") or ""
    bearer = "recoverable" if recoverable else "Silkhaus-borne"
    base_narr = f"{inv.get('vendor','vendor')} {period} — {bearer}, {unit}".strip()
    inv_no = inv.get("invoice_no") or "?"

    if net is None:
        flags.append("could not determine amounts — entry not built")
        return {"inv": inv, "lines": [], "flags": flags, "balanced": False,
                "dr": Decimal("0.00"), "cr": Decimal("0.00"), "recoverable": recoverable}

    if treatment == "rcm":
        lines.append(("Dr", debit_code, net, base_narr + " (RCM)"))
        lines.append(("Dr", "110038", vat, "Reverse charge 5%"))
        lines.append(("Cr", "110040", vat, "Reverse charge 5%"))
        lines.append(("Cr", "110001", net, f"{inv.get('vendor','vendor')} invoice {inv_no}"))
    else:
        # standard / none / unknown
        lines.append(("Dr", debit_code, net, base_narr))
        if vat and vat > 0:
            lines.append(("Dr", "110038", vat, "Input VAT 5%"))
        cr_amt = q(net + (vat or 0))
        lines.append(("Cr", "110001", cr_amt, f"{inv.get('vendor','vendor')} invoice {inv_no}"))

    if recoverable:
        flags.append("output VAT on the landlord recharge is raised at settlement (f8), not here")

    dr = q(sum((a for d, c, a, n in lines if d == "Dr"), Decimal("0")))
    cr = q(sum((a for d, c, a, n in lines if d == "Cr"), Decimal("0")))
    return {"inv": inv, "lines": lines, "flags": flags, "balanced": dr == cr,
            "dr": dr, "cr": cr, "recoverable": recoverable}


def fmt(amount):
    return f"{amount:,.2f}"


def render(entries, period_label):
    out = []
    out.append(f"## Property-cost journal entries — {period_label}\n")
    totals = {}  # code -> [dr, cr]
    all_flags = []
    ok = True
    for e in entries:
        inv = e["inv"]
        head = f"{inv.get('vendor','vendor')} · {inv.get('invoice_no','?')} · {inv.get('category','?')} · " \
               f"{inv.get('unit_id') or inv.get('premise_ref') or 'unit ?'} — " \
               f"{'recoverable' if e['recoverable'] else 'Silkhaus-borne'}"
        out.append(f"### {head}")
        if not e["lines"]:
            out.append("_Could not build this entry — see flags._\n")
        else:
            out.append("| # | Dr/Cr | Account (code) | Amount (AED) | Narration |")
            out.append("|---|-------|----------------|-------------:|-----------|")
            for i, (drcr, code, amt, narr) in enumerate(e["lines"], 1):
                out.append(f"| {i} | {drcr} | {acct(code)} | {fmt(amt)} | {narr} |")
                t = totals.setdefault(code, [Decimal('0'), Decimal('0')])
                t[0 if drcr == 'Dr' else 1] += amt
            mark = "✓" if e["balanced"] else "✗ NOT BALANCED"
            out.append(f"\n**Balanced:** Dr {fmt(e['dr'])} = Cr {fmt(e['cr'])} {mark}\n")
        if not e["balanced"]:
            ok = False
        for f in e["flags"]:
            all_flags.append(f"{inv.get('vendor','vendor')} {inv.get('invoice_no','?')} — {f}")

    # totals
    out.append("### Totals")
    out.append("| Account (code) | Dr | Cr |")
    out.append("|----------------|---:|---:|")
    tdr = tcr = Decimal('0')
    for code in sorted(totals):
        dr, cr = totals[code]
        tdr += dr; tcr += cr
        out.append(f"| {acct(code)} | {fmt(q(dr))} | {fmt(q(cr))} |")
    out.append(f"| **TOTAL** | **{fmt(q(tdr))}** | **{fmt(q(tcr))}** |")
    out.append(f"\n**All entries balance:** {'YES ✓' if ok and q(tdr)==q(tcr) else 'NO ✗'}\n")

    # flags
    out.append("### Review flags")
    if all_flags:
        for f in all_flags:
            out.append(f"- {f}")
    else:
        out.append("- None.")
    return "\n".join(out) + "\n", ok


def load_invoices(args):
    if args.json:
        obj = json.loads(args.json)
        return obj if isinstance(obj, list) else [obj]
    if args.json_file:
        with open(args.json_file) as fh:
            obj = json.load(fh)
        return obj if isinstance(obj, list) else [obj]
    if args.in_csv:
        with open(args.in_csv, newline="") as fh:
            return list(csv.DictReader(fh))
    raise SystemExit("Provide --in CSV, --json '<obj>', or --json-file path.json")


def main():
    p = argparse.ArgumentParser(description="Build Silkhaus property-cost journal entries.")
    p.add_argument("--in", dest="in_csv", help="invoice_master.csv")
    p.add_argument("--json", help="single invoice as a JSON object")
    p.add_argument("--json-file", help="JSON list/object of invoices")
    p.add_argument("--out", help="write markdown here (default: stdout)")
    p.add_argument("--period", default="period", help="label for the heading, e.g. 'May 2026'")
    args = p.parse_args()

    invoices = load_invoices(args)
    entries = [build_entry(inv) for inv in invoices]
    md, ok = render(entries, args.period)

    if args.out:
        with open(args.out, "w") as fh:
            fh.write(md)
        print(f"Wrote {args.out} ({len(entries)} entr{'y' if len(entries)==1 else 'ies'}). "
              f"All balanced: {'YES' if ok else 'NO'}")
    else:
        print(md)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
