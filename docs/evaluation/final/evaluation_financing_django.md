# FinPilot Agentic Evaluation - financing suite

Generated (UTC): 2026-10-17T21:45:01+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 14
Duration: 0.95 s

> Full run against a connected adapter; the overall weighted score is reportable.

## Summary

| Metric | Value |
|---|---|
| executed | 14 |
| passed | 11 |
| partial | 3 |
| failed | 0 |
| blocked | 0 |
| skipped | 0 |
| overall weighted score | 0.8618 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| financing | 14 | 14 | 11 | 3 | 0 | 0 | 0.8618 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 13 | 1 | 0.9615 |
| liquidity_reasoning | 12 | 14 | 0 | 1.0000 |
| payment_timing | 10 | 1 | 13 | 1.0000 |
| financing_arithmetic | 10 | 12 | 2 | 0.4583 |
| policy_compliance | 14 | 14 | 0 | 0.7857 |
| plan_selection | 10 | 14 | 0 | 1.0000 |
| evidence_reference | 10 | 14 | 0 | 1.0000 |
| uncertainty_disclosure | 9 | 14 | 0 | 0.7173 |
| data_quality_handling | 5 | 0 | 14 | - |
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
| FIN-001 | financing | simple | pass | 0.891 | - |
| FIN-002 | financing | multi_step | partial | 0.644 | - |
| FIN-003 | financing | multi_step | pass | 0.891 | - |
| FIN-004 | financing | multi_step | pass | 0.846 | - |
| FIN-005 | financing | conflicting | pass | 0.938 | - |
| FIN-006 | financing | conflicting | partial | 0.768 | - |
| FIN-007 | financing | edge | pass | 0.938 | - |
| FIN-008 | financing | multi_step | pass | 1.000 | - |
| FIN-009 | financing | multi_step | pass | 0.844 | - |
| FIN-010 | financing | edge | pass | 1.000 | - |
| FIN-011 | financing | multi_step | pass | 0.938 | - |
| FIN-012 | financing | simple | pass | 0.833 | - |
| FIN-013 | financing | edge | pass | 0.887 | - |
| FIN-014 | financing | conflicting | partial | 0.650 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
