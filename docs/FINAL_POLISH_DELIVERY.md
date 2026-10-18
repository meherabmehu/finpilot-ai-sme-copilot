# Final premium polish and survival integration

## Starting repository and reused implementation

Fetched `origin/feat/finpilot-platform` before implementation. Local and remote were
clean and identical at `36d201f600b224db02f6a89064fb5b1fd7e8fa0b`, newer than the
`71a42f9` baseline mentioned in the brief. The existing Django/PostgreSQL/templates,
licensed variable Inter, responsive components, Decimal financial engine, Watchtower,
investigation evidence, decision lifecycle, provider adapter, imports and exports were
retained. No new branch, framework, financial ledger schema or migration was added.

## Approved visual direction

`static/css/polish.css` refines the previous design instead of replacing the application:
light sidebar, white cards, restrained teal, light neutral surfaces, deep navy text,
consistent spacing and clear active navigation. The SVG mark is a code-native teal
leaf. Inter remains locally hosted under its existing OFL license. Bengali uses the
existing system fallback; complete Bangla translation is not claimed.

The public landing/sign-in experience has a split benefit/form layout. Its real form
submits to the original CSRF-protected, rate-limited login handler. Signup, verification,
password reset and validation remain intact. There are no decorative OAuth controls.
The workspace search now uses the existing business-scoped transaction search handler.
No financial figures from the reference image are used.

## Final navigation and page map

Exactly five authenticated pages remain: Dashboard, My Business, AI Advisor,
Financial Planning and Reports. Public landing/authentication is separate.

| Page | Final experience |
|---|---|
| Dashboard | Rule-based survival status, four metrics, one dated cash/reserve chart, up to three next actions, compact actual activity, expandable Watchtower/freshness/policy evidence |
| My Business | Overview, Transactions, Recurring Commitments, Data & Records, Financial Preferences; all old record/edit/import/account URLs preserved |
| AI Advisor | Existing bounded optional provider/fallback, concise conversation, question-specific deterministic evidence, recovery entry and full evidence disclosure |
| Financial Planning | Six focused tabs described below; only the active tab's details render |
| Reports | Available report cards, one global PDF/CSV/Excel format selection, real downloads and advanced earlier exports |

Financial Planning tabs:

1. **Overview**: current problem/status, cash, reserve risk, payment priorities,
   runway basis and one primary recovery action.
