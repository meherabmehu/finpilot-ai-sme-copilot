# Limitations and status

Implemented: public pages, registration with email verification, secure login/logout and Django reset flow, multi-business creation/switching, owner/viewer authorization, five portal pages, financial records and audit snapshots, bounded preview/confirm CSV/XLSX imports, operating/cash summaries, baseline forecasts, weekly backtesting, explicit saved scenario comparisons, amortization/illustrative product comparisons, scoped conversations and read-only AI tools, PDF/XLSX/CSV exports, idempotent scheduled monitoring, synthetic seed, deployment files.

Configuration-dependent: external email delivery, actual LLM answers, real lender catalog verification, production PostgreSQL, TLS, shared ingress throttling, encrypted backups and scheduler. No credentials or real financial records are shipped.

Not implemented: statutory double-entry accounting, verified net/gross profit, tax or inventory valuation, automated bank feeds, exchange-rate conversion, membership invitation UI, MFA, PostgreSQL RLS, malware scanning, calibrated prediction intervals, partial loan repayments and variable-rate contracts, retention automation, dedicated invoice lines, specialized public-dataset adapters, real loan applications or payment execution. Recurring commitments can be created or disabled; change a commitment by disabling it and adding its replacement.

Scenario estimates use a simplified 30-day operating baseline and explicit in-period payment assumptions. Forecasts can overlap recurring patterns and known pending payments, which is disclosed. Data completeness cannot be verified independently. Loan catalog matching uses amount/country/currency/term and textual eligibility; it does not perform lender underwriting. Only synthetic loan examples are seeded.

Reports cover operating/cash summary, transactions, current forecast, saved scenarios, saved financing illustrations and data quality. Separate audited P&L and balance-sheet-derived working capital are not provided. Bounded recent business/user-scoped model context is replayed; live model behavior remains unverified. No feature should be described as competition-ready without operator integration testing and resolving these scope gaps.


## Agentic continuation status
Watchtower, preference editing, saved investigations, scenario comparisons, simple three-action modifications (advanced JSON up to eight), decision lifecycle/history, manual outcome checks, financing sensitivity and agentic exports are integrated into the five pages. No new primary navigation page or model training was added.

Recommendations are bounded heuristic choices, not exhaustive financial optimization. Cash completeness is user-confirmed; unrecorded liabilities, real receipt timing, fees and counterparty agreement remain unknown. Original evidence is application-preserved, not database-enforced immutable. Policy-feedback suggestions exist as a service but not a dedicated UI. Detailed lender metadata is not independently verified. Existing historical forecasts remain separate from the dated Decision Lab and can overlap scheduled expenses as disclosed.

Monitoring works when the management command or manual review is invoked; no deployed scheduler or 24/7 autonomy was verified. Real LLM/SMTP, PostgreSQL contention, deployment build/migration application, assistive-technology testing and physical-device/Safari testing remain external verification tasks. The synthetic follow-up supports only simple timing/collection plans. Authenticated GitHub push is blocked until a secure credential is supplied.
