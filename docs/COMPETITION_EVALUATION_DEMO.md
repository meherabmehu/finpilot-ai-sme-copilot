# Competition evaluation demo — measured synthetic services

Use the licensed external package and the opt-in CLI in AGENTIC_EVALUATION_INTEGRATION.md. No source ZIP, production data or model key is needed by the deployed app. Each demonstration runs in an isolated test database, not a live customer workspace. Figures below come from actual final Django responses, not the reference adapter.

Final weighted result: 147 pass / 25 partial / 0 failed or blocked out of 172, score 0.917476. This is deterministic service evaluation, not prediction accuracy.

## 1. Collections without assuming payment — REC-002

Inspect recorded overdue exposure, then the hypothetical recovery comparison. The reason for nonpayment and actual customer receipt are unknown. No message/payment is executed.

Run with `--suite full --case REC-002` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **answered**.
- Recorded cash: **41000.00**; dated minimum: **-2500.00**; reserve funding gap: **123550.00**.
- Recorded overdue receivables: **27700.00**; hypothetical recommended candidate: **Assume overdue recovery in 1 days**.

## 2. Payroll and supplier collision — LIQ-001

Show first shortfall separately from minimum date. Protected payroll cannot be delayed merely to improve the chart; the unresolved reserve gap stays visible.

Run with `--suite full --case LIQ-001` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **answered**.
- Recorded cash: **16800.00**; dated minimum: **-10300.00**; reserve funding gap: **27120.00**.
- First shortfall: **2026-03-06**; minimum date: **2026-04-01**.

## 3. Owner policy changes the feasible answer — PAIR-02-A

Compare PAIR-02-B: only the owner policy permits the payroll-delay candidate. This is a synthetic contrast, not a suggestion to relax protection.

Run with `--suite full --case PAIR-02-A` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **answered**.
- Recorded cash: **20500.00**; dated minimum: **-31100.00**; reserve funding gap: **41691.00**.
- A actual recommendation: **Keep recorded schedule**; B: **Delay payroll by 5 days**.
- A feasible plans: Keep recorded schedule; B: Delay payroll by 5 days, Keep recorded schedule.

## 4. Validated modification — DM-004

The actual lifecycle is proposed → modified → accepted; a modification without a replacement specification is rejected. Expected balance remains labelled simulated.

Run with `--suite full --case DM-004` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **answered**.
- Recorded cash: **13600.00**; dated minimum: **4500.00**; reserve funding gap: **6805.00**.
- Actual states: proposed → modified → modified → accepted.

## 5. Monitoring against synthetic observations — DM-006

The harness supplies explicitly synthetic paid arrivals, then actual monitor_business evaluates the decision. Difference 0.00 verifies this arithmetic, not that a plan caused business success. Notification sent: false.

Run with `--suite full --case DM-006` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **answered**.
- Recorded cash: **13600.00**; dated minimum: **4500.00**; reserve funding gap: **6805.00**.
- Actual states: proposed → accepted → evaluated → closed.

## 6. Tenant isolation / refusal — ADV-001

An actual membership lookup refuses access before financial output is returned. No balance, events or recommendation are disclosed. This is a service-boundary test, not a complete pentest.

Run with `--suite full --case ADV-001` (add `--case PAIR-02-B` for the policy comparison).

- Actual response status: **refused**.
- Recorded cash: **not disclosed**; dated minimum: **not disclosed**; reserve funding gap: **not disclosed**.

## Judge-facing caveats

No loan approval, guaranteed customer payment, forecast confidence percentage, causal success or automatic scheduler claim. All external agreements remain unconfirmed. The 25 partial outcomes and seven literal lifecycle rejection-text mismatches are disclosed in the result report. The package remains proprietary evaluation work; commercial source-derived aggregate redistribution is not authorized by this demo.
