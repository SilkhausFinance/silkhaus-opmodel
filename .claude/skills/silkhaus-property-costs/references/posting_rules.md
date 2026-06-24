# Silkhaus property-cost posting rules (f7) — chart of accounts & treatment

Derived from the Silkhaus operating model, stage **f7 — "Operations: servicing the occupied unit"**
(plus the VAT/RCM rules from f9 and the reverse-charge note in the revenue process). This is the
**source of truth** for property-cost entries. If a code here ever conflicts with a newer NetSuite
chart-of-accounts export the user provides, prefer the export and update this file.

Scope: costs of running an **occupied** unit — utilities, connectivity, cleaning, repairs &
maintenance, guest make-good, and any other unit operating cost. Furnishing/fit-out (f2/f3),
depreciation & prepaids (f11), payroll & overhead OpEx (f10), and landlord settlement (f8) are
*other* stages — out of scope here, but cross-referenced where a cost flows into them.

---

## 1. Chart of accounts (property costs)

### P&L expense accounts (Silkhaus-borne)
| Code | Account | Used for |
|---|---|---|
| 640004 | DEWA Consumption | Electricity & water consumption (DEWA) |
| 640005 | DEWA Municipality Fee | Municipality/housing fee on the DEWA bill |
| 630024 | Cooling Charges | District cooling (Empower / Emicool / Tabreed) |
| 630025 | Gas Charges | Piped/cylinder gas |
| 630026 | Mobile & Internet | Connectivity for the unit (du / Etisalat) |
| 620012 | Repairs & Maintenance | R&M when **not** recharged to the landlord |
| 620013 | Unit Cleaning Expenses | Cleaning — **always** Silkhaus-borne |
| 620011 | Guest Experience Expenses | Service-failure / guest make-good costs |
| 630061 | Apology / Booking Refund | Compensation/apology paid to a guest |

### Balance-sheet accounts
| Code | Account | Used for |
|---|---|---|
| 120060 | Landlord Receivable — Utilities | **Recoverable** utilities/connectivity on rev-share units |
| 120059 | Landlord Receivable — Repairs & Maintenance | **Recoverable** R&M on rev-share units (taxable reimbursement) |
| 110001 | Accounts Payable | Credit side of every vendor bill |
| 110038 | VAT on Purchases AE (Input VAT) | 5% input VAT on purchases; debit side of RCM |
| 110040 | VAT on Sales AE (Output VAT) | Output VAT — credit side of RCM; output VAT on landlord recharge (raised at f8) |
| 120023 | Bank — ENBD Opex | Cash account when the vendor is paid (payment is a separate step, usually omitted here) |

> Cross-stage: recoverable balances in 120060 / 120059 are recovered from the landlord at **f8
> settlement**, netted through the Revshare Payout — LL clearing (120091). Don't post the recovery
> here; just park the cost on the receivable.

---

## 2. The control: recoverable vs Silkhaus-borne

The single test in f7 is **"is the cost charged to the landlord?"** Decision order:

1. **Cleaning → Silkhaus-borne, always (620013).** Silkhaus recognises the cleaning *revenue* at
   booking (f4), so it bears the cleaning *cost*. Never recharge the landlord.
2. **Guest-experience / service failure / make-good → Silkhaus-borne (620011, or 630061 for a guest
   refund/apology).** A failure we caused is our cost.
3. **Lease unit → Silkhaus-borne** by definition → the category's P&L expense account.
4. **Rev-share unit, recharged (default for utilities & R&M) → RECOVERABLE** → Landlord Receivable
   (120060 utilities/connectivity, 120059 R&M).
5. **Rev-share unit, *not* recharged → Silkhaus-borne** → the category's P&L expense account.

Category → P&L expense account (when Silkhaus-borne):
`utility-dewa`→640004, `utility-municipality`→640005, `utility-cooling`→630024,
`utility-gas`→630025, `connectivity`→630026, `repairs-maintenance`→620012, `cleaning`→620013,
`guest-experience`→620011 (or 630061), `other`→closest matching P&L account (flag if unsure).

Category → landlord receivable (when recoverable):
utilities/connectivity (`utility-*`, `connectivity`) → **120060**; `repairs-maintenance` → **120059**.
(Cleaning and guest-experience are never recoverable.)

