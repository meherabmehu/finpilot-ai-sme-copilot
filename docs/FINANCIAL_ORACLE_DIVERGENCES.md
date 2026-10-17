# Financial oracle divergences and adjudications

Classification: **A** confirmed application defect; **B** benchmark/reporting defect; **C** defensible
convention or representation; **D** unresolved policy ambiguity; **E** unsupported/exposure/backend.
No expectation, oracle, scoring weight or source scenario was changed. Provisional mixed findings
remain mixed in the machine-readable `evaluation/final/divergences.json`.

## Eighteen conventions

| IDs | Assessment against current services |
|---|---|
| C1, C2, C8 | Paid-only cash, inclusive opening/as-of window, transfers neutral: preserved. |
| C3, C4 | Future dated events inside horizon, including paid rows dated after as-of: preserved. |
| C5 | Undated pending blocks: preserved, A explanation improved to name missing input. |
| C6, C7 | Overdue receipts not presumed collected; overdue payments stress tomorrow: preserved. App question analysis calls due-today receipts not yet overdue (C boundary distinction). |
| C9 | Linked recurring invoice occurrence suppression: preserved; actual suppression count now exposed. |
| C10–C14 | Closing collection-first vs payment-first intraday risk, earliest minimum, reserve-gap, first shortfall/reserve breach: preserved. |
| C15 | Existing Decimal/half-up monetary arithmetic retained. SQLite extreme cents are not exact (E); PostgreSQL benchmark verified EDGE-008 without coercing amounts. |
| C16 | Accrual/earned operating totals include pending earned amounts; observed cash includes paid only. Do not delete valid receivables to force cash-basis revenue. |
| C17 | Incomplete/unknown/currency/capacity blocks retained; actual reasons surfaced. Capacity limits remain bounded, no silently expanded limits to chase score. |
| C18 | A: explicit category-token recognition now protects Salaries & Wages/pay-run labels; shared debt-service aliases improve diagnosis/health. Employer on-cost ambiguity remains D. |

## Fixed, not merely adapted

- **A — payroll protection:** before fix PAIR-17-B had no payroll event under the application's
  exact-string classification, so its authored selector could not resolve. Independent tests now
  show neither shifting nor reducing a `Salaries & Wages` obligation is feasible while payroll is
  protected. PAIR-17-A/B actual feasible sets are equal after fix; no arbitrary recommendation flip.
- **A — debt vocabulary:** `Loan instalment` and related explicit categories now count as debt
  service in both near-term diagnosis and horizon burden. No lender/approval/affordability inferred.
- **A — horizon transparency:** dated commitments outside the horizon and the next recurring
  occurrence are surfaced, not added to projected cash. Example independent regression: 27,500 on
  day 31 is excluded from 30-day ending cash 1,000 but explicitly disclosed. Output detail bounded
  to 20 explanatory entries while structured state retains the count/list.
- **A — blocking clarity:** unknown opening cash, missing dates, unconfirmed completeness, currency
  and capacity failures now identify actual blockers. Unknown stays None, not zero.

## Accepted or unresolved, not “fixed” for score

- **C — fingerprint:** benchmark hashes its portable case structure; app hashes a richer snapshot
  with synthetic UUID and explanations. Their SHA-256 bytes should not be equal. Tests check app
  stability/change detection; no expected hash is returned as the application hash.
- **C — alternatives:** app can compare explicitly hypothetical overdue recovery plans that are
  absent from the benchmark's suggested-plan universe. A different name is not automatically bad
  advice. Customer agreement and actual receipt remain unknown.
- **C/E — financing:** scalar normalization uses the first supplied illustration, explicitly exposes
  principal/rate/months, and calls actual `financing_assessment`. Missing hypothetical gap loans
  are not manufactured. Horizon repayment vs lifetime repayment remains a documented adapter
  mapping divergence; no amortization formula change is justified.
- **B/C — violation strings:** first-40-character comparison can report “not reported” even when
  actual violation wording and infeasible classification are present. Raw outputs retained.
- **B — expected-only upstream tables / unscored lifecycle:** separate actual-output checks added,
  original score left untouched. 83 literal lifecycle assertions include 7 rejection-text mismatches.
- **D — on-costs/unclear category labels:** employer pension/NI/401(k) match are not inferred payroll.
  No automatic policy change; owners should explicitly categorize or mark critical where needed.
- **E — exposure gaps:** some policy aggregates, split details, duplicate diagnostics and growth
  ratios remain absent. Neither expectation echoing nor a parallel oracle-shaped engine was added.

## Compatibility / deployment impact

No migrations, new production dependency, database column, primary page or background process.
Snapshot fields are additive; existing reports tolerate old dictionaries. New classification and
explanations change fingerprints: old pending decisions may require reinvestigation rather than
accepting against obsolete semantics. Saved historical snapshots/audit trails are not rewritten.
An ordinary push might trigger the existing webhook; no deployment, environment modification or
production seeding was performed, and remote delivery is blocked until secure authentication exists.
