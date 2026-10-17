# FinPilot Agentic Evaluation - decision_memory suite

Generated (UTC): 2026-10-17T21:45:13+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 14
Duration: 1.783 s

> Full run against a connected adapter; the overall weighted score is reportable.

## Summary

| Metric | Value |
|---|---|
| executed | 14 |
| passed | 14 |
| partial | 0 |
| failed | 0 |
| blocked | 0 |
| skipped | 0 |
| overall weighted score | 0.9512 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| decision_memory | 14 | 14 | 14 | 0 | 0 | 0 | 0.9512 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 14 | 0 | 1.0000 |
| liquidity_reasoning | 12 | 14 | 0 | 1.0000 |
| payment_timing | 10 | 0 | 14 | - |
| financing_arithmetic | 10 | 0 | 14 | - |
| policy_compliance | 14 | 14 | 0 | 1.0000 |
| plan_selection | 10 | 14 | 0 | 1.0000 |
| evidence_reference | 10 | 14 | 0 | 1.0000 |
| uncertainty_disclosure | 9 | 14 | 0 | 0.6536 |
| data_quality_handling | 5 | 2 | 12 | 0.5000 |
| tenant_isolation_safety | 5 | 0 | 14 | - |

## Ranking objective (declared, never implied)

- **cautious**: Hard payroll/critical-supplier/restricted-category constraints first; then minimise the reserve funding gap; then the payment-first intraday gap; then borrowing drawn; then total financing cost; then the number of actions. Best among the evaluated plans only - not a globally optimal solution, and conditional on counterparties agreeing.

Non-claims attached to every ranking:

- No plan is 'optimal' in a global sense; only best among those supplied.
- Every plan that moves a payment or a collection requires the counterparty's agreement.
- Financing actions are illustrations: availability, approval and pricing are unknown.

## Cases

| Scenario | Category | Difficulty | Verdict | Score | Critical failures |
|---|---|---|---|---|---|
| DM-001 | decision_memory | monitoring | pass | 0.893 | - |
| DM-002 | decision_memory | monitoring | pass | 0.968 | - |
| DM-003 | decision_memory | monitoring | pass | 0.957 | - |
| DM-004 | decision_memory | monitoring | pass | 0.957 | - |
| DM-005 | decision_memory | monitoring | pass | 0.957 | - |
| DM-006 | decision_memory | monitoring | pass | 0.936 | - |
| DM-007 | decision_memory | monitoring | pass | 0.949 | - |
| DM-008 | decision_memory | monitoring | pass | 0.940 | - |
| DM-009 | decision_memory | monitoring | pass | 0.957 | - |
| DM-010 | decision_memory | monitoring | pass | 0.957 | - |
| DM-011 | decision_memory | monitoring | pass | 0.957 | - |
| DM-012 | decision_memory | monitoring | pass | 0.957 | - |
| DM-013 | decision_memory | monitoring | pass | 0.957 | - |
| DM-014 | decision_memory | monitoring | pass | 0.974 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
