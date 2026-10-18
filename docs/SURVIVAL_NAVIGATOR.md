# Financial Survival Navigator delivery

The existing five-page Django portal now presents recorded cash, risks and recovery
decisions with one shared navy/white/blue interface. No framework, database records,
financial policies or original financial formulas were replaced.

## Page and implementation map

| Page | Primary experience | Preserved details |
|---|---|---|
| Dashboard | One justified risk, available cash, unpaid receivables, dated payments, reserve, one dated-only chart, up to three next steps | Watchtower, monitoring freshness, actual transactions, operating performance and evidence through disclosures |
| My Business | Business profile, Financial rules, Data & accounts | Existing edit/save, transaction create/edit/void, sales/expenses, recurring commitments, import preview/confirmation/history and manually managed accounts |
| AI Advisor | Clean conversation, suggested questions, provider status, cash context and recovery entry | Business/user-scoped history, deterministic fallback, configured provider adapter, full answers and saved evidence |
| Survival Decision Lab | Problem → Options → Simulation → Comparison → Plan | Original `/planning/` and investigation URLs, historical snapshots, scenario builder, forecasts, financing calculator, modification, acceptance/rejection, review, lifecycle and exports |
| Reports | Five working report rows with PDF, Excel and CSV | All earlier report formats/types remain available under advanced exports |

The shared shell uses self-hosted variable Inter, a 24–28px heading scale, 14–16px
body/control text, tabular numerals, minimum 44px controls, visible focus, semantic
navigation and a phone bottom bar. Bengali falls back to installed Nirmala UI/system
fonts; this is not a claim of complete Bangla localization. Inter is licensed under
SIL OFL 1.1; its unmodified license accompanies the font in `static/fonts/`.
Font source: https://github.com/google/fonts/tree/main/ofl/inter.

## Financial behavior and boundaries

`apps/portal/intelligence/survival.py` is a read-only presentation/sensitivity service
on authorized snapshots. It reuses the existing Decimal `cash_timeline` and plan
events. It does not change plan rankings, accounting amounts or saved evidence.

Each plan can be tested against earlier receipts (default 3 days), original plan
dates, delayed receipts (default 7 days) and missing collections. Day adjustments
are bounded to 0–30. Earlier dates cannot precede tomorrow. Delayed receipts outside
the review horizon do not fund the horizon; the receivable is still outstanding.
No probabilities or “most likely” outcomes are invented. Payment dates and amounts,
including payroll and critical suppliers, remain unchanged in these sensitivity
tests. Closing cash/reserve gaps and payment-first cash gaps remain distinct.

`build_state` adds receipt-source provenance so loan disbursements are not called
customer collections. This metadata does not change cash arithmetic. Legacy saved
snapshots remain accessible; uncertainty tests require new typed provenance rather
than guessing receipt types. Their original expected/observed outcomes remain stored.
Snapshot fingerprints can mark old proposals stale; start a fresh investigation
before accepting a stale proposal. No historical snapshot is overwritten.

Saved accepted plans take priority in the final recovery step. Selection records
intention only. Customer/supplier agreements, finance approval and actual payments
are separate real-world actions. Monitoring remains deployment/operator scheduled;
manual review does not establish an always-running service.

New `receivables` and `payables` exports query pending, unarchived records belonging
to the authenticated business. Date filters use record date; missing due dates stay
unknown. Payables include payroll and other payments, so the UI says “Supplier &
other payments.” PDF/CSV/XLSX use the original formatting, auditing and spreadsheet
formula-injection protections. No fake report/download categories are displayed.

## Files and schema

- Shared presentation: `static/css/survival.css`, `static/fonts/`, `static/js/app.js`,
  `templates/base.html`, `templates/portal.html`.
- Pages: `templates/dashboard.html`, `business.html`, `advisor.html`, `planning.html`,
  `investigation.html`, `reports.html`; reusable recovery/rules partials in `templates/partials/`.
- Services/integration: `apps/portal/intelligence/survival.py`, `financial_state.py`,
  `apps/portal/views.py`, `forms.py`, `reports.py`.
- Regression checks: `tests/test_survival_navigator.py`, updated workflow test and
  browser scripts, new `scripts/browser_survival.py`.
- Development benchmark: Windows loopback support in `evaluation/agentic/database.py`.
  It verifies the server data directory against an explicitly marked disposable
  local cluster before creating its own randomly named test database.

**No new migrations, environment variables, provider keys, production credentials,
financial-policy changes or infrastructure are required.**

