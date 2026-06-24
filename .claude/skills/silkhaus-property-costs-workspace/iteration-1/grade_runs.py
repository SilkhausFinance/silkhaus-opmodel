#!/usr/bin/env python3
"""Grade silkhaus-property-costs runs against per-eval assertions.

Reads every output file (.md/.csv) in each run's outputs/ dir, concatenates the
text, and evaluates each assertion as a deterministic check. Writes grading.json
(fields: text / passed / evidence) into each run dir. Reusable across iterations.
"""
import json
import re
import shutil
from pathlib import Path

ITER = Path(__file__).resolve().parent


def load_text(run_dir: Path) -> str:
    out = run_dir / "outputs"
    if not out.is_dir():
        return ""
    parts = []
    for p in sorted(out.glob("*")):
        if p.suffix.lower() in (".md", ".csv", ".txt"):
            parts.append(p.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def has(t, *subs):
    return all(s in t for s in subs)


# Each checker takes the concatenated run text and returns (passed, evidence).
def evidence_for(code, t):
    return f"found '{code}'" if code in t else f"'{code}' not present"


def grade_eval0(t):
    res = []
    res.append(("Rev-share DEWA (A-1203) debits Landlord Receivable — Utilities (120060)",
                "120060" in t, evidence_for("120060", t)))
    res.append(("Rev-share plumbing R&M (FixIt) debits Landlord Receivable — R&M (120059)",
                "120059" in t, evidence_for("120059", t)))
    res.append(("Turnover cleaning (SparkleClean) is Silkhaus-borne to Unit Cleaning Expenses (620013)",
                "620013" in t, evidence_for("620013", t)))
    res.append(("Leased-unit DEWA (L-0907) is Silkhaus-borne to DEWA Consumption (640004)",
                "640004" in t, evidence_for("640004", t)))
    res.append(("Emicool cooling on a rev-share unit also debits Landlord Receivable — Utilities (120060)",
                "Emicool" in t and "120060" in t,
                "Emicool present with 120060" if ("Emicool" in t and "120060" in t) else "Emicool not tied to 120060"))
    res.append(("Splits 5% Input VAT to VAT on Purchases (110038)",
                "110038" in t, evidence_for("110038", t)))
    res.append(("Credits Accounts Payable (110001)",
                "110001" in t, evidence_for("110001", t)))
    bal = "3,983.00" in t
    res.append(("Every entry balances and the totals block foots to 3,983.00",
                bal, "totals foot to 3,983.00" if bal else "3,983.00 total not found"))
    invented = any(s in t for s in ("Due from Owner", "placeholder", "map to your", "indicative"))
    real = "110001" in t
    res.append(("Uses only real Silkhaus GL codes (no invented placeholder accounts like 'Due from Owner')",
                real and not invented,
                "real codes, no placeholders" if (real and not invented)
                else f"invented/placeholder language present ({'Due from Owner' if 'Due from Owner' in t else 'placeholder'})"))
    return res


def grade_eval1(t):
    res = []
    res.append(("Invoice master has a row for each invoice (DEWA 700114882 and SparkleClean SC-2207)",
                "700114882" in t and "SC-2207" in t,
                "both invoice numbers present" if ("700114882" in t and "SC-2207" in t) else "missing an invoice number"))
    res.append(("Premise 2049913 is mapped to unit A-1203",
                "2049913" in t and "A-1203" in t,
                "2049913 -> A-1203 present" if ("2049913" in t and "A-1203" in t) else "premise/unit mapping missing"))
    res.append(("DEWA recoverable cost debits Landlord Receivable — Utilities (120060)",
                "120060" in t, evidence_for("120060", t)))
    res.append(("Cleaning is Silkhaus-borne to Unit Cleaning Expenses (620013)",
                "620013" in t, evidence_for("620013", t)))
    res.append(("Splits 5% Input VAT (110038) and credits Accounts Payable (110001)",
                "110038" in t and "110001" in t,
                "110038 and 110001 present" if ("110038" in t and "110001" in t) else "missing 110038/110001"))
    res.append(("Every entry balances (foots to 1,412.25)",
                "1,412.25" in t, evidence_for("1,412.25", t)))
    invented = any(s in t for s in ("placeholder", "indicative", "6410", "6420", "1410", "2010"))
    res.append(("Uses only real Silkhaus GL codes (no invented placeholders)",
                "110001" in t and not invented,
                "real codes only" if ("110001" in t and not invented) else "invented codes/placeholder language present"))
    # quality: DEWA should be ONE entry, not split into duplicate sub-entries with repeated flags
    dewa_subentries = len(re.findall(r"DEWA · 700114882", t))
    dup_flag = t.count("output VAT on the landlord recharge is raised at settlement (f8), not here") > 1
    single = dewa_subentries <= 1 and not dup_flag
    res.append(("DEWA is booked as ONE entry (consumption + municipality combined), not split into duplicate sub-entries with repeated flags",
                single,
                f"{dewa_subentries} DEWA sub-entries; duplicate f8 flag={dup_flag}"))
    return res


def grade_eval2(t):
    res = []
    res.append(("Applies reverse charge: debits Input VAT (110038) and credits Output VAT (110040) at 5%",
                "110038" in t and "110040" in t,
                "110038 and 110040 present" if ("110038" in t and "110040" in t) else "missing real RCM VAT codes"))
    nil = re.search(r"net.{0,12}(nil|zero|0\b)", t, re.IGNORECASE) is not None
    res.append(("Reverse-charge VAT legs net to nil", nil,
                "states net VAT nil" if nil else "no 'net nil' statement"))
    res.append(("Entry balances (foots to 1,050.00)",
                "1,050.00" in t, evidence_for("1,050.00", t)))
    unknown = ("unknown" in t.lower() or "not sure" in t.lower() or "unconfirmed" in t.lower()) and \
              ("lease" in t.lower() and "rev-share" in t.lower())
    res.append(("Raises a review flag that unit type (lease vs rev-share) is unknown rather than silently guessing",
                unknown,
                "flags unknown lease vs rev-share" if unknown else "does not clearly flag unknown unit type"))
    recov = "recover" in t.lower() and ("lease" in t.lower() and "rev-share" in t.lower())
    res.append(("Flags that recoverability depends on lease-vs-rev-share",
                recov, "ties recoverability to unit type" if recov else "recoverability not tied to unit type"))
    invented = any(s in t for s in ("Due from Property Owner", "Owner Recoverable /", "Smart Locks (P&L)"))
    real = "110038" in t and ("120059" in t or "620012" in t)
    res.append(("Does not invent a GL code — uses real Silkhaus codes (e.g. 120059 / 620012 / 110038 / 110040)",
                real and not invented,
                "real Silkhaus codes used" if (real and not invented) else "invented account name(s) present / real codes missing"))
    return res


GRADERS = {0: grade_eval0, 1: grade_eval1, 2: grade_eval2}
EVAL_DIRS = {
    0: "eval-0-mixed-property-batch",
    1: "eval-1-email-to-master",
    2: "eval-2-ambiguity-flags",
}
CONFIGS = ["with_skill", "without_skill"]


def main():
    summary = []
    for eid, ename in EVAL_DIRS.items():
        for cfg in CONFIGS:
            run_dir = ITER / ename / cfg
            if not run_dir.is_dir():
                continue
            t = load_text(run_dir)
            graded = GRADERS[eid](t)
            expectations = [{"text": txt, "passed": bool(p), "evidence": ev} for (txt, p, ev) in graded]
            passed = sum(1 for e in expectations if e["passed"])
            total = len(expectations)
            out = {
                "eval_id": eid,
                "eval_name": ename,
                "configuration": cfg,
                "summary": {
                    "pass_rate": round(passed / total, 4) if total else 0.0,
                    "passed": passed,
                    "failed": total - passed,
                    "total": total,
                },
                "expectations": expectations,
            }
            # Viewer reads grading.json at the config level (sibling to outputs/).
            (run_dir / "grading.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
            # Aggregator requires <config>/run-1/{grading.json,timing.json}.
            run1 = run_dir / "run-1"
            run1.mkdir(exist_ok=True)
            (run1 / "grading.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
            timing_src = run_dir / "timing.json"
            if timing_src.exists():
                shutil.copy2(timing_src, run1 / "timing.json")
            summary.append(f"{ename:28s} {cfg:14s} {passed}/{total}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
