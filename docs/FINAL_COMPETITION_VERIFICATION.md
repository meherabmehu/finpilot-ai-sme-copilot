# Final competition verification — 19 October 2026

Branch: `feat/finpilot-platform`. Fetch confirmed baseline
`9518d5762556fe4ac98e28f32d850c9abf97c025` matched remote, with no starting changes.
Tested application commit: `85149c0ab7a2616170a03e19889276400a33f576`.
The final handoff identifies any subsequent documentation commit separately.
Existing users, financial records, URLs and immutable decision snapshots were preserved.

## Audit and resulting fixes

| Area | Finding and final status | Evidence |
|---|---|---|
| Groq activation | **Defective → fixed:** Advisor badge ignored Groq although inference worked. Selected-provider readiness now drives it, including disabled-provider behavior. | `test_groq_badge_uses_selected_provider`; browser badge checks; production GET checks |
| Question relevance | **Defective → fixed:** Restaurant expense questions triggered sales material; sales increases were described as decreases; English-only scope rejected some Banglish financial inputs; explicit new loan questions could inherit unrelated collection intent. | 45 audit tests, including independent mandatory questions, language/no-borrowing/date regressions |
| Partial recovery question | **Incomplete → implemented:** Half-receipt follow-ups now compute explicit invoice-level residual cash/gap. Multiple eligible invoices require identification; tomorrow is visibly illustrative, not inferred confirmation. Tiny amounts below currency precision receive guidance. | 3,600 × 50% = 1,800; baseline gap 3,990 → 2,190; ending cash 67,810; upcoming 400 counted once |
| AI synthesis | **Implemented and tested:** Groq can connect cited premises into bounded conditional operational hypotheses and practical actions. Model-generated hypotheses are labeled unconfirmed; numeric/date facts remain server-authored. | Strict schema, unknown references/numeric claims/eligibility/execution rejection; mocked browser; real synthetic Groq synthesis verified |
| Historical/current consistency | **Implemented and tested:** 4,540 historical gap remains immutable when current bill correction gives 3,990. Current source fingerprints include records, policies and owner context. | `test_original_gap_4540_current_3990_remains_historical`; existing edit/void/import/policy/freshness and concurrent-source tests |
| Industry behavior | **Implemented and tested:** All seven business types use actual category-linked evidence and different operational questions; category inference never changes payment protection automatically. | Seven parameterized type/evidence cases and existing payment-criticality tests |
| Debt capacity | **Defective → fixed:** Loan proceeds/repayments polluted historical repayment-capacity cash. Separate paid operating flows now exclude financing. Larger/longer custom quotations retain arithmetic while unsupported cash-impact simulation is explicitly unavailable. | Operating net 20 stays 20 despite 100,000 loan proceeds and 5,000 repayment; long-term quotation regression |
| Combined gap solver | **Implemented and strengthened:** Automatic candidates exclude active disputes and promises beyond the horizon, and do not move a recorded future promise to tomorrow. Explicit owner scenarios remain conditional. | Dispute/promise regression; multiple-recovery, protected-payment, residual-gap, transfer and ledger-immutability tests |
| Forecast | **Defective → fixed:** Candidate baseline denominator could differ from the original engine; advanced overlays left stale adverse/daily-flow fields. Baseline matching and coherent overlays repaired. Added historical validation gate retaining simpler models without stable evidence. | Chronological leakage regression; sparse-history tests; measured noisy experiments below |
| Financing sources | **Implemented and expanded:** Five reviewed public descriptions, purpose restrictions, explicit quotation requirements and pricing basis. No public description becomes an individual offer. | Official sources below; country/currency/amount/term/purpose/freshness tests |
| Roadmap | **Implemented and tested:** Immediate review, supplier deadline and pre-deadline action remain separate from final outcome review; owner task status never proves payment. | Existing deadline, stale-source, accepted-plan and owner-progress/browser checks |
| Reports | **Defective → fixed:** Explicit current-versus-period semantics added; forecast reports identify dated-only versus operating minimum; financing reports include public source references and period-filtered saved quotes. | Genuine PDF/CSV/XLSX parsing, numeric/formula-injection, 2,000-row and business-isolation tests |
| Automated alerts / continuous catalog refresh | **Incomplete, disclosed:** Manual monitoring/source review work. No scheduler, external alert sending or continuous bank ingestion was added. | Roadmap UI and operator commands disclose this limitation |
| Actual partial settlement | **Limited by current data model:** Owner-reported partial amounts do not change cash. Automatic linked invoice/paid-movement settlement matching is not implemented. Do not mark a full invoice paid to represent a partial receipt or count a separately recorded receipt twice. | Context round-trip preserves cash; explicit recovery simulations are not settlement |
| External underwriting / forecast accuracy | **Not externally verified:** Individual eligibility, actual lender quotation, causal operating effects, real-world forecast improvement and calibrated uncertainty require independent evidence. | No fabricated lender rates, numerical AI claims or zero-WAPE accuracy claims |

## Groq: actual evidence and boundaries

