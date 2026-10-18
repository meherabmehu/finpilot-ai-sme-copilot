# FinPilot AI

A Django financial copilot for SMEs, built for the 2026 FinTechathon, Topic E. One account can manage independent business workspaces through exactly five primary pages: Dashboard, My Business, AI Advisor, Financial Planning, and Reports.

The [final survival integration](docs/FINAL_POLISH_DELIVERY.md) adds a light teal workspace,
six focused Planning tabs, explainable runway and payment priorities, partial-collection
stress tests, saved scenario exports and owner-reported recovery progress. The earlier
engine, investigations, financial records and decision lifecycle remain intact.

The [Financial Survival Navigator](docs/SURVIVAL_NAVIGATOR.md) connects recorded cash,
financial rules, recovery options, collection uncertainty, saved decisions and outcome
reviews in a responsive interface. The existing `/planning/` URL still provides cash
forecasts, scenario simulation and financing comparisons through secondary tabs.

## Local setup (PowerShell)

Python 3.13 or 3.14 and Node 24 are supported by this checkout. PostgreSQL is required in production. SQLite is an explicit local development fallback.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: use a random SECRET_KEY; set PostgreSQL and SMTP if available.
$env:DEBUG='true'
npm.cmd ci
npm.cmd run build
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py collectstatic --noinput
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. Register, then use the verification link printed in the development server console. In production configure SMTP. The environment's `DEBUG` variable overrides `.env`; set it explicitly when needed.

## Synthetic demonstration

```powershell
$env:DEBUG='true'
$env:DEMO_PASSWORD='Choose-your-own-long-demo-password'
.\.venv\Scripts\python manage.py seed_demo
.\.venv\Scripts\python manage.py monitor_finances
```

Sign in as `demo@finpilot.local` with the password you supplied. Three synthetic businesses contain six months of distinct records. The command is idempotent and disabled when DEBUG is false. Existing demo account passwords are not reset by rerunning it. Never use this seed in production.

## Validation

```powershell
$env:DEBUG='true'
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py makemigrations --check --dry-run
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\ruff check .
.\.venv\Scripts\python -m playwright install chromium
.\.venv\Scripts\python scripts/browser_check.py
.\.venv\Scripts\python scripts/responsive_check.py
```

Browser checks require a running local server, seeded demo, and the same `DEMO_PASSWORD`. They create local-only screenshots under ignored `test-results/`.

The responsive sweep covers all primary pages, business and planning tabs, public/authentication/onboarding screens, open header menus and long values at widths from 320 to 2560px, plus phone landscape orientations. Run a smaller selection with `python scripts/responsive_check.py --widths 320,768,1440`. Layout rules are maintained in `static/css/responsive.css`; wide tables scroll within their own regions, and phone navigation includes safe-area spacing.

## Project layout

- `config/`: settings, URL routing and WSGI.
- `apps/portal/`: normalized models, authorization, forms, views, imports, reports, financial engine, read-only AI adapter and management commands.
- `templates/`: public website, authentication, onboarding and five portal pages.
- `frontend/`, `static/`: locally compiled Tailwind, custom responsive CSS, vanilla JS, vendored Chart.js and HTMX.
- `tests/`: financial known-answer, isolation, permissions, import, auth and export checks.
- `docs/`: architecture, deployment, methodology, security, limitations and presentation guide.

## Configuration-dependent integrations

`LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL` enable an OpenAI-compatible chat-completions API. No API calls or genuine AI claims are made without these settings. This is protocol interoperability, not a universal adapter for every provider's API. SMTP enables external email delivery. No bank API, payment execution, ML training or downloaded trained model is included.

See [deployment](docs/DEPLOYMENT.md), [security](docs/SECURITY.md), [limitations](docs/LIMITATIONS.md), and [testing](docs/TESTING.md). The UI follows the supplied references with a quieter blue/navy palette and responsive layouts.


## Agentic financial decisions

The existing five pages now include a record-backed Watchtower, owner financial preferences, deterministic investigations, constrained counterfactual Decision Lab, saved decision history and expected-versus-actual monitoring. Acceptance records intent only: no payments, collections, lender applications or accounting entries are executed. No model training is required. The optional OpenAI-compatible advisor remains available; no-provider chat provides explicitly deterministic analysis.

See [architecture](docs/AGENTIC_ARCHITECTURE.md), [decision workflow](docs/DECISION_INTELLIGENCE.md), [memory](docs/DECISION_MEMORY.md), [evidence](docs/EVIDENCE_AND_EXPLAINABILITY.md), [synthetic demo](docs/DEMO_GUIDE.md) and [actual progress / blockers](docs/IMPLEMENTATION_PROGRESS.md). Current exports include financial issues, investigation evidence, simulated comparisons, decisions and outcomes.

`python manage.py monitor_finances --business BUSINESS_UUID` refreshes internal issues and reviews decisions. It does not install a scheduler or send notifications. Production scheduler/provider/PostgreSQL verification remains operator-dependent. Collect static assets before running tests against manifest storage.


### Final quality hardening
Repeat imports are explicitly non-mutating; corrected files follow documented append-only event-reference rules. Investigations now distinguish overdue collections, expense growth and liquidity pressure and honor no-borrowing instructions. Comparisons prominently separate action feasibility from unresolved reserve goals. Forecasts deduplicate linked commitments and disclose baseline/error limitations; loan comparisons show their own fees. Decision reports use readable tables and numeric safe XLSX cells.

Latest verification: 149 SQLite tests passed (two PostgreSQL-only skipped), 151 tests passed on isolated PostgreSQL 17, and 63 Chromium layout/workflow checks passed. No live-provider, deployed-scheduler or production-runtime claim is made. See [audit](docs/QUALITY_HARDENING_AUDIT.md), [accounting/imports](docs/ACCOUNTING_AND_IMPORTS.md), [forecast reliability](docs/FORECASTING.md), [provider readiness](docs/AI_PROVIDER_READINESS.md), [monitoring operations](docs/MONITORING_OPERATIONS.md), [future evaluation adapter](docs/EVALUATION_ADAPTER.md) and [verification](docs/TESTING.md).

### Development-only authoritative agentic evaluation

The supplied proprietary benchmark is integrated through an opt-in, source-hash-pinned adapter to
actual Django services in disposable test databases. It is not a production dependency. See
[setup/isolation](docs/AGENTIC_EVALUATION_INTEGRATION.md), [measured results](docs/AGENTIC_EVALUATION_RESULTS.md),
[remaining partial outcomes](docs/BENCHMARK_FAILURE_ANALYSIS.md) and the
[six synthetic demos](docs/COMPETITION_EVALUATION_DEMO.md). The final 172-case run has 147 pass / 25 partial,
not “172 passed”; its weighted 0.917476 is deterministic service coverage, not forecast accuracy or LLM certification.
