# Competition demo

1. Run migrations, build assets, seed with an explicit long DEMO_PASSWORD, and run monitoring.
2. Open the landing page; show the signup/onboarding flow or sign in as demo@finpilot.local.
3. Open ABC Electronics. Explain the synthetic banner and distinction between revenue, operating surplus and cash.
4. Visit AI Advisor. With a configured provider ask about cash health; otherwise explicitly show the unavailable AI state and deterministic analysis.
5. Open the 30-day baseline, explain history coverage and limitations, then save three scenarios with different assumptions.
6. Compare loan costs using explicit amount, rate, term and capacity. The synthetic product is not an available bank offer.
7. Generate and download CSV, XLSX and PDF reports.
8. Switch to Tasty Bites. Show changed records and separate conversations.
9. Sign in with an unrelated account and request the first business UUID URL. Access returns 404. Automated tests verify this same negative case.

Do not describe simulated scenarios as actual decisions executed, or unconfigured AI as live intelligence.


## Reproducible Decision Lab scenario (DEBUG only)

Use an isolated local development database. Set `DEBUG=true` and set `DEMO_PASSWORD` securely to at least 12 characters (do not commit it).

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_decision_demo
```

Sign in as `decisions@finpilot.local` with the configured password. The command prints the synthetic business URL. Existing demo users keep their existing password. Never run seed/reset/follow-up against production; the command rejects DEBUG=false. All four ledger records and the workspace are labeled synthetic.

Known opening cash USD 1000; supplier 500 due +2 days; payroll 800 due +3; customer receipt 700 due +5; inventory 100 due +7. Baseline daily cash: 1000 → 500 → -300 → 400 → 300. Future receipts remain assumptions. Minimum is -300 and ending balance is 300.

1. Open Dashboard Watchtower → Decision Lab.
2. Ask “Can I pay my supplier and protect payroll?”
3. Inspect at least three alternatives, formulas, dependencies and original timeline.
4. Record Request earlier collection (or Discuss supplier timing); no transactions change.
5. Check monitoring; decision becomes Monitoring and is not evaluated prematurely.
6. To simulate elapsed time and actual receipts/payments explicitly:

```bash
python manage.py seed_decision_demo --follow-up
```

This DEBUG-only operation converts this demo's selected timing/collection events into synthetic paid activity and evaluates at the fixed future review date, without changing the system clock. Use an unmodified timing plan, not a split/financing plan, for this scripted follow-up. Expected and actual ending cash reconcile to 300; difference 0. It does not prove real-world causation.

7. Reload detail and export investigation/decision evidence in Reports.
8. Reset only this dedicated synthetic workspace and its synthetic decision history:

```bash
python manage.py seed_decision_demo --reset
```

Other businesses are not reset. This reset is intentionally destructive only for the named demo's local synthetic history; do not add real records to it. For a finite browser workflow including seven-width layout checks, install Playwright Chromium/dependencies and run `python -m scripts.browser_decisions` after seeding. The script creates a synthetic investigation and accepts a plan; it never targets the hosted website.