Local Django reads `FINPILOT_AI_PROVIDER=groq`, the official
`https://api.groq.com/openai/v1` endpoint and `openai/gpt-oss-20b`. Key presence was
checked without returning its value. Offline configuration and real `/models`
availability checks passed. A strict-schema synthetic inference returned HTTP 200:
496 prompt + 74 completion = 570 tokens, observed request latency 560 ms.
A separate real request using only the marked local synthetic competition workspace
validated conditional synthesis in 1,053 ms and left its financial fingerprint unchanged.
These are individual observations, not a latency, quota or model-quality guarantee.

`check_ai_provider --live --inference` reproduces model discovery and one bounded
synthetic inference. It prints safe status/usage only. Transport/model errors use
truthful fallback; 401/429/500, timeout boundaries, disabled setup, cache/circuit,
unsupported output and changed-source handling are tested with mocks. Rate-limit
headers were observed; actual account quota exhaustion was not deliberately induced.
No real owner ledger was used for the synthetic API verification. xAI remains a
separate, unconfigured option; Groq never silently routes to xAI or a legacy key.

The model's new reasoning is a **conditional hypothesis**, not a verified factual
claim. The validator binds source IDs, intent relationships and allowed actions,
rejects numeric/date/approval/execution assertions and requires explicit conditional
uncertainty. It does not prove causal truth of natural language. Financial facts are
still rendered from deterministic evidence. Hypothesis output is currently English;
Bangla/Banglish financial inputs are normalized, not a claim of unrestricted
multilingual financial understanding. Answers lead with relevant evidence and expose
expanded supporting material through the existing disclosure.

## Forecast measurements

[Full measured MAE/WAPE tables](FORECAST_ROBUSTNESS.md) include all five methods,
7/15/30/90-day horizons, fold counts and net denominators. Reproduce with
`DEBUG=true python -m scripts.evaluate_forecast_robustness`.

Six varied 600-day synthetic histories cover stationary noise, noisy weekday effects,
structural change, sparse invoices, near-zero net movement and volatile shocks.
A 40-day history has no valid evaluation folds and undefined metrics. In the 24 valid
dataset/horizon pairs, raw adaptive selection **won 7, lost 9, tied 8** against moving
average. There is no universal accuracy improvement.

Examples: noisy-weekday 30-day MAE 242.01 → 104.25 and WAPE 6.83% → 2.94%; its
7-day raw adaptive MAE worsened 282.22 → 380.86 and WAPE 37.75% → 50.94%.
Deployment retained moving average in 21 of 28 evaluated current selections, including
all near-zero-denominator and short-history cases. Candidate selection needs earlier
training-only folds; the additional deployment gate requires stable historical MAE
improvement of at least 5% across at least three folds. Reused validation is selection
evidence, **not independent performance measurement of that final gate**. The raw
adaptive table is not relabeled as a backtest of the added gate.

Historical schedule statuses are not reconstructed. Missing ledger days are treated
as zero in these experiments and can represent missing records in real use. Dated-only
minimum and estimated operating-plus-schedule minimum have separate assumptions;
an early dip can remain the lowest date across several horizons. No trained ML,
prediction probability, calibrated confidence interval or real-world zero-WAPE claim.

## Decision Lab, source updates and records

Independent known answers remain: 71,010 − 5,400 + 400 = 66,010; a 70,000 reserve gives
3,990 gap. Explicitly collecting the overdue 3,600 gives 69,610 and 390 residual;
the future 400 is never added twice. Half receipt gives 67,810 and 2,190 residual.
Multi-invoice combinations, policy/no-borrowing constraints, scope checks, realistic
counterparty dependencies, scenario transfer and acceptance without ledger execution pass.
Feasibility under assumptions is distinct from satisfying the reserve goal.

Current Dashboard, Watchtower, Advisor, Decision Lab, Forecast, scenario views, Roadmap
and Reports read current scoped source state; historical investigations and accepted
plans keep their original evidence. Existing writer-side refresh covers create/edit/
void, paid-status changes, CSV/XLSX confirmation, profile/policy updates and recurrence
creation/disable. Roadmap progress and reported partial receipt are owner statements,
not paid ledger movements. No new partial-settlement engine or production reset.

## Public lending sources

Reviewed official pages on 19 October 2026:

