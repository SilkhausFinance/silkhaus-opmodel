# Journal Entries — Vendor Invoices (Property A-1203)

**Entity:** Silkhaus (Dubai STR rev-share)
**System:** NetSuite
**Property:** Unit A-1203 — Marina Gate Tower 1, Apt 1203 (Premise 2049913), Owner: Khan
**Currency:** AED
**Prepared:** 2026-06-16

> Note: These entries assist the close workflow but are not financial advice. Review and approve per the authorization matrix before posting.

---

## JE-001 — DEWA Utilities (Tax Invoice 700114882)

**Date:** 2026-05-31 | **Period:** May 2026
**Memo:** DEWA electricity & water + municipality housing fee, May 2026, Unit A-1203 (premise 2049913). Invoice 700114882.
**Vendor:** Dubai Electricity & Water Authority (DEWA)

| Line | Account | Class / Property | Debit (AED) | Credit (AED) |
|------|---------------------------------------|------------------|------------:|------------:|
| 1 | 6410 · Utilities Expense | A-1203 | 945.00 | |
| 2 | 1410 · Input VAT Recoverable | A-1203 | 47.25 | |
| 3 | 2010 · Accounts Payable — DEWA | A-1203 | | 992.25 |
| | **Totals** | | **992.25** | **992.25** |

---

## JE-002 — Sparkle Clean Cleaning Services (Invoice SC-2207)

**Date:** 2026-05-25 | **Period:** May 2026
**Memo:** Deep clean + turnover, Unit A-1203 (premise 2049913). Sparkle Clean invoice SC-2207.
**Vendor:** Sparkle Clean

| Line | Account | Class / Property | Debit (AED) | Credit (AED) |
|------|---------------------------------------|------------------|------------:|------------:|
| 1 | 6420 · Cleaning & Housekeeping Expense | A-1203 | 400.00 | |
| 2 | 1410 · Input VAT Recoverable | A-1203 | 20.00 | |
| 3 | 2011 · Accounts Payable — Sparkle Clean| A-1203 | | 420.00 |
| | **Totals** | | **420.00** | **420.00** |

---

## Totals (both entries)

| | Debit (AED) | Credit (AED) |
|---------------------------|------------:|------------:|
| Expense (utilities + cleaning) | 1,345.00 | |
| Input VAT recoverable | 67.25 | |
| Accounts payable | | 1,412.25 |
| **Total** | **1,412.25** | **1,412.25** |

---

## Assumptions & Notes

1. **Vendor bills (AP), not cash.** Booked as NetSuite Vendor Bills crediting Accounts Payable since no payment was indicated. If paid immediately, replace the AP credit with the bank/cash account.
2. **Input VAT recoverable (5%).** UAE short-term holiday-home rentals are standard-rated taxable supplies, so the 5% VAT on related operating costs is treated as recoverable input VAT (asset, acct 1410) rather than expensed. If A-1203 is in fact let on an exempt/long-term residential basis, VAT would instead be capitalized into the expense (utilities 992.25 / cleaning 420.00) and lines 2 removed.
3. **DEWA municipality housing fee** is included in the utilities expense line and is VAT-taxed in the invoice (VAT 47.25 = 5% × 945.00). If your policy books the housing/municipality fee to a separate account, split line 1 into 900.00 utilities + 45.00 municipality fee.
4. **Dates.** DEWA invoice has no explicit invoice date; used billing-period end (2026-05-31). Sparkle Clean dated 25/05/2026 (DD/MM/YYYY).
5. **Property dimension.** Costs tagged to NetSuite class/segment A-1203 for rev-share owner reporting (owner Khan). These are operator-incurred property operating costs; whether they are rebilled/net-settled against owner rev-share is a downstream settlement step, not part of these AP entries.
6. **Account numbers are indicative** — map to Silkhaus's actual NetSuite chart of accounts before posting.
7. **Both entries balance** (debits = credits) and are non-reversing (actual invoices, not accruals).
