# Limitations and status

Implemented: public pages, registration with email verification, secure login/logout and Django reset flow, multi-business creation/switching, owner/viewer authorization, five portal pages, financial records and audit snapshots, bounded preview/confirm CSV/XLSX imports, operating/cash summaries, baseline forecasts, weekly backtesting, explicit saved scenario comparisons, amortization/illustrative product comparisons, scoped conversations and read-only AI tools, PDF/XLSX/CSV exports, idempotent scheduled monitoring, synthetic seed, deployment files.

Configuration-dependent: external email delivery, actual LLM answers, real lender catalog verification, production PostgreSQL, TLS, shared ingress throttling, encrypted backups and scheduler. No credentials or real financial records are shipped.

Not implemented: statutory double-entry accounting, verified net/gross profit, tax or inventory valuation, automated bank feeds, exchange-rate conversion, membership invitation UI, MFA, PostgreSQL RLS, malware scanning, calibrated prediction intervals, partial loan repayments and variable-rate contracts, retention automation, dedicated invoice lines, specialized public-dataset adapters, real loan applications or payment execution. Recurring commitments can be created or disabled; change a commitment by disabling it and adding its replacement.

Scenario estimates use a simplified 30-day operating baseline and explicit in-period payment assumptions. Forecasts can overlap recurring patterns and known pending payments, which is disclosed. Data completeness cannot be verified independently. Loan catalog matching uses amount/country/currency/term and textual eligibility; it does not perform lender underwriting. Only synthetic loan examples are seeded.

Reports cover operating/cash summary, transactions, current forecast, saved scenarios, saved financing illustrations and data quality. Separate audited P&L and balance-sheet-derived working capital are not provided. Multi-turn model context is not replayed. No feature should be described as competition-ready without operator integration testing and resolving these scope gaps.
