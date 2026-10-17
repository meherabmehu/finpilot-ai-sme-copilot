# Verification

Run commands from README. Tests use pytest-django and isolated test databases; browser checks use the explicitly seeded development database. Static assets must be built and collected before page-render tests, because tests exercise production-style manifest resolution.

Final expanded suite: **68 passed in 70.95 seconds** on local SQLite, Python 3.14 and Django 5.2.18. The initial 53-test suite exposed a missing Chart.js source-map asset; packaging was fixed before the successful full run. The final suite includes cash completeness, recurring commitments, saved financing and expanded read-only tools.

Browser verification passed at 1440px, 390px and 768px, covering five-page navigation, login, workspace switching, no page JavaScript errors and no horizontal page overflow. Django check and production `check --deploy` passed with no issues; migration drift check found no changes. The frontend build passed and npm audit reported **zero vulnerabilities** after upgrading the development watcher dependency. Deployment checks validate settings, not a running production database.

Coverage includes known-answer EMI and rounding, reconciliation, pending/paid distinctions, archives and dates, forecasting gates, scheduled obligations, scenario side effects, successful and malicious CSV/XLSX paths, duplicate rejection, export formula protection, page rendering, registration/verification/login, reset delivery, business creation, tenant isolation, viewer restrictions, CSRF, foreign account rejection, scoped tools and monitoring idempotency. Provider API calls are mocked only inside tests; live provider integration is configuration-dependent and unverified without credentials.

The browser script checks desktop (1440px), mobile (390px), tablet (768px), public landing, login, all five primary pages, business switching, JavaScript errors and horizontal page overflow. Screenshots remain local and ignored. This is not an exhaustive end-to-end test of every form or assistive technology.

Docker daemon was unavailable in the execution environment, so container build/runtime and PostgreSQL deployment are not verified here. SQLite migrations and tests do not establish PostgreSQL-specific correctness. SMTP and live LLM requests require external configuration. No ML training is performed.
