---
name: silkhaus-property-costs
description: >-
  Turn Silkhaus property/unit operating-cost vendor invoices into reviewable NetSuite journal
  entries, using Silkhaus's real chart of accounts and the f7 "Operations — servicing the
  occupied unit" posting rules. Two stages: (1) scan Gmail for vendor invoices and build/append a
  structured "invoice master" register, then (2) turn that register into a balanced, reviewable
  JE table. Handles the core control — deciding whether each cost is RECOVERABLE from the landlord
  (rev-share) or BORNE by Silkhaus (lease / un-recharged / service failure) — plus 5% input VAT
  and reverse-charge (RCM) for international vendors. USE THIS SKILL whenever the user wants to
  book or account for property costs: utilities (DEWA consumption & municipality, cooling/Empower,
  gas, mobile & internet), unit cleaning, repairs & maintenance, guest make-good, or "any other
  property cost"; whenever they say "build the invoice master", "scan my email/Gmail for invoices",
  "book the DEWA bills", "cleaning invoices", "R&M entries", "recharge to the landlord", "utility
  recovery", "is this recoverable", or are doing the month-end property-cost / operations close.
  Trigger even if they don't name a GL code or say "journal entry" — if the input is a property
  vendor invoice and the goal is the accounting treatment, this is the skill.
---

# Silkhaus — property-cost accounting (f7)

This skill automates the **Operations / property-cost** leg of the Silkhaus revenue-share model
(stage **f7** in the operating model). It takes vendor invoices for running an occupied unit and
produces the correct journal entries, with the recoverable-vs-borne control applied and VAT handled.

It runs in two stages. You can run either alone, but the normal flow is 1 → 2.

```
 Gmail invoices ──▶ [Stage 1] Invoice master (register) ──▶ [Stage 2] Reviewable JE table
```

**Source of truth for the chart of accounts:** `references/posting_rules.md` (derived from the
Silkhaus operating model, f7). Always read it before generating entries — do not invent GL codes.

**Golden rule:** every entry must balance (Σ debits = Σ credits) and every account used must exist
in `references/posting_rules.md`. The output is a *reviewable* table for a controller to sign off —
when anything is uncertain (which unit, lease vs rev-share, recoverable vs not, VAT treatment),
do **not** guess silently: post your best treatment **and** raise it in a "Review flags" list.

---

## Stage 1 — Build the invoice master (scan Gmail)

Goal: produce a clean, structured register of property-cost invoices from the user's mailbox, so
Stage 2 has reliable inputs. Use whatever email/Gmail MCP tools are available in the session
(e.g. `search_threads`, `get_thread`); if an invoice is a PDF attachment, read it as a document
(use the `pdf` skill or any available PDF text extraction).

### 1a. Find the invoices
Search the mailbox for property-cost vendor invoices for the period in question. Cast a wide net,
then filter. Useful query building blocks (combine with a date range for the close period):

- **Subjects/keywords:** `"tax invoice"`, `invoice`, `statement`, `bill`, `receipt`, `DEWA`,
  `Empower`, `Emicool`, `tabreed`, `cooling`, `gas`, `du OR etisalat OR internet`, `cleaning`,
  `maintenance OR repair`.
- **Likely senders:** utility providers (DEWA, Empower/Emicool, gas supplier, du/Etisalat),
  the cleaning vendor(s), maintenance contractors, and any building/owners-association billers.

Ask the user to confirm the period and any vendor names you don't recognise rather than assuming.

### 1b. Extract these fields per invoice
Read each invoice (body or attachment) and pull:

