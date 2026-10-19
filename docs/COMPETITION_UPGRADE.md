# Competition upgrade working matrix

Historical delivery snapshot. See [final competition verification](FINAL_COMPETITION_VERIFICATION.md)
for current Groq activation, audit fixes, measured forecast limitations and release evidence.

Baseline: clean `feat/finpilot-platform`, local and fetched remote `f212d0923a30bc32426a4cd5560e5b9128845d95`. Django 5.2, PostgreSQL/SQLite development, server templates, locally hosted CSS/JS, Decimal engine, Render Docker and Vercel deployments. Existing snapshots, users and ledger records are preserved.

## Executive delivery

The existing five-page product and six Planning tabs remain. This upgrade connects
source consistency, business-aware payment assessment, question-specific grounded
answers, explicit invoice recovery, bounded combined alternatives, forecast method
evaluation, public financing discovery, deadline tasks and genuine exports. Ledger
cash remains Decimal-based; simulation, owner statements and historical decisions
remain distinct from actual settlement. No payment, notification or loan execution
was added.

## Completion and verification matrix

| Requirement | Implementation / files | Final status and evidence |
|---|---|---|
| Source consistency | `financial_state.py`, `access.py`: same-business transactional lock, source revision, profile/collection context fingerprint, writer-side Watchtower refresh including imports | Implemented and tested; source edit, import, void, freshness and concurrency tests |
| Historical/current explanation | `freshness.py`, issue/investigation/roadmap templates: original versus current date, cash, gap, latest recorded change and Needs Review | Implemented and tested; original snapshots retained, browser detects explicit new receipt |
| Industry reasoning | `business_domain.py`: all seven existing types, country/currency, category-linked evidence, operational questions, owner context | Implemented and tested; Retail inventory and Restaurant food/payroll guidance differs; no inferred contractual facts |
| Payment urgency/criticality | `assess_payment`, priorities UI, protection checkbox help: explicit policy versus preliminary suggestion, unknown impact, due/overdue urgency, total/protected/other obligations | Implemented and tested; protected payments never automatically reclassified |
| xAI provider | `advisor.py`, `ai_grounding.py`, settings, `check_ai_provider`: compatible structured chat API, typed scope/evidence selection, safe endpoint, time/output bounds, cache/circuit fallback | Implemented, externally unverified; no owner Grok key supplied, so no real Grok call or API latency claim |
| Question relevance | Deterministic intent, financial follow-ups, model classification of ambiguous scope when configured, narrow collection answers, date-specific evidence, sales sensitivity, payment assessment | Implemented and tested; unrelated questions refused before financial state generation |
| Grounding/security | Model may select only server-authored evidence/action/question IDs; unsupported prose, fabricated IDs and executable actions rejected; legacy free-form adapter restricted to reproducible clauses | Implemented and tested with mocked provider, malicious record text, rate limits, disabled provider and concurrent data changes |
| Cash runway | Existing positive-net-burn behavior retained; reserve coverage and explicit 20% outflow sensitivity added | Implemented and tested; 120-day known answer, zero burn unknown, financing excluded from burn |
| Invoice recovery | `recovery_solver.py`, Recovery formset and scenario UI: explicit amount/date, multiple overdue invoices, authorized references, no duplicate future receipt | Implemented and tested; 3,990 baseline gap, 390 residual in the supplied synthetic example |
| Combined solver | Up to 8 candidate actions, largest 4 overdue receipts, subsets up to 3 actions, max 64 evaluations, original hard constraints and ranking | Implemented and tested; two receipts can solve a gap no single receipt solves; unresolved gaps remain explicit |
| Target reserve | Optional hypothetical target; target questions identified; policy changes never silent; transfer/acceptance requires explicit preferences when target differs | Implemented and tested; not a policy override or global optimization claim |
| Scenario/Decision integration | Recovery snapshots saved in Scenario and transferred into new immutable Decision Lab evidence | Implemented and tested; acceptance and task progress do not settle invoices |
| Forecast candidates | `forecasting.py`: preserved moving average, last-week naive, exponential smoothing, weekday model; nested training-only selection with minimum 5% improvement gate | Implemented and tested; no forced complexity or trained-ML claim |
| Horizon evaluation | 7/15/30/90 days, outer folds, inner selection, MAE/net WAPE denominators, undefined/unstable cases, lowest date and separate dated-only versus operating assumptions | Implemented and tested; reproducible fixed-cutoff synthetic comparison below |
| Public loan discovery | `loan_catalog.py`, official links/dates, country/currency/amount/term/purpose checks, quotation state, original custom calculator | Implemented and tested; public page facts verified, actual customer quotation/eligibility externally unverified |
| Loan source refresh | `check_loan_catalog --file` validates a reviewed JSON catalog; `--live` checks official URL response without silently updating content verification | Implemented and tested; continuous ingestion/scheduler not implemented; manual review required |
| Debt suitability | Preserved reducing-balance schedule, policy/capacity warnings, +2-point sensitivity, fees and no-loan entry | Implemented and tested; no approval/underwriting claim |
| Deadline roadmap | Immediate review, recorded payment dates, pre-deadline check, final outcome review, owner targets/responsible/status, late task flags, current gap/fingerprint | Implemented and tested; manual monitor includes deadline diagnostics, automatic alerts inactive |
| Optional receivable context | New `CollectionContext` and migration `0005`: owner alias, follow-up/dispute, promised date, reported partial amount, confirmation reference | Implemented and tested; these fields never change cash or prove settlement; original ledger fields preserved |
| My Business audit | Existing import preview/idempotency/atomicity/security retained; all transaction types/status/due/reference/category search, progressive context, category quality suggestions | Implemented and tested; suggestions never rewrite categories without owner editing |
| Reports audit | Fingerprint/type/completeness metadata, currency warnings, aging, recovery snapshots, deadline roadmap/outcomes, optional separate interpretation | Implemented and tested; genuine PDF/CSV/XLSX parsed, 2,000-row CSV and formula protection tested; oversized export rejected without partial file |
| Responsive/accessibility | Teal/white visual style preserved, mobile badges/buttons wrap, readable record tables, progressive loan/forecast detail | Implemented and tested; browser results below; automated audits are not full screen-reader certification |
| Benchmark | Original licensed input, oracle, adapter and scoring unchanged | Implemented and tested; 172 executed, 157 passed, 15 partial, 0 failed/blocked, score 0.924161 |