- [BRAC Bank Anonno](https://www.bracbank.com/en/sme/loan/anonno): Bangladesh/BDT,
  published amount/term bounds; individual pricing and full eligibility require quotation.
- [SBA 7(a)](https://www.sba.gov/loans/7a-loans/): USA/USD, participating-lender program;
  maximum 5 million; lender credit and repayment assessment required.
- [Growth Guarantee Scheme](https://www.british-business-bank.co.uk/finance-options/debt-finance/growth-guarantee-scheme):
  UK/GBP; generally 2 million, regional/subsidy restrictions and lender-specific pricing.
- [SBA Microloan](https://www.sba.gov/loans/microloans/): USA/USD, up to 50,000,
  maximum seven years; published general 8%–13% range is not an individual quotation.
  Existing-debt repayment and real-estate purchase are excluded.
- [SBA 504](https://www.sba.gov/loans/504-loans/): USA/USD fixed assets, published
  10/20/25-year terms; working capital/inventory excluded. The page header says
  5 million while its detailed maximum says 5.5 million; the catalog discloses that
  discrepancy and requires CDC confirmation rather than inventing a uniform limit.

No invented fees, final rate, approval or personal eligibility. Source dates expire
after 90 days. Custom quoted-term calculator and no-loan alternatives remain.

## Final quality gate and artifacts

| Check | Observed result |
|---|---|
| Django checks / schema dry-run | Passed; no migration changes |
| Ruff / diff whitespace / static build | Passed; npm build and collectstatic succeeded |
| SQLite full suite | **318 passed, 2 PostgreSQL-only skips** |
| Disposable PostgreSQL 16 full suite | **320 passed, no skips**; marked loopback cluster stopped afterward |
| Original 172-case benchmark | **157 passed, 15 partial, 0 failed, 0 blocked**, weighted **0.928124**, no critical failures |
| Original browser workflow | 147 viewport checks, 21 exports, 18 axe audits; no errors/overflow/violations |
| Competition browser workflow | 32 viewport checks, 3 roadmap export formats, 16 axe audits; no errors/overflow/violations |
| New Advisor browser workflow | 16 English/Bangla/Banglish questions, 4 widths, 2 axe audits; corrected badge and outside-scope refusal; provider mocked |
| Actual screenshots inspected | Desktop forecast 1440; mobile loans 390; source-linked cards, dates and readable responsive layout |
| Actual Groq | Model list, strict-schema synthetic inference and conditional synthesis succeeded; financial records unchanged |

Artifacts in ignored `test-results/`: `final-audit-sqlite.xml`,
`final-audit-postgres.xml`, `final-audit-benchmark-release/`,
`final-forecast-robustness.json`, `final-groq-synthesis.json`,
`survival/verification.json`, `competition-browser/verification.json`,
`final-advisor-browser/verification.json`, and final production checks below.
Benchmark input hashes, oracle and scoring remain unchanged. Partials are not passes;
this measures deterministic service coverage, not LLM accuracy or model reliability.
Formula injection, numeric PDF/CSV/XLSX parsing and scoped authorization remain in the
full suites. Automated accessibility checks are not a full assistive-technology audit.

## Production and migration evidence

Application release commit: `85149c0ab7a2616170a03e19889276400a33f576`.
Render deploy `dep-dbasjuhsrm7s73aq48c0` reached **live**; Vercel deployment
`dpl_Hc9DYM5X5DQrA9CfbtKXLKxfgeXt` reached **READY** and its production alias was assigned.
Migration execution completed with no pending migration. New approved startup/build
output explicitly shows **`[X] 0005_collection_owner_context`** on both providers;
Render recorded it at `2026-10-19T07:43:49Z`. No schema/financial data reset was required.
Migration proof came from deployment logs without downloading production secrets.

Read-only post-release checks use `scripts/verify_production_readonly.py` and existing
approved authentication: public landing, health, login, static CSS and 12 authorized
pages/tabs. The corrected Groq badge is checked separately from HTTP success.
Results are in `final-production-render.json` and `final-production-vercel.json`.
No production chat, financial, synthetic-fixture or credential mutation is part of
these checks. A documentation-only follow-up does not change the tested application;
the final handoff reports the actual final branch/HEAD and deployment state.

## Competition demo and honest limits

1. Use local marked synthetic businesses with the existing local demo credentials;
   never seed hosted data. Existing demo fixtures are not reset and browser-created
   paid receipts may legitimately change their current balances.
2. Show paid cash, minimum reserve and actual supplier due date. Use that recorded
   date in a question; the separate fixed-date regression verifies October 25.
3. Ask overdue total, supplier priority, restaurant expenses and a sales sensitivity
   independently. Show different evidence and unknown operational dependencies.
4. Ask a half-receipt follow-up. Choose an invoice if several match; confirm the
   hypothetical date and compare remaining gap without recording an actual receipt.
5. Compare no-borrowing and combined recovery alternatives. Active disputes and later
   owner promises are not silently assumed paid tomorrow.
6. Transfer a scenario, accept a conditional plan, update owner task progress and
   show supplier/pre-deadline actions before final review. Acceptance never pays bills.
7. Show 4,540 historical versus 3,990 current-gap regression without overwriting
   original evidence; inspect Needs Review after an explicit source change.
8. Show forecast horizon/date, dated-only versus operating assumptions, noisy MAE/WAPE
   and baseline retention. Do not present the artificial zero-error demo as accuracy.
9. Compare official public sources with an actual-quote calculator; show debt capacity
   excluding loan proceeds and a higher-rate reserve stress. No approval claim.
10. Export real reports and distinguish current projections, historical evidence,
    owner-reported progress and verified paid transactions. Groq hypotheses stay labeled.

Remaining limitations: no automatic alerts or lender ingestion; no verified customer
motives or externally confirmed supplier dependency; no automatic partial-settlement
matching; no universal forecast improvement; no sustained-load quota/latency proof.
No missing raw key blocks Groq now. Personalized underwriting and real-world forecast
validation remain external evidence requirements, not silently completed features.
