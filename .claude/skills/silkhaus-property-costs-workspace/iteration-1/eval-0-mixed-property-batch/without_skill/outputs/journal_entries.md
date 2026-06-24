# May 2026 Close — Property Bills Journal Entries

**Entity:** Silkhaus (Dubai STR / rev-share)  |  **ERP:** NetSuite  |  **Period:** May 2026
**Currency:** AED  |  **VAT:** UAE standard rate 5%, amounts stated VAT-inclusive
**Prepared for review — not yet posted.**

---

## Key treatment logic (read before reviewing)

| Driver | Treatment |
|---|---|
| **Rev-share unit, owner-cost** (utilities, structural/plumbing repairs) | Cost economically belongs to the owner. Booked to a **Due from Owner** receivable (recoverable), credited to the vendor/accrual. **Not** Silkhaus P&L expense. Input VAT passes through to owner (not reclaimed by Silkhaus). |
| **Rev-share unit, operator-cost** (turnover cleaning of a guest stay) | Cost of delivering the guest stay; borne by Silkhaus, not recharged to owner. Booked to **Silkhaus P&L expense**; input VAT reclaimable. |
| **Leased unit** (Silkhaus is lessee/operator) | Silkhaus bears the cost. Booked to **Silkhaus P&L expense**; input VAT reclaimable. |

**Assumptions stated (override at review if your policy differs):**
1. All five amounts are VAT-inclusive at 5%; net = gross ÷ 1.05.
2. Rev-share utilities (DEWA, Emicool) and the plumbing repair are **owner-recoverable** → balance-sheet receivable, no Silkhaus expense, no Silkhaus input-VAT reclaim (VAT recharged to owner with the cost).
3. Turnover cleaning on the rev-share unit is an **operator cost** → Silkhaus expense + input VAT reclaim.
4. Leased-unit DEWA is a **Silkhaus expense** + input VAT reclaim.
5. Vendors are VAT-registered, so input VAT is shown on the operator/leased items. If a vendor is not registered, drop the VAT line and gross-up the expense.
6. Credits are booked to **Accounts Payable** per vendor (these are bills). If you prefer accrual at close, swap AP for **Accrued Expenses**.
7. GL account numbers are placeholders — map to your NetSuite chart before posting.

---

## Journal Entries (one JE per bill)

### JE-01 — DEWA, Unit A-1203 (rev-share, Owner: Khan) — owner-recoverable
| Account | Dept/Class | Property | Debit | Credit |
|---|---|---|---|---|
| 1310 · Due from Owner – Khan | Rev-share | A-1203 | 1,260.00 | |
| 2000 · Accounts Payable – DEWA | | A-1203 | | 1,260.00 |
| **Totals** | | | **1,260.00** | **1,260.00** |

*Recoverable utility recharged to owner at gross (AED 1,200.00 net + AED 60.00 VAT passed through). No Silkhaus expense / no input-VAT reclaim.*

### JE-02 — Turnover cleaning, SparkleClean, Unit A-1203 — operator cost
| Account | Dept/Class | Property | Debit | Credit |
|---|---|---|---|---|
| 6200 · Cleaning & Turnover Expense | STR Ops | A-1203 | 400.00 | |
| 1450 · Input VAT Recoverable | | A-1203 | 20.00 | |
| 2000 · Accounts Payable – SparkleClean | | A-1203 | | 420.00 |
| **Totals** | | | **420.00** | **420.00** |

### JE-03 — Plumbing repair, FixIt, Unit A-1203 (rev-share) — owner-recoverable
| Account | Dept/Class | Property | Debit | Credit |
|---|---|---|---|---|
| 1310 · Due from Owner – Khan | Rev-share | A-1203 | 735.00 | |
| 2000 · Accounts Payable – FixIt | | A-1203 | | 735.00 |
| **Totals** | | | **735.00** | **735.00** |

*Repair on a rev-share unit recharged to owner at gross (AED 700.00 net + AED 35.00 VAT passed through). No Silkhaus expense / no input-VAT reclaim.*