## Grok setup and provider boundaries

The owner API key is **not present**. Production and local calculations work without
it. There is no browser form for platform credentials, no database secret field, and
no provider key in messages, screenshots, report output or committed source.

Locally, put these in the ignored root `.env` and restart the Django process:

```dotenv
XAI_API_KEY=<owner key, stored locally only>
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=<model accessible to the owner account>
XAI_TIMEOUT_SECONDS=30
XAI_MAX_OUTPUT_TOKENS=1800
XAI_TEMPERATURE=0.2
FINPILOT_AI_ENABLED=true
FINPILOT_AI_PROVIDER=xai
FINPILOT_AI_FALLBACK_ENABLED=true
```

The official [structured-output documentation](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
currently demonstrates `grok-4.7` with compatible chat structured output. Do not assume
the owner account has access. Configure an accessible documented model explicitly;
the application does not invent/default a model ID. `auto` is the backward-compatible
provider default for older installations; explicit `xai` never falls through to an
old LLM credential.

```powershell
$env:DEBUG='true'
.\.venv\Scripts\python manage.py check_ai_provider
.\.venv\Scripts\python manage.py check_ai_provider --live
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

`--live` queries the official model list only when securely configured; it sends no
financial data. Successful model discovery is not proof that every inference call
will succeed. Actual Grok response testing remains externally unverified until a key
is configured. Mocked tests exercise the transport, schemas, 401/429/500 fallback,
unknown references, unsupported prose/actions, cache freshness, changed data,
ambiguous scope and prompt injection. They do not measure real Grok accuracy or latency.

For Render, use [this service's Environment page](https://dashboard.render.com/web/srv-dbagh9ijnfac73fkm23g/env),
set the same variables, then save/redeploy. For Vercel, use Project Settings >
Environment Variables > Production, then redeploy. Keep `DEBUG=false` in hosting.
Never copy `LIVE_LOGIN_PASSWORD`/`DEMO_PASSWORD` into client code or platform AI fields.

Grok selects and orders evidence and focused follow-up questions. Financial clauses
are rendered from validated server-owned text, not unrestricted model prose. This is
deliberately narrower than free-form AI advice: an accepted evidence ID cannot invent
a bank offer, amount, execution or customer motive. The same server entry point retains
allowlisted legacy tools for compatibility. No model response executes a tool that
changes data. Ambiguous scope classification is limited to eight seconds; a financial
selection call uses the configured maximum of forty seconds, with no unbounded retry.
Provider circuit/cache are process-local; multi-instance distributed coordination is
not claimed. Histories are user/business scoped and bounded to recent owner questions.

## Known-answer financial validation

| Example | Independently checked result |
|---|---|
| Recorded cash | Pending invoices do not change paid cash; paid loan proceeds affect cash but not operating revenue; transfers have zero net business cash effect; voided rows are excluded |
| Supplied reserve example | 71,010 - 5,400 + 400 = 66,010; reserve 70,000 gives 3,990 gap |
| Explicit overdue recovery | Add a new assumed 3,600 recovery once: 69,610 ending cash, 390 residual; the upcoming 400 is already in baseline |
| Combined solution | Cash 1,000, protected payable 1,200, reserve 500: two separate 400 overdue recoveries leave cash 600 and close the gap; one alone cannot |
| Runway | Opening 30,000 less 6,000 paid expenses = 24,000; 200/day historical burn gives 120 days. Explicit 20% outflow growth gives 100 days. Not a failure-date forecast |
| Custom loan | 10,000 principal, 12% nominal annual, 12 months, upfront fee 200: monthly 888.49, interest 661.86, total including fees 10,861.86. These are entered assumptions, not published bank rates |
| Outcomes | Owner-reported task/partial receipt does not settle the ledger. A separate synthetic paid entry changes current cash/fingerprint and triggers Needs Review; final expected/actual reconciliation still obeys the fixed review date |

### Forecast comparison

`seed_competition_demo` creates 500 days of **synthetic** Retail and Restaurant paid
operating data. The comparison cutoff is fixed at opening date +499 days, before
interactive demo receipts. All methods use the same inputs and outer folds. Selection
uses only earlier inner data. The artificial fixture has a repeating weekday pattern;
zero measured adaptive error here is expected and **not real-world forecast accuracy**.

| Synthetic history | Horizon | Outer folds | Previous moving-average MAE / WAPE | Adaptive MAE / WAPE |
|---|---:|---:|---:|---:|
| Retail | 7 | 4 | 0.56 / 0.46% | 0.00 / 0.00% |
| Retail | 15 | 4 | 4.58 / 1.78% | 0.00 / 0.00% |
| Retail | 30 | 4 | 8.33 / 1.63% | 0.00 / 0.00% |
| Retail | 90 | 4 | 2.50 / 0.16% | 0.00 / 0.00% |
| Restaurant | 7 | 4 | 18.33 / 7.33% | 0.00 / 0.00% |
| Restaurant | 15 | 4 | 151.25 / 27.63% | 0.00 / 0.00% |
| Restaurant | 30 | 4 | 275.00 / 27.16% | 0.00 / 0.00% |
| Restaurant | 90 | 4 | 82.50 / 2.58% | 0.00 / 0.00% |

MAE is absolute error of the horizon's operating **net** movement; WAPE divides the
sum of absolute errors by the sum of absolute actual horizon net movements. Near-zero
net denominators are flagged. Sparse histories retain the original baseline. Current
pending schedules are not replayed backwards as if historically known. Dated invoice
overlays remain separate from the evaluated operating component; historical pattern
overlap with unlinked commitments remains uncertain. Long seasonal cycles and a trained
ML forecaster are **not implemented**; available real owner history has not been used
to claim an improvement over the earlier observed 76.09% demo value.

## Verified public financing coverage

Reviewed 19 October 2026. These are public product/program descriptions, **not customer
offers or verified eligibility**. No current numeric annual rate or fee was safely
confirmed for these records, so quotation-required states appear instead of invented
prices. Rates, fees, maturity, guarantees and affordability require lender review.

| Market | Source | Verified scope / limit |
|---|---|---|
| Bangladesh / BDT | [BRAC Bank Anonno](https://www.bracbank.com/en/sme/loan/anonno) | Working capital/fixed assets; published 500,000–5,000,000 BDT, up to 48 months; complete pricing/eligibility requires quotation |
| USA / USD | [SBA 7(a)](https://www.sba.gov/loans/7a-loans/) | Participating-lender program, maximum 5,000,000 USD; US small-business and repayment assessment required |
| UK / GBP | [Growth Guarantee Scheme](https://www.british-business-bank.co.uk/finance-options/debt-finance/growth-guarantee-scheme) | Accredited-lender scheme, generally up to 2,000,000 GBP; regional/subsidy limits and announced versus operational terms need confirmation |

Catalog verification expires after 90 days. `check_loan_catalog --file reviewed.json`
validates a proposed source file; `--live` checks URL status without advancing review
dates or following arbitrary redirects. An operator must read the page, verify terms,
review the diff and update the version-controlled catalog. Other supported business
countries keep the custom quoted-term calculator and an explicit no-verified-coverage
state. No scraping/scheduler or third-party outreach is silently enabled.

## My Business and Reports audit

Existing model/form validation, scoped accounts, paid/pending meaning, recurring
invoice links, preview/atomic import, duplicate fingerprints, mapping, malicious
spreadsheet handling and void audit trails were reviewed and retained. Existing
CSV/XLSX import regression tests remain. Search now covers references and categories,
all eight types, payment status and due filters. Optional alias/follow-up data is
progressive. Ambiguous categories prompt correction; neither categories nor criticality
are silently rewritten.

The new migration creates one optional context table; no transaction values, users,
opening balances or decision snapshots are migrated, reset or seeded. Reported partial
amount is explicitly an owner statement, **not a partial-settlement engine**. Actual
paid movements and the remaining invoice must still be reconciled by the owner.

All existing report routes remain. Recovery snapshots, roadmap tasks/deadlines/current
versus expected status, source fingerprint, completeness/currency warning and invoice
aging were added to the existing writers. PDF bytes are parsed with pypdf, XLSX with
openpyxl, and CSV numeric/content checks cover the new scenario. Spreadsheet formula
protection remains. A 2,000-row genuine CSV is tested; source exports above 20,000 rows
and scenario reports above 500 snapshots are rejected with explicit guidance instead
of silently returning partial content. Optional executive interpretation is requested
explicitly and separated from deterministic export figures; no automatic provider call
is made for every download.

## Actual validation and reproduction

Full local application suites: **SQLite 264 passed, 2 PostgreSQL-only skips**;
**PostgreSQL 266 passed**. Ruff, Django checks, schema dry-run, template compilation,
asset build and collectstatic passed. Final configuration-focused checks are recorded
in `test-results/competition-targeted.xml`. These are local synthetic results.

Browser evidence: existing workflow **147 viewport checks, 21 real exports, 18 axe
audits**; new competition workflow **32 viewport checks, 3 roadmap export formats,
16 axe audits**. No page errors, overflow or automated WCAG violations. Onboarding,
entry, import, scope refusal, recovery calculation/save/transfer, acceptance, task
progress, actual-record immutability, custom loan arithmetic, Restaurant explanation,
explicit new paid receipt and stale evidence were exercised. Screenshots were reviewed.
Automated checks and keyboard smoke tests are not complete assistive-technology proof.

The original 172-case benchmark was rerun on a disposable PostgreSQL database, with
original source hashes/oracle/scoring intact: **157 passed, 15 partial, 0 failed,
0 blocked; weighted score 0.924161**. Previous release: 147 passed, 25 partial,
0 failed/blocked, 0.917476. Arithmetic dimensions did not improve merely through prose;
clearer intent and mandatory dated-only planning/counterparty disclosures explain the
measured change. The remaining partials include absent diagnostic/financing information
and stricter benchmark requirements; no missing lender terms are invented to gain
credit. This is not LLM accuracy or a production reliability measurement.

```powershell
$env:DEBUG='true'
.\.venv\Scripts\python manage.py migrate --noinput
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py makemigrations --check --dry-run
.\.venv\Scripts\python -m ruff check .
npm.cmd run build
.\.venv\Scripts\python manage.py collectstatic --noinput
.\.venv\Scripts\python -m pytest -q --basetemp=test-results/new-unique-test-temp
# For the full PostgreSQL suite, use only the explicitly disposable local test DB.
# Never set a production DATABASE_URL for pytest or synthetic demo commands.
.\.venv\Scripts\python manage.py seed_competition_demo
.\.venv\Scripts\python -m scripts.evaluate_competition_forecasts
.\.venv\Scripts\python -m scripts.browser_survival
.\.venv\Scripts\python -m scripts.browser_competition
```

PostgreSQL test cluster: marked local `test-results/survival-pg`, loopback port 57543.
Benchmark command: `FINPILOT_EVAL_DJANGO=1 python -m evaluation.agentic.run
--benchmark-root test-results/benchmark-input/FinPilot-Agentic-Evaluation --adapter django
--suite full --out-dir test-results/competition-evaluation-postgres-release
--postgres-socket test-results/survival-pg --postgres-port 57543`.

Ignored local artifacts include `competition-sqlite.xml`, `competition-postgres.xml`,
`competition-forecasts.json`, `competition-browser/verification.json`,
`survival/verification.json`, and `competition-evaluation-postgres-release/`.
They contain synthetic evidence and are not bundled with production.

## Competition demonstration

1. Run `seed_competition_demo` locally with `DEBUG=true` and the existing local
   `DEMO_PASSWORD`. It refuses hosted settings and never resets existing businesses.
2. Log in as `competition@finpilot.local` with that local demo password. Every
   business and record created by the command is explicitly synthetic.
3. Select Competition Synthetic Retail. Explain paid cash, protected inventory bill,
   reserve and overdue invoices. Browser exercises may add clearly labeled synthetic
   receipts later, so the current cash can legitimately differ from the original example.
4. Ask how much is overdue, then ask which payment to prioritize. Show the different
   evidence, preliminary criticality and unknown supplier dependency. Ask a football
   question to demonstrate scope refusal.
5. In Scenario Simulation, choose an overdue invoice, partial/full amount and explicit
   assumed future date. Review baseline versus recovery gap, upcoming receipts included
   once, and bounded combined alternatives. Show unresolved and feasible cases.
6. Transfer a compatible scenario into Decision Lab, inspect dependencies, accept a
   feasible action set, then open Roadmap. Show immediate review, pre-deadline check,
   payment deadline and separate final outcome review. Mark owner-reported progress.
7. Add an explicitly synthetic paid entry separately in My Business. Refresh Dashboard,
   Watchtower and the historical investigation; show the Needs Review explanation.
8. Compare no-loan alternatives with Loan Discovery and the custom actual-quote
   calculator. Never present sample inputs as a bank rate or an approved offer.
9. Download PDF/CSV/XLSX scenario/survival/roadmap reports. Show current versus archived
   evidence and genuine file content.
10. Switch to Competition Synthetic Restaurant. Ask about a 20% sales reduction;
    inspect food/payroll dependency questions, explicit revenue sensitivity, forecast
    horizons and method evaluation. Weekly synthetic seasonality is not assumed for
    every restaurant.

## Release and known limits

Branch stays `feat/finpilot-platform`. The final commit SHA, successful push and actual
hosting deploy status are reported in the final handoff after verification. Existing
Render and Vercel automatic deploys use the same source. Render hosts frontend/Django;
the existing shared Neon database is retained. Migration `0005_collection_owner_context`
must run before new code serves requests; existing startup/build migration commands
handle it. No production test fixtures, owner credential changes or platform key
changes are required. Production smoke checks use existing login and read-only pages.

Real Grok inference/latency is externally blocked by the missing owner key. Personalized
lender eligibility, negotiated rates and bank data remain externally unverified.
Continuous source ingestion, automated alerts, trained ML, calibrated probabilities,
verified customer identity and automatic partial-settlement matching are not claimed.
Owner confirmation is not payment proof. Free Render services may sleep. New snapshots
can flag older proposals stale because provenance changed; accepted history is retained.
