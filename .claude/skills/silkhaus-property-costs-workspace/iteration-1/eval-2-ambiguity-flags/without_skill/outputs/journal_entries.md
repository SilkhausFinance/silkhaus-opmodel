# Journal Entry — LockSmart Ltd Maintenance Invoice (Unit C-0500)

## Invoice summary

| Field | Value |
|---|---|
| Vendor | LockSmart Ltd (UK-based supplier) |
| Description | Smart-lock replacement, Unit C-0500 |
| Invoice amount | AED 1,000.00 |
| VAT shown on invoice | None (foreign supplier, no UAE VAT charged) |
| Cost category | Repairs & Maintenance |
| ERP | NetSuite |
| VAT regime | UAE 5% VAT |

---

## Two flagged issues and how they are handled

### 1. Reverse-charge VAT (import of services) — RESOLVED, applied

LockSmart Ltd is a **UK supplier** invoicing a **UAE business** with **no VAT on the invoice**. This is an **import of services**, which falls under the **UAE reverse-charge mechanism (RCM)**.

Under RCM, Silkhaus must **self-account for output VAT at 5%** and (assuming the cost is used for taxable supplies / fully recoverable) **claim an equal input VAT**. The two legs net to **zero cash VAT** but must both be recorded and reported on the VAT return (Box 3 output + Box 10 input, reverse charge).

- Reverse-charge VAT base: AED 1,000.00
- Reverse-charge VAT @ 5% = **AED 50.00** (output) and **AED 50.00** (input, recoverable)

**Net VAT cash impact: AED 0.** Net expense to the business: **AED 1,000** (the AED 50 is not a real cost because it is recovered).

> Assumption: Silkhaus is VAT-registered and uses C-0500 maintenance for taxable activity, so input VAT is fully recoverable. If the unit were used for VAT-exempt supply (not the case for STR), input VAT would be irrecoverable and the AED 50 would be added to expense.

### 2. C-0500 — leased unit vs. rev-share unit — UNKNOWN, assumption stated

The cost-bearer differs by unit type:

- **If LEASED:** Silkhaus holds the head-lease and bears maintenance itself → debit **Silkhaus's own Repairs & Maintenance expense** (P&L).
- **If REV-SHARE:** Silkhaus operates for the property owner; lock replacement is typically a **property/owner cost** → debit an **Owner Recoverable / Due-from-Owner** account (balance sheet), to be netted against the owner's next revenue-share payout, rather than hitting Silkhaus P&L.

> **Stated assumption for the primary entry:** Because the classification is unconfirmed, I book the **primary entry as a LEASED-unit expense** (the conservative treatment — it recognizes the cost in Silkhaus's own P&L now and does not assume a recovery from an owner that may not be contractually due). **Action required:** confirm C-0500's classification in the property master. If it is a **rev-share** unit, post the **Alternative entry** below instead, which reclassifies the debit to the owner-recoverable account.

---

## PRIMARY journal entry — assuming C-0500 is a LEASED unit (cost = Silkhaus P&L)

| Line | Account | Debit (AED) | Credit (AED) |
|---|---|---:|---:|
| 1 | Repairs & Maintenance — Smart Locks (P&L) | 1,000.00 | |
| 2 | Input VAT — Recoverable (Reverse Charge) | 50.00 | |
| 3 | Accounts Payable — LockSmart Ltd | | 1,000.00 |
| 4 | Output VAT Payable (Reverse Charge) | | 50.00 |
| | **Totals** | **1,050.00** | **1,050.00** |

- Memo: "LockSmart Ltd — smart-lock replacement, Unit C-0500. Import of services; 5% reverse-charge VAT self-accounted (output + recoverable input, net nil)."
- AP to LockSmart = **AED 1,000** (the actual amount payable to the UK supplier).
- NetSuite tax code: reverse-charge / import-of-services code (self-assessed), so both the output and recoverable input legs flow to the VAT return automatically.

---

## ALTERNATIVE journal entry — if C-0500 is a REV-SHARE unit (cost = owner recoverable)

| Line | Account | Debit (AED) | Credit (AED) |
|---|---|---:|---:|
| 1 | Owner Recoverable / Due from Property Owner (B/S) | 1,000.00 | |
| 2 | Input VAT — Recoverable (Reverse Charge) | 50.00 | |
| 3 | Accounts Payable — LockSmart Ltd | | 1,000.00 |
| 4 | Output VAT Payable (Reverse Charge) | | 50.00 |
| | **Totals** | **1,050.00** | **1,050.00** |

- Memo: "LockSmart Ltd — smart-lock replacement, rev-share Unit C-0500. Cost recoverable from owner; nets against next revenue-share payout. 5% reverse-charge VAT self-accounted (net nil)."
- Under this treatment the AED 1,000 is **not** a Silkhaus expense; it is parked as a receivable and cleared against the owner's payout.
- Reverse-charge VAT handling is identical regardless of unit type (the RCM obligation sits with Silkhaus as the importing entity).

---

## Summary of assumptions

1. **Reverse-charge VAT applies** (UK supplier → UAE business, import of services). Self-assessed output VAT AED 50 and recoverable input VAT AED 50; **net VAT cash = nil**.
2. **Input VAT is fully recoverable** (Silkhaus is VAT-registered; STR activity is taxable).
3. **C-0500 unit type is unconfirmed.** Primary entry assumes **leased** (Silkhaus P&L). If rev-share, use the Alternative entry (owner-recoverable). **Confirm in property master and adjust if needed.**
4. Amount payable to LockSmart Ltd is **AED 1,000** in both scenarios (no VAT remitted to the supplier).