| Field | Notes |
|---|---|
| `source` | Gmail message/thread id or permalink, so the entry is traceable |
| `vendor` | Biller name as printed |
| `category` | One of: `utility-dewa`, `utility-municipality`, `utility-cooling`, `utility-gas`, `connectivity`, `cleaning`, `repairs-maintenance`, `guest-experience`, `other` |
| `invoice_no` | Vendor's invoice/reference number |
| `invoice_date` | Document date (YYYY-MM-DD) |
| `period_start`,`period_end` | Service/consumption period if shown (utilities usually show it) |
| `premise_ref` | Premise/account/meter no (DEWA premise, cooling account, SIM/line) — the key to map to a unit |
| `unit_id` | Silkhaus unit, if identifiable (else leave blank → flag) |
| `landlord` | Landlord/owner of the unit, if known |
| `unit_type` | `lease` / `revshare` / `unknown` — drives recoverability |
| `currency` | Usually AED |
| `gross` | Total payable incl. VAT |
| `vat` | VAT amount if shown |
| `net` | Pre-VAT amount if shown |
| `vat_treatment` | `standard` (UAE VAT-registered vendor), `rcm` (international vendor — reverse charge), `none`, or `unknown` |
| `recoverable` | `Y` / `N` / `unknown` — see the decision tree in Stage 2 |
| `notes` | Anything that affects the posting (e.g. "service failure — clean missed", "landlord owns deposit") |

**Mapping premise → unit → unit_type is the crux.** Invoices identify a *premise* (a DEWA premise
number, a cooling account, a phone line), not a Silkhaus unit. To set `unit_id`, `landlord` and
`unit_type` you need a unit master that maps premise refs to units. If the user has one (a CSV, a
NetSuite export, or a tab in the dashboard), ask for it and use it. If not, fill what you can,
leave the rest blank, and flag the unmapped invoices — never invent a unit.

### 1c. Save the register
Append rows to an invoice-master CSV (default: `invoice_master.csv` in the working directory; ask
if the user wants another path). Use the header in `assets/invoice_master_template.csv`. Appending
(not overwriting) lets the master grow across runs; de-duplicate on `vendor`+`invoice_no`.

Show the user the rows you added as a quick table and ask them to confirm/fix `unit_type` and
`recoverable` for anything you marked `unknown` before moving to Stage 2.

---

## Stage 2 — Generate the journal entries

Goal: turn invoice-master rows into a **balanced, reviewable JE table** using the f7 rules.

### 2a. Classify each invoice — recoverable vs Silkhaus-borne
This is the central control in f7. The test is simply: **is the cost charged to the landlord?**

```
Is the category CLEANING?
  └─ YES → Silkhaus-borne, ALWAYS. Unit Cleaning Expenses (620013).
           (Silkhaus keeps the cleaning revenue recognised at booking, so it bears the cleaning cost.
            Never recharge the landlord.)
  └─ NO ↓

Is it GUEST-EXPERIENCE / service failure / make-good (e.g. clean missed, apology)?
  └─ YES → Silkhaus-borne. Guest Experience Expenses (620011) or Apology/Booking Refund (630061).
  └─ NO ↓

Is the unit LEASE?
  └─ YES → Silkhaus-borne by definition → the specific P&L expense account for the category.
  └─ NO (rev-share) ↓

Is this rev-share cost recharged to the landlord per policy?  (default for utilities & R&M = YES)
  └─ YES → RECOVERABLE → Landlord Receivable (Utilities 120060 / R&M 120059), recovered at f8 settlement.
  └─ NO  → Silkhaus-borne → the specific P&L expense account for the category.
```

If `unit_type` or the recharge policy is `unknown`, post the **default** (rev-share + recharge for
utilities/R&M; Silkhaus-borne for cleaning/guest-experience) and add a Review flag.

### 2b. Apply VAT / RCM on the purchase
- **`standard`** (UAE VAT-registered vendor): split the gross — debit the expense/receivable at the
  **net**, debit **Input VAT (110038)** at 5% of net, credit **Accounts Payable (110001)** at gross.
- **`rcm`** (international vendor — Guesty, Airbnb, Stripe and similar): book the expense at the bill
  amount, then self-account the reverse charge — debit **Input VAT (110038)**, credit **Output VAT
  (110040)** at 5% (net VAT nil), credit **A/P (110001)** for the bill.
- **`none` / `unknown`**: post at gross with no VAT line and add a Review flag.

