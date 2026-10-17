# FinPilot Agentic Evaluation - data_quality suite

Generated (UTC): 2026-10-17T21:45:04+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 18
Duration: 1.035 s

> Full run against a connected adapter; the overall weighted score is reportable.

## Summary

| Metric | Value |
|---|---|
| executed | 18 |
| passed | 17 |
| partial | 1 |
| failed | 0 |
| blocked | 0 |
| skipped | 0 |
| overall weighted score | 0.9335 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| data_quality | 18 | 18 | 17 | 1 | 0 | 0 | 0.9335 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 16 | 2 | 0.9479 |
| liquidity_reasoning | 12 | 13 | 5 | 1.0000 |
| payment_timing | 10 | 2 | 16 | 0.7500 |
| financing_arithmetic | 10 | 0 | 18 | - |
| policy_compliance | 14 | 13 | 5 | 1.0000 |
| plan_selection | 10 | 18 | 0 | 0.9444 |
| evidence_reference | 10 | 18 | 0 | 1.0000 |
| uncertainty_disclosure | 9 | 18 | 0 | 0.8102 |
| data_quality_handling | 5 | 11 | 7 | 0.6515 |
| tenant_isolation_safety | 5 | 0 | 18 | - |

## Ranking objective (declared, never implied)

- **cautious**: Hard payroll/critical-supplier/restricted-category constraints first; then minimise the reserve funding gap; then the payment-first intraday gap; then borrowing drawn; then total financing cost; then the number of actions. Best among the evaluated plans only - not a globally optimal solution, and conditional on counterparties agreeing.

Non-claims attached to every ranking:

- No plan is 'optimal' in a global sense; only best among those supplied.
- Every plan that moves a payment or a collection requires the counterparty's agreement.
- Financing actions are illustrations: availability, approval and pricing are unknown.

## Cases

| Scenario | Category | Difficulty | Verdict | Score | Critical failures |
|---|---|---|---|---|---|
| DQ-001 | data_quality | missing_information | pass | 0.954 | - |
| DQ-002 | data_quality | missing_information | pass | 1.000 | - |
| DQ-003 | data_quality | missing_information | pass | 0.893 | - |
| DQ-004 | data_quality | missing_information | partial | 0.775 | - |
| DQ-005 | data_quality | missing_information | pass | 1.000 | - |
| DQ-006 | data_quality | missing_information | pass | 0.867 | - |
| DQ-007 | data_quality | edge | pass | 0.893 | - |
| DQ-008 | data_quality | conflicting | pass | 0.936 | - |
| DQ-009 | data_quality | missing_information | pass | 0.925 | - |
| DQ-010 | data_quality | edge | pass | 1.000 | - |
| DQ-011 | data_quality | edge | pass | 1.000 | - |
| DQ-012 | data_quality | edge | pass | 1.000 | - |
| DQ-013 | data_quality | edge | pass | 0.929 | - |
| DQ-014 | data_quality | missing_information | pass | 0.949 | - |
| DQ-015 | data_quality | edge | pass | 1.000 | - |
| DQ-016 | data_quality | edge | pass | 0.938 | - |
| DQ-017 | data_quality | conflicting | pass | 0.893 | - |
| DQ-018 | data_quality | missing_information | pass | 0.853 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