## Measured local validation — 18 October 2026

| Check | Actual result |
|---|---|
| SQLite application suite | 197 passed; 2 PostgreSQL row-lock tests skipped |
| PostgreSQL 16.14 application suite | 199 passed; 0 skipped |
| Full pinned benchmark, actual PostgreSQL Django adapter | 172 executed; 147 passed; 25 partial; 0 failed/blocked; weighted score 0.917476 |
| SQLite benchmark diagnostic | 171 executed; 146 passed; 25 partial; 1 blocked extreme-cent boundary; overall score not reportable |
| New survival browser workflow | 112 viewport/page checks; 15 working export checks; 0 page errors/overflow; financial ledger unchanged |
| Decision browser regression | 63 page/viewport checks; 0 overflow/page errors |
| Existing public/authenticated responsive script | 302 checks across 14 viewport/orientation combinations, including 320–2560px; 0 failures |
| Existing browser smoke script | Desktop/tablet/mobile, five-page navigation and business switching passed |
| axe-core 4.11.1 | 10 main-page audits at 390px/1440px; no automated WCAG 2 A/AA or 2.1 A/AA violations |
| Django check, migration dry-run, Ruff | Passed; no model changes detected |
| Frontend build and collectstatic | Passed |

The benchmark result matches the earlier baseline; visual polish does not establish
better financial predictions. Partials are not passes. The unchanged licensed
benchmark stays outside tracked source, and its pinned SHA-256 is checked before
execution. The Windows development run used an isolated loopback cluster, never a
production URL. No LLM provider, payments or external notification service was used.
Its supplemental checks confirmed all 21 actual policy-pair groups and 83 lifecycle
assertions across 14 lifecycle cases, with no nonwording mismatches or ledger mutations.

Automated accessibility checks do not replace screen-reader/user testing. Axe can
leave canvas/complex visual checks for manual review; screenshots were also inspected.
The application's strict CSP remains enabled; axe is injected by DevTools preload
only for local QA, not shipped to application pages.

## Reproduce

Use the existing `.venv`, project dependencies and a local synthetic database.
Set `DEBUG=true`; keep `DEMO_PASSWORD` in your local environment, not shell history.

```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py makemigrations --check --dry-run
.\.venv\Scripts\python -m pytest -q --basetemp=test-results/pytest-local
.\.venv\Scripts\python -m ruff check .
npm.cmd run build
.\.venv\Scripts\python manage.py collectstatic --noinput
.\.venv\Scripts\python manage.py seed_decision_demo
.\.venv\Scripts\python -m scripts.browser_survival
.\.venv\Scripts\python -m scripts.browser_decisions
```

`browser_survival` serves and shuts down its own local synthetic server. When
`test-results/axe.min.js` contains pinned axe-core 4.11.1, it also runs accessibility
audits. `browser_check` and `responsive_check` use a separately running local server
and the existing `seed_demo` account. See `AGENTIC_EVALUATION_INTEGRATION.md` for the
licensed benchmark. On Windows, `--postgres-socket` names the marked cluster data
directory, and `--postgres-port` must select an available loopback port. Unix behavior
is unchanged. Generated databases are dropped; only the dedicated local cluster is
stopped after testing.

## Screenshots and detailed artifacts

These files are **local ignored artifacts**, all containing synthetic records. They
are deliberately not committed or hosted with production assets.

| Page | Desktop | Mobile |
|---|---|---|
| Dashboard | [1440px](../test-results/survival/dashboard-1440.png) | [390px](../test-results/survival/dashboard-390.png) |
| My Business | [1440px](../test-results/survival/business-1440.png) | [390px](../test-results/survival/business-390.png) |
| AI Advisor | [1440px](../test-results/survival/advisor-1440.png) | [390px](../test-results/survival/advisor-390.png) |
| Survival Lab | [1440px](../test-results/survival/lab-1440.png) | [390px](../test-results/survival/lab-390.png) |
| Reports | [1440px](../test-results/survival/reports-1440.png) | [390px](../test-results/survival/reports-390.png) |

Additional evidence: `test-results/survival/verification.json`,
`test-results/survival-pytest*.xml`, `test-results/decision-responsive.json`,
`test-results/responsive/report.json`, and
`test-results/survival-evaluation-postgres-final/`.

GitHub branch: `feat/finpilot-platform`. Delivery continues on the existing branch;
deployment status and exact pushed commit are verified separately at handoff.