### JE-04 — DEWA, Unit L-0907 (leased unit) — Silkhaus expense
| Account | Dept/Class | Property | Debit | Credit |
|---|---|---|---|---|
| 6100 · Utilities Expense | STR Ops | L-0907 | 933.33 | |
| 1450 · Input VAT Recoverable | | L-0907 | 46.67 | |
| 2000 · Accounts Payable – DEWA | | L-0907 | | 980.00 |
| **Totals** | | | **980.00** | **980.00** |

### JE-05 — Emicool district cooling, Unit B-0801 (rev-share, Owner: Mensah) — owner-recoverable
| Account | Dept/Class | Property | Debit | Credit |
|---|---|---|---|---|
| 1310 · Due from Owner – Mensah | Rev-share | B-0801 | 588.00 | |
| 2000 · Accounts Payable – Emicool | | B-0801 | | 588.00 |
| **Totals** | | | **588.00** | **588.00** |

*Recoverable cooling charge recharged to owner at gross (AED 560.00 net + AED 28.00 VAT passed through). No Silkhaus expense / no input-VAT reclaim.*

---

## Batch summary

| JE | Property | Vendor | Type | Gross (AED) | Net | VAT | Debit account |
|---|---|---|---|---:|---:|---:|---|
| JE-01 | A-1203 | DEWA | Rev-share / owner-recoverable | 1,260.00 | 1,200.00 | 60.00 | Due from Owner – Khan |
| JE-02 | A-1203 | SparkleClean | Operator expense | 420.00 | 400.00 | 20.00 | Cleaning Expense |
| JE-03 | A-1203 | FixIt | Rev-share / owner-recoverable | 735.00 | 700.00 | 35.00 | Due from Owner – Khan |
| JE-04 | L-0907 | DEWA | Leased / Silkhaus expense | 980.00 | 933.33 | 46.67 | Utilities Expense |
| JE-05 | B-0801 | Emicool | Rev-share / owner-recoverable | 588.00 | 560.00 | 28.00 | Due from Owner – Mensah |
| **Total** | | | | **3,983.00** | **3,793.33** | **189.67** | |

### Where the AED 3,983.00 lands
| Bucket | Amount (AED) |
|---|---:|
| Due from Owner – Khan (A-1203: DEWA + plumbing, gross) | 1,995.00 |
| Due from Owner – Mensah (B-0801: Emicool, gross) | 588.00 |
| **Total owner-recoverable receivable** | **2,583.00** |
| Silkhaus P&L expense (Cleaning 400.00 + Utilities 933.33) | 1,333.33 |
| Input VAT recoverable (20.00 + 46.67) | 66.67 |
| **Total Silkhaus-borne (expense + reclaimable VAT)** | **1,400.00** |
| Accounts Payable (sum of all five vendor bills, gross) | 3,983.00 |

**Check:** Owner-recoverable 2,583.00 + Silkhaus-borne 1,400.00 = 3,983.00 = total AP credited. ✔ Each JE balances.

---

### Review flags
- **Owner-recoverable VAT:** I assumed input VAT on rev-share owner costs is passed through to the owner (booked gross to Due from Owner, no Silkhaus reclaim). If Silkhaus is the principal contracting party and reclaims that VAT, move AED 60 + 35 + 28 = **123.00** to Input VAT Recoverable and reduce the owner receivables accordingly.
- **Turnover cleaning:** treated as Silkhaus operator cost. If your rev-share contract recharges cleaning to the owner (or it's a pass-through guest charge), reclassify JE-02 to Due from Owner – Khan like JE-01/03.
- **AP vs. accrual:** booked to AP as vendor bills. If these are accrued at close pending invoices, replace AP with Accrued Expenses and reverse next period.
- **GL codes / NetSuite dimensions:** account numbers are placeholders; populate Subsidiary, Department/Class, and the Property/Location segment per your NetSuite setup.