---

## 3. VAT / RCM rules

- **Standard (UAE VAT-registered vendor):** debit the expense/receivable at **net**, debit **Input
  VAT 110038** at 5% of net, credit **A/P 110001** at gross. `net = gross / 1.05`, `vat = gross − net`.
- **Reverse charge (RCM) — international vendor** (Guesty, Airbnb, Stripe and similar): book the
  expense at the bill amount, then self-account: **Dr Input VAT 110038 / Cr Output VAT 110040** at 5%
  of the bill (net VAT effect nil). Credit **A/P 110001** for the bill amount.
- **Recoverable cost VAT:** book the cost **net** to the landlord receivable and still claim input
  VAT (110038). The **output VAT on the recharge is raised when the landlord is invoiced at f8** —
  do not add an output-VAT line in the f7 entry; note it instead.
- **None/unknown:** post at gross, no VAT line, and raise a Review flag.

Rounding: compute VAT to 2 dp; if a vendor's printed VAT differs from `gross/1.05` by a rounding
cent, prefer the **printed** net/VAT and note it.

---

## 4. Worked examples

**A — Recoverable utility (rev-share, standard VAT).** DEWA, AED 1,050 gross, rev-share unit A-1203:
```
Dr  Landlord Receivable — Utilities (120060)   1,000.00   DEWA May-26, recoverable, unit A-1203
Dr  VAT on Purchases AE (110038)                   50.00   Input VAT 5%
Cr  Accounts Payable (110001)                   1,050.00   DEWA invoice D-558823
Balanced: 1,050.00 = 1,050.00 ✓  (output VAT on recharge → f8)
```

**B — Silkhaus-borne utility (lease unit).** Same DEWA bill, but unit is a lease unit:
```
Dr  DEWA Consumption (640004)                   1,000.00   DEWA May-26, lease unit L-0907
Dr  VAT on Purchases AE (110038)                   50.00   Input VAT 5%
Cr  Accounts Payable (110001)                   1,050.00   DEWA invoice D-558823
Balanced: 1,050.00 = 1,050.00 ✓
```

**C — Cleaning (always Silkhaus-borne).** Cleaning vendor, AED 315 gross:
```
Dr  Unit Cleaning Expenses (620013)               300.00   Turnover cleaning, unit A-1203
Dr  VAT on Purchases AE (110038)                   15.00   Input VAT 5%
Cr  Accounts Payable (110001)                     315.00   CleanCo invoice CC-4471
Balanced: 315.00 = 315.00 ✓
```

**D — Recoverable R&M (rev-share).** AC repair, AED 525 gross, rev-share unit:
```
Dr  Landlord Receivable — R&M (120059)            500.00   AC repair, recoverable, unit A-1203
Dr  VAT on Purchases AE (110038)                   25.00   Input VAT 5%
Cr  Accounts Payable (110001)                     525.00   FixIt invoice FX-220
Balanced: 525.00 = 525.00 ✓  (output VAT on recharge → f8)
```

**E — International vendor, RCM.** Software/tooling bill direct to the unit, AED 200, no VAT charged:
```
Dr  <expense account for category>                200.00   Vendor bill, RCM
Dr  VAT on Purchases AE (110038)                   10.00   Reverse charge 5%
Cr  VAT on Sales AE (110040)                        10.00   Reverse charge 5%
Cr  Accounts Payable (110001)                     200.00   Vendor invoice
Balanced: 210.00 = 210.00 ✓
```

**F — Guest make-good (Silkhaus-borne).** Apology refund to a guest, AED 400:
```
Dr  Apology / Booking Refund (630061)             400.00   Guest make-good — clean missed, unit A-1203
Cr  Bank / gateway                                400.00   Refund paid
Balanced: 400.00 = 400.00 ✓
```

---

## 5. Review-flag triggers (don't guess silently)
- Invoice not mapped to a unit (no premise→unit match).
- `unit_type` unknown (lease vs rev-share) → recoverability defaulted.
- Rev-share recharge policy unclear for this cost.
- Vendor possibly international → RCM assumed.
- VAT not shown / vendor VAT-registration status unclear.
- Cost doesn't fit a known category → account mapping is a guess.
- Printed VAT ≠ gross/1.05 (rounding) → used printed figures.