For **recoverable** costs the cost is booked **net** to the landlord receivable; Silkhaus still
claims the input VAT, and **output VAT on the recharge is raised at settlement (f8)** — note this in
the entry rather than adding an output-VAT line here. (Flag if unsure — recharge VAT mechanics are a
controller call.)

### 2c. Build and validate the entries
Use the bundled script — it embeds the GL map, applies the account selection, does the VAT math, and
**proves each entry balances** so you don't post a one-sided journal by hand:

```bash
python3 scripts/build_je.py --in invoice_master.csv --out je_review.md
# or pass a single classified invoice as JSON:
python3 scripts/build_je.py --json '{"vendor":"DEWA","category":"utility-dewa","unit_type":"revshare","recoverable":"Y","vat_treatment":"standard","gross":1050,"invoice_no":"D-1","invoice_date":"2026-05-31"}'
```

The script reads the same `references/posting_rules.md` account map, emits the reviewable markdown
table, and exits non-zero if any entry fails to balance. Read `scripts/build_je.py` if you need to
extend the category→account mapping.

### 2d. Present the reviewable JE table
ALWAYS use this structure so the controller can scan and sign off:

```
## Property-cost journal entries — <period>

### <vendor> · <invoice_no> · <category> · <unit_id or premise> — <recoverable|Silkhaus-borne>
| # | Dr/Cr | Account (code) | Amount (AED) | Narration |
|---|-------|----------------|-------------:|-----------|
| 1 | Dr | Landlord Receivable — Utilities (120060) | 1,000.00 | DEWA <period> — recoverable, unit <id> |
| 2 | Dr | VAT on Purchases AE (110038)            |    50.00 | Input VAT 5% |
| 3 | Cr | Accounts Payable (110001)               | 1,050.00 | DEWA invoice <no> |
**Balanced:** Dr 1,050.00 = Cr 1,050.00 ✓

### Totals
| Account | Dr | Cr |
... (rolled-up totals across all invoices) ...

### Review flags
- <invoice> — unit not mapped (no premise→unit match); posted as <default>, confirm unit & recoverability.
- <invoice> — vendor may be international; assumed RCM, confirm.
```

Rules for the table:
- Show the GL **name and code** on every line; amounts to 2 dp; thousands separators.
- One sub-table per invoice, then a rolled-up **Totals** block, then **Review flags**.
- Never omit the balance line — it's the cheap proof the entry is postable.
- Do not include the "pay the vendor" entry (DR 110001 / CR bank 120023) unless the user asks —
  f7 books the cost to A/P; payment is a separate step.

---

## Worked examples (the four shapes)

See `references/posting_rules.md` for the full account list and more examples. The four shapes:

**1. Recoverable utility (rev-share, standard VAT)** — DEWA AED 1,050 gross on a rev-share unit:
Dr Landlord Receivable — Utilities (120060) 1,000 · Dr Input VAT (110038) 50 · Cr A/P (110001) 1,050.

**2. Silkhaus-borne utility (lease unit)** — same bill on a lease unit:
Dr DEWA Consumption (640004) 1,000 · Dr Input VAT (110038) 50 · Cr A/P (110001) 1,050.

**3. Cleaning (always Silkhaus-borne)** — cleaning vendor AED 315 gross:
Dr Unit Cleaning Expenses (620013) 300 · Dr Input VAT (110038) 15 · Cr A/P (110001) 315.

**4. Recoverable R&M (rev-share)** — AC repair AED 525 gross on a rev-share unit:
Dr Landlord Receivable — R&M (120059) 500 · Dr Input VAT (110038) 25 · Cr A/P (110001) 525.
*(Note: output VAT on the landlord recharge is raised at settlement, f8.)*

---

## When to stop and ask
- The period or vendor list is ambiguous → confirm before scanning.
- An invoice can't be mapped to a unit, or lease/rev-share is unknown → post the default and flag;
  ask the user to supply/confirm a premise→unit master if many are unmapped.
- A cost doesn't fit a known category, or the VAT treatment is unclear → flag, don't guess.
- The user asks to actually post to NetSuite, send email, or label/modify messages → that's an
  action outside this skill's read-and-draft remit; surface it and let the user do it.