2. **Decision Lab**: original question-specific investigations and policy-aware plans,
   progressive five-step review, full/early/delayed/missing/**partial** receipt cases,
   original saved evidence and decision acceptance/modification/rejection.
3. **Cash Flow Forecast**: original moving-average/schedule baseline, observed starting
   cash, coverage, reserve line, earliest modeled breach and honest uncertainty notes.
4. **Scenario Simulation**: typed dated stress cases plus the preserved earlier
   operating illustration builder; explicit calculation and owner-only snapshot saving.
5. **Loan Comparison**: original principal/rate/fee/term calculations, reducing-balance
   schedule, full cost, policy warnings, rate sensitivity and illustrative debt safety.
6. **Recovery Roadmap**: accepted/monitored plans, suggested actions, optional responsible
   person/target, owner-reported progress, original expected cash and recorded outcomes.

Old `/planning/`, `?tab=decisions/forecast/scenarios/loans`, investigation detail and
decision endpoints still work. Planning now opens its Overview. Mobile Planning uses
six visible tabs, while other overflowing tab strips bring the active tab into view.

## Financial capabilities and boundaries

| Capability | Implementation and boundary |
|---|---|
| Cash runway | Current cash divided by positive average paid **operating** daily net burn, over at most 90 days. Requires complete state, at least 30 calendar and 10 active history days. Transfers and financing are excluded from burn; existing paid financing can affect current cash. Zero/negative burn yields no finite estimate. Months use 30 days; no exhaustion date is invented. |
| Survival status | Insufficient Data if required state is missing; Critical for negative recorded/modeled closing cash; At Risk for reserve, intraday funding or due/overdue concerns; otherwise Stable under dated assumptions. No opaque score. |
| Payment priorities | Explicit payroll, critical-supplier and restricted-category flags precede other dated commitments; debt categories are described as debt service. Unprotected spending is never presented as a legal right to defer. |
| Collection risk | Pending invoice amount, recorded due date, days overdue and isolated missing-receipt reserve sensitivity. There is no structured customer identity, so invoice descriptions are not treated as customer identities and no default probabilities are inferred. |
| Scenario uncertainty | Full eligible receipts, user-defined partial/delayed receipts, and an explicit stress case. Assumptions are visible and bounded; cases recalculate actual Decimal timelines. No probabilities or “most likely” label. |
| Sales/cost stress | Sales changes affect typed dated future income only, not issued receivables. Expense shocks affect unprotected expense estimates/recurrences; fixed payables, payroll, critical obligations, restricted categories and debt service are excluded from additional cost shocks. Original plan actions still use its saved policy. |
| Supplier timing | Existing evaluator validates event ownership, timing, protection and action bounds. Counterparty agreement remains a dependency; no actual due date changes. |
| No additional borrowing | Additional finance actions require explicit permission and current snapshot policy limits. Entered terms are illustrations. Existing recorded schedules are retained as assumptions; this does not approve or execute a loan. Saved no-borrowing questions cannot be given a new financing action through this form. |
| Survival-first ranking | The original hard-constraint/gap/intraday/borrowing/cost ranking remains. New cases expose reserve, priority funding and conditional robustness; they do not overwrite original rankings or claim global optimality. |
| Recovery progress | Scoped `AuditEvent` entries record owner-reported tasks. The decision transition history and actual ledger are separate and unchanged. Owner confirmation is not payment proof, settlement or causal attribution. |
| Debt safety | Existing entered-cost, repayment, policy and +2 percentage-point rate checks remain, with clearer caveats. No underwriting, bank approval or verified current lender offer is claimed. |

New `revenue_event_ids`/`expense_estimate_event_ids` snapshot provenance enables typed
adjustments without guessing record kinds. Old snapshots remain readable and unchanged;
new shocks requiring missing provenance ask for a fresh investigation. A changed
fingerprint can mark old proposals stale. Accepted history and review outcomes remain.

Stress calculations never update financial transactions. Saving a scenario creates a
`Scenario` snapshot only. Roadmap confirmations create scoped audit entries only.
PDF/CSV/XLSX include saved stress cases and a current Financial Survival Summary using
the existing report writers and spreadsheet formula protection. The current summary
does not pretend that date filters reconstruct past as-known financial evidence.

## Independent known-answer verification

- Cash 10,000 less 30 daily paid operating expenses of 100 gives cash 7,000, net burn
  100/day and **70 estimated days**. A paid 1,000 financing receipt raises current cash
  to 8,000 and runway to 80 days without changing operating burn.
- Cash 1,000, a dated 800 receipt and a later protected 1,200 payroll gives minimum
  cash **600** under full receipt, **200** under 50% receipt and **-200** without receipt.
  A seven-day delay creates a -200 interim low while ending cash returns to 600.
- Dated future income 500 with 20% decrease becomes 400; an eligible expense 100 with
  10% increase becomes 110; fixed payable 200 and payroll 100 stay unchanged. Ending
  cash from 1,000 is **990**.
- Owner roadmap confirmation is retry-safe and changes neither decision state events
  nor financial rows. Viewer writes, cross-business sources/actions and missing-CSRF
  requests are rejected.

## Actual verification — 18 October 2026

| Check | Measured result |
|---|---|
| Django check / migration dry-run | Passed; no migrations detected |
| Ruff | Passed |
| Frontend build / collectstatic | Passed |
| SQLite full application suite | 216 passed; 2 PostgreSQL-only skips |
| Disposable PostgreSQL 16.14 full suite | 218 passed; no skips |
| Actual Django adapter, full pinned 172-case benchmark | 147 passed, 25 partial, 0 failed/blocked; score **0.917476** |
| Financial/tenant/lifecycle targeted tests | Included in application suite; no oracle changes |
| New browser workflow | 147 page/viewport checks; 21 working report exports; no page errors/overflow or financial-ledger mutation |
| Decision browser regression | 63 page/viewport checks; no overflow or page errors |
| Existing smoke workflow | Five-page navigation, business switching, desktop/tablet/mobile passed |
| Public/authenticated responsive sweep | 302 checks across 14 viewport/orientation combinations; no failures or page errors |
| axe-core 4.11.1 | 18 audits covering public sign-in, all main pages, scenarios and roadmap at 390/1440px; no automated WCAG findings |

The benchmark score is unchanged from the baseline; the redesign does not establish
better prediction accuracy. Partials are not passes. The pinned licensed input package
and generated artifacts stay ignored and outside production. Tests use only isolated
synthetic databases. No model, payment, notification or credit application was invoked.
Automated accessibility tests do not establish complete screen-reader conformance;
screenshots, keyboard focus, reduced motion and visible layouts were also reviewed.

## Screenshots

All are **local ignored artifacts** with synthetic data, not committed production files.
These links work from the local checkout, not the public GitHub renderer.

| Screen | Desktop | Mobile |
|---|---|---|
| Landing | [1440px](../test-results/survival/landing-1440.png) | [390px](../test-results/survival/landing-390.png) |
| Sign in | [1440px](../test-results/survival/signin-1440.png) | [390px](../test-results/survival/signin-390.png) |
| Dashboard | [1440px](../test-results/survival/dashboard-1440.png) | [390px](../test-results/survival/dashboard-390.png) |
| My Business | [1440px](../test-results/survival/business-1440.png) | [390px](../test-results/survival/business-390.png) |
| AI Advisor | [1440px](../test-results/survival/advisor-1440.png) | [390px](../test-results/survival/advisor-390.png) |
| Financial Planning | [1440px](../test-results/survival/lab-1440.png) | [390px](../test-results/survival/lab-390.png) |
| Reports | [1440px](../test-results/survival/reports-1440.png) | [390px](../test-results/survival/reports-390.png) |
| Computed stress cases | [1440px](../test-results/survival/stress-results-1440.png) | [390px](../test-results/survival/stress-results-390.png) |
| Recovery Roadmap | [1440px](../test-results/survival/roadmap-1440.png) | [390px](../test-results/survival/roadmap-390.png) |

## Limits and deliberately deferred work

No inferred customer identities, trained default probabilities, automatic settlement
matching, external task execution, credit approvals or new infrastructure were added.
Task completion remains owner-reported and actual outcomes remain ledger-based.
Uniform receipt shocks are explicit assumptions, not a learned per-customer model.
Runway uses an unvalidated historical average; current dated commitments and debt need
separate review. There is no new calibrated statistical forecast or confidence interval.
Existing provider/SMTP configuration is preserved; no credentials were changed.

## Reproduce and release

Use the current `.venv`/requirements and local synthetic data. Set `DEBUG=true` and
keep demo credentials in your environment. Run the existing Django checks, pytest,
Ruff, `npm.cmd run build`, collectstatic, `scripts.browser_survival`,
`scripts.browser_decisions`, and the smoke/responsive scripts against a local server.
The licensed benchmark procedure is in `AGENTIC_EVALUATION_INTEGRATION.md`; this run's
actual evidence is in ignored `test-results/polish-evaluation-postgres/`.

Branch remains `feat/finpilot-platform`. Source changes are reviewed and committed;
exact commit, remote HEAD and Vercel production status are verified at handoff.
There are no production configuration changes or new migrations. Production
verification uses health and authenticated GETs only; no live financial data is seeded
or edited. The prior explicit authorization includes GitHub push and its existing
Vercel production deployment side effect.
