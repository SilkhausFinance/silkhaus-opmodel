## Property-cost journal entries — Jun 2026

### LockSmart Ltd · (no invoice no.) · repairs-maintenance · C-0500 — recoverable
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Landlord Receivable — R&M (120059) | 1,000.00 | LockSmart Ltd 2026-06-15 — recoverable, C-0500 (RCM) |
| 2 | Dr | VAT on Purchases AE (110038) | 50.00 | Reverse charge 5% |
| 3 | Cr | VAT on Sales AE (110040) | 50.00 | Reverse charge 5% |
| 4 | Cr | Accounts Payable (110001) | 1,000.00 | LockSmart Ltd invoice (ref pending) |

**Balanced:** Dr 1,050.00 = Cr 1,050.00 ✓

### Totals
| Account (code) | Dr | Cr |
|----------------|---:|---:|
| Accounts Payable (110001) | 0.00 | 1,000.00 |
| VAT on Purchases AE (110038) | 50.00 | 0.00 |
| VAT on Sales AE (110040) | 0.00 | 50.00 |
| Landlord Receivable — R&M (120059) | 1,000.00 | 0.00 |
| **TOTAL** | **1,050.00** | **1,050.00** |

**All entries balance:** YES ✓

### Review flags
- LockSmart Ltd — **unit_type unknown** (lease vs rev-share): defaulted to **rev-share** per f7. Confirm. If C-0500 is actually a **lease** unit, this is Silkhaus-borne — replace line 1 with **Dr Repairs & Maintenance (620012) 1,000.00** (no landlord receivable).
- LockSmart Ltd — **recoverable unknown**: defaulted to **RECOVERABLE** (rev-share R&M recharge → Landlord Receivable R&M 120059). Confirm the cost is recharged to the landlord per policy; if not recharged, post to **Repairs & Maintenance (620012)** instead.
- LockSmart Ltd — **international vendor (UK-based), no VAT shown → assumed reverse charge (RCM)**, self-accounted Input VAT (110038) / Output VAT (110040) at 5%, net VAT nil. Confirm LockSmart has no UAE VAT registration (if it does and charged AED VAT, treat as `standard`).
- LockSmart Ltd — **RCM on a recoverable cost is an edge case.** The f7 worked examples cover recoverable R&M with *standard* VAT (cost booked net to the receivable; output VAT on the recharge raised at f8). Here, because the vendor is international, the cost is booked at the bill amount (AED 1,000) to the receivable and the reverse charge is self-accounted now. Controller to confirm: (a) the AED 1,000 receivable amount, and (b) how the f8 landlord-recharge output VAT interacts with the RCM output VAT already booked here, to avoid double-counting.
- LockSmart Ltd — **output VAT on the landlord recharge is raised at settlement (f8), not here** (standard f7 note for recoverable costs).
- LockSmart Ltd — **no invoice/reference number provided.** Capture the vendor invoice no. before posting (narration currently "ref pending").

---

### Assumptions applied (defaults posted, per skill's "post the default and flag" rule)
- **Category:** lock replacement → `repairs-maintenance`.
- **unit_type:** unknown → **rev-share** (f7 default for utilities & R&M).
- **Recoverable:** unknown → **Y / recoverable** (rev-share R&M is recharged by default) → Landlord Receivable — R&M (120059).
- **VAT treatment:** UK vendor + no VAT shown → **RCM** (reverse charge), not `none`.
- **Payment entry** (Dr A/P / Cr bank) intentionally omitted — f7 books to A/P; payment is a separate step.
