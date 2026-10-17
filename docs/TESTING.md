# Verification

## Final quality hardening verification (latest)

Starting commit 3fd006e, branch feat/finpilot-platform. Unchanged baseline after requirements installation, npm ci/build and collectstatic: 124 passed. Initial missing Django/Ruff executables were workspace dependency prerequisites, not application failures.

Final executed checks:
- SQLite: **149 passed, 2 skipped** (only PostgreSQL-specific concurrency tests), 40.51 seconds.
- Disposable local PostgreSQL 17: **151 passed, 0 skipped**, 44.00 seconds, including concurrent preview/confirmation and accept/monitor threads. Created a fresh local role/database; pytest created/destroyed its separate test database. No production database used.
- Django check, makemigrations --check --dry-run: passed, no new migrations.
- DEBUG=false `check --deploy`: passed using ephemeral secret and isolated local database settings, not deployed production verification.
- Frontend build, collectstatic, Ruff, diff whitespace and staged credential-pattern checks passed.
- Chromium: actual question → modification → acceptance → monitoring, **63 page-width checks**, no page-level horizontal overflow or JavaScript errors; five pages, all planning tabs and saved detail at 320/375/390/768/1024/1440/1920. Synthetic local DB only.
- PDF parsed using pypdf for section/currency/escaping assertions; CSV/XLSX exported and numeric cells/formula safety checked. A synthetic two-investigation PDF (12 pages including appendices) was rasterized and its first page visually inspected. This is not an exhaustive visual review of every export/page.

Independent Decimal annuity check: principal 10000, nominal annual 12%, 12 months, fee 200 yields payment 888.49, interest 661.86, financing cost 861.86, total repayment+fees 10861.86. Product fee 100 yields 10761.86. Sum of actual scheduled payments plus fees reconciles, including the final adjusted installment. No amortization-formula change was needed.

New regressions cover repeat/corrected/ambiguous-reference imports, earned-vs-cash semantics, question-specific overdue/expense evidence, no-borrowing custom plans, unresolved reserve gaps, linked forecast schedules and WAPE diagnostics, structured report sections/types, resource ID tenant boundaries, viewer/CSRF denials, mocked malicious tools/descriptions, safe monitoring failures, source-record outcome changes, manual record replay and generic production denial. These are scoped security checks, not a penetration test or proof of all possible race interleavings.

Not verified live: provider/SMTP, installed scheduler, production migration/deploy/runtime, external evaluation ZIP, Safari/physical hardware or comprehensive assistive-technology/contrast audit. No paid service or production setting was activated. Final compatibility checks also cover no-borrowing enforcement on legacy saved investigations and business-specific expense thresholds in legacy alert cards.

To run local SQLite checks, use README build/collectstatic commands. For PostgreSQL use an explicitly disposable database, a role allowed to create its own pytest test database, and the standard POSTGRES_* or DATABASE_URL configuration. Do NOT point tests at a production database or enable --reuse-db on shared business databases.

## Previous continuation verification (historical)


## Continuation verification — 2026-10-17 (historical)

Executed locally on Python 3.13.16 / Django 5.2.18 / SQLite:

- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes.
- Local `migrate`: all migrations through existing 0004 applied successfully; no new migration.
- `npm ci`, `npm run build`, `python manage.py collectstatic --noinput`: passed.
- `python -m pytest -q`: **124 passed**, 0 failed, 0 skipped, 34.18 seconds in the final code run.
- `ruff check .`: passed.
- `python -m scripts.browser_decisions`: Chromium workflow (login, investigate, accept, monitor), 42 page-width checks, zero page overflow and zero JavaScript errors. Five primary pages plus saved detail; seven widths 320, 375, 390, 768, 1024, 1440, 1920. Detail disclosures expanded for layout checks.
- `monitor_finances --business` invoked locally on synthetic data: completed MonitoringRun, no notifications sent.

New tests cover owner/viewer/business isolation, POST/CSRF, request replay, stale policy/evidence, modifications and retries, same-day payment-first cash risk, snapshot opening date, all nine agentic export format/type combinations, formula escaping, useful no-LLM explanation and DEBUG-only reproducible demo/reset/outcome reconciliation. Original upload/tool-safety/report tests also pass.

On the clean checkout, the first run had 71 passes / 28 missing-static-manifest failures. Collecting static assets resolved those environmental failures; the unchanged baseline then passed 99 tests. These failures were not concealed by relaxing production manifest storage.

Not verified in this continuation: live LLM/SMTP, production deploy/database migration, PostgreSQL lock contention, installed scheduler, Safari/physical hardware, comprehensive keyboard/screen-reader/contrast audit, or all browser form permutations. Local browser tests use an isolated synthetic workspace and do not target production.

## Prior implementation verification (historical, not rerun unless stated above)


Run commands from README. Tests use pytest-django and isolated test databases; browser checks use the explicitly seeded development database. Static assets must be built and collected before page-render tests, because tests exercise production-style manifest resolution.

Final expanded suite: **68 passed in 70.95 seconds** on local SQLite, Python 3.14 and Django 5.2.18. The initial 53-test suite exposed a missing Chart.js source-map asset; packaging was fixed before the successful full run. The final suite includes cash completeness, recurring commitments, saved financing and expanded read-only tools.

Browser verification passed at 1440px, 390px and 768px, covering five-page navigation, login, workspace switching, no page JavaScript errors and no horizontal page overflow. Django check and production `check --deploy` passed with no issues; migration drift check found no changes. The frontend build passed and npm audit reported **zero vulnerabilities** after upgrading the development watcher dependency. Deployment checks validate settings, not a running production database.

Coverage includes known-answer EMI and rounding, reconciliation, pending/paid distinctions, archives and dates, forecasting gates, scheduled obligations, scenario side effects, successful and malicious CSV/XLSX paths, duplicate rejection, export formula protection, page rendering, registration/verification/login, reset delivery, business creation, tenant isolation, viewer restrictions, CSRF, foreign account rejection, scoped tools and monitoring idempotency. Provider API calls are mocked only inside tests; live provider integration is configuration-dependent and unverified without credentials.

The browser script checks desktop (1440px), mobile (390px), tablet (768px), public landing, login, all five primary pages, business switching, JavaScript errors and horizontal page overflow. Screenshots remain local and ignored. This is not an exhaustive end-to-end test of every form or assistive technology.

Responsive update: `scripts/responsive_check.py` passed 308 layout/menu checks over 14 viewports: widths 320, 360, 390, 430, 600, 768, 960, 1024, 1280, 1440, 1920 and 2560px, plus 568×320 and 844×390 landscape. It covers 18 public/authentication/onboarding/portal routes, every business and planning tab, open header menus, and long business names and monetary values. No layout failures or JavaScript errors were reported. The existing navigation/switching browser check passed again, along with 26 page/import regression tests. These are Chromium viewport checks; physical iOS/Android hardware and Safari were not available. Safe-area and mobile input-zoom behavior are implemented through standard CSS and viewport settings, but are not hardware-verified.

Docker daemon was unavailable in the execution environment, so container build/runtime and PostgreSQL deployment are not verified here. SQLite migrations and tests do not establish PostgreSQL-specific correctness. SMTP and live LLM requests require external configuration. No ML training is performed.
