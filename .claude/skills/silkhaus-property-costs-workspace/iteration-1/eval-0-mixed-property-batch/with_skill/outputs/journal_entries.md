# Property-cost journal entries — May 2026 close

Generated with the `silkhaus-property-costs` skill (f7 rules). Each entry was built and
balance-checked by `scripts/build_je.py` (exit 0, all balanced). All amounts AED; vendor
invoices are UAE VAT-registered, so VAT is treated as **standard** input VAT (5% extracted
from the gross). Output VAT on landlord recharges is raised at settlement (f8), not here.

## Property-cost journal entries — May 2026

### DEWA · (inv. no. not provided) · utility-dewa · A-1203 (owner Khan) — recoverable
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Landlord Receivable — Utilities (120060) | 1,200.00 | DEWA May-26 electricity & water — recoverable, unit A-1203 |
| 2 | Dr | VAT on Purchases AE (110038) | 60.00 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001) | 1,260.00 | DEWA invoice (no. n/a) |

**Balanced:** Dr 1,260.00 = Cr 1,260.00 ✓  *(output VAT on recharge → f8)*

### SparkleClean · (inv. no. not provided) · cleaning · A-1203 — Silkhaus-borne
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Unit Cleaning Expenses (620013) | 400.00 | Turnover cleaning — Silkhaus-borne, unit A-1203 |
| 2 | Dr | VAT on Purchases AE (110038) | 20.00 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001) | 420.00 | SparkleClean invoice (no. n/a) |

**Balanced:** Dr 420.00 = Cr 420.00 ✓

### FixIt · (inv. no. not provided) · repairs-maintenance · A-1203 (owner Khan) — recoverable
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Landlord Receivable — R&M (120059) | 700.00 | Plumbing repair — recoverable, unit A-1203 |
| 2 | Dr | VAT on Purchases AE (110038) | 35.00 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001) | 735.00 | FixIt invoice (no. n/a) |

**Balanced:** Dr 735.00 = Cr 735.00 ✓  *(output VAT on recharge → f8)*

### DEWA · (inv. no. not provided) · utility-dewa · L-0907 — Silkhaus-borne
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | DEWA Consumption (640004) | 933.33 | DEWA May-26 — leased unit, Silkhaus-borne, unit L-0907 |
| 2 | Dr | VAT on Purchases AE (110038) | 46.67 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001) | 980.00 | DEWA invoice (no. n/a) |

**Balanced:** Dr 980.00 = Cr 980.00 ✓

### Emicool · (inv. no. not provided) · utility-cooling · B-0801 (owner Mensah) — recoverable
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Landlord Receivable — Utilities (120060) | 560.00 | Emicool district cooling — recoverable, unit B-0801 |
| 2 | Dr | VAT on Purchases AE (110038) | 28.00 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001) | 588.00 | Emicool invoice (no. n/a) |

**Balanced:** Dr 588.00 = Cr 588.00 ✓  *(output VAT on recharge → f8)*

### Totals
| Account (code) | Dr | Cr |
|----------------|---:|---:|
| Accounts Payable (110001) | 0.00 | 3,983.00 |
| VAT on Purchases AE (110038) | 189.67 | 0.00 |
| Landlord Receivable — R&M (120059) | 700.00 | 0.00 |
| Landlord Receivable — Utilities (120060) | 1,760.00 | 0.00 |
| Unit Cleaning Expenses (620013) | 400.00 | 0.00 |
| DEWA Consumption (640004) | 933.33 | 0.00 |
| **TOTAL** | **3,983.00** | **3,983.00** |

**All entries balance:** YES ✓

### Classification summary (the f7 control applied)
| Vendor | Unit | Type | Cost charged to landlord? | Treatment | Debit account |
|---|---|---|---|---|---|
| DEWA | A-1203 | rev-share | Yes (utility, default recharge) | Recoverable | Landlord Receivable — Utilities (120060) |
| SparkleClean | A-1203 | rev-share | No — cleaning is **never** recharged | Silkhaus-borne | Unit Cleaning Expenses (620013) |
| FixIt | A-1203 | rev-share | Yes (R&M, default recharge) | Recoverable | Landlord Receivable — R&M (120059) |
| DEWA | L-0907 | **lease** | No — lease unit, borne by definition | Silkhaus-borne | DEWA Consumption (640004) |
| Emicool | B-0801 | rev-share | Yes (cooling = utility, default recharge) | Recoverable | Landlord Receivable — Utilities (120060) |

### Review flags
- **DEWA A-1203 / FixIt A-1203 / Emicool B-0801 (recoverable):** output VAT on the landlord
  recharge is raised when the landlord is invoiced at **f8 settlement**, not in these f7 entries.
  The cost sits net on the landlord receivable (120060 / 120059); Silkhaus still claims the 5%
  input VAT now.
- **SparkleClean cleaning:** booked Silkhaus-borne to Unit Cleaning Expenses (620013) per the f7
  rule that cleaning is never recharged (Silkhaus recognises the cleaning revenue at booking).
  Confirm this turnover clean was a normal clean and **not** a guest service-failure make-good
  (which would route to Guest Experience 620011 instead).
- **Vendor invoice numbers / dates:** none were provided in the source. Invoice date defaulted to
  the close date 2026-05-31 and invoice no. left as "n/a" — populate from the actual vendor PDFs
  before posting so the entries are traceable.

### Assumptions stated (per task constraints — no external accounts accessed)
1. All five vendors (DEWA, SparkleClean, FixIt, Emicool) are **UAE VAT-registered**, so the AED
   amounts are gross and include 5% VAT → posted as standard input VAT. None are international,
   so no reverse-charge (RCM) treatment applies.
2. The stated amounts are the **gross/total** payable; net = gross ÷ 1.05, VAT = gross − net.
3. Rev-share units follow the **default recharge policy** for utilities and R&M → recoverable.
   L-0907 is a leased unit, so its DEWA cost is Silkhaus-borne.
4. Emicool district cooling is classified as a utility (`utility-cooling`), so its recoverable
   leg uses Landlord Receivable — Utilities (120060), consistent with the posting rules.
5. Entries stop at A/P (cost booked, f7). The vendor-payment entry (Dr 110001 / Cr bank 120023)
   is a separate downstream step and is intentionally excluded.
