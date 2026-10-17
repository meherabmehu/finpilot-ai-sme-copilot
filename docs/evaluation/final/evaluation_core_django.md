# FinPilot Agentic Evaluation - core suite

Generated (UTC): 2026-10-17T21:44:40+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 78
Duration: 4.754 s

> Full run against a connected adapter; the overall weighted score is reportable.

## Summary

| Metric | Value |
|---|---|
| executed | 78 |
| passed | 71 |
| partial | 7 |
| failed | 0 |
| blocked | 0 |
| skipped | 0 |
| overall weighted score | 0.9182 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| edge_cases | 18 | 18 | 17 | 1 | 0 | 0 | 0.9486 | - |
| expenses | 10 | 10 | 8 | 2 | 0 | 0 | 0.9017 | - |
| financing | 14 | 14 | 11 | 3 | 0 | 0 | 0.8618 | - |
| liquidity | 24 | 24 | 24 | 0 | 0 | 0 | 0.9201 | - |
| receivables_payables | 12 | 12 | 11 | 1 | 0 | 0 | 0.9482 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 74 | 4 | 0.9759 |
| liquidity_reasoning | 12 | 78 | 0 | 0.8778 |
| payment_timing | 10 | 21 | 57 | 0.9524 |
| financing_arithmetic | 10 | 14 | 64 | 0.4643 |
| policy_compliance | 14 | 78 | 0 | 0.9231 |
| plan_selection | 10 | 78 | 0 | 0.9872 |
| evidence_reference | 10 | 78 | 0 | 0.9744 |
| uncertainty_disclosure | 9 | 78 | 0 | 0.8157 |
| data_quality_handling | 5 | 1 | 77 | 1.0000 |
| tenant_isolation_safety | 5 | 0 | 78 | - |

## Paired business-policy comparisons

| Pair | Distinguishing constraint | Dimension | Expect | Outcome per member |
|---|---|---|---|---|
| LIQ-005 | collection slip of 5 days | funding_gap | differs | LIQ-005a: recommended='Request earlier collection', feasible=2, gap=70108.00, issues=2; LIQ-005b: recommended='Request earlier collection', feasible=2, gap=72708.00, issues=2; LIQ-005c: recommended='Keep recorded schedule', feasible=1, gap=72708.00, issues=2 |

## Ranking objective (declared, never implied)

- **cautious**: Hard payroll/critical-supplier/restricted-category constraints first; then minimise the reserve funding gap; then the payment-first intraday gap; then borrowing drawn; then total financing cost; then the number of actions. Best among the evaluated plans only - not a globally optimal solution, and conditional on counterparties agreeing.

Non-claims attached to every ranking:

- No plan is 'optimal' in a global sense; only best among those supplied.
- Every plan that moves a payment or a collection requires the counterparty's agreement.
- Financing actions are illustrations: availability, approval and pricing are unknown.

## Cases

| Scenario | Category | Difficulty | Verdict | Score | Critical failures |
|---|---|---|---|---|---|
| EDGE-001 | edge_cases | edge | pass | 1.000 | - |
| EDGE-002 | edge_cases | edge | pass | 0.944 | - |
| EDGE-003 | edge_cases | edge | pass | 1.000 | - |
| EDGE-004 | edge_cases | edge | pass | 1.000 | - |
| EDGE-005 | edge_cases | edge | pass | 0.947 | - |
| EDGE-006 | edge_cases | edge | pass | 1.000 | - |
| EDGE-007 | edge_cases | edge | pass | 1.000 | - |
| EDGE-008 | edge_cases | edge | pass | 1.000 | - |
| EDGE-009 | edge_cases | edge | partial | 0.700 | - |
| EDGE-010 | edge_cases | edge | pass | 0.916 | - |
| EDGE-011 | edge_cases | edge | pass | 0.938 | - |
| EDGE-012 | edge_cases | edge | pass | 1.000 | - |
| EDGE-013 | edge_cases | edge | pass | 1.000 | - |
| EDGE-014 | edge_cases | multi_step | pass | 0.881 | - |
| EDGE-015 | edge_cases | edge | pass | 0.875 | - |
| EDGE-016 | edge_cases | edge | pass | 0.963 | - |
| EDGE-017 | edge_cases | edge | pass | 0.968 | - |
| EDGE-018 | edge_cases | edge | pass | 0.944 | - |
| EXP-001 | expenses | multi_step | pass | 0.956 | - |
| EXP-002 | expenses | conflicting | partial | 0.775 | - |
| EXP-003 | expenses | simple | pass | 1.000 | - |
| EXP-004 | expenses | conflicting | pass | 0.800 | - |
| EXP-005 | expenses | conflicting | partial | 0.671 | - |
| EXP-006 | expenses | multi_step | pass | 0.904 | - |
| EXP-007 | expenses | multi_step | pass | 0.943 | - |
| EXP-008 | expenses | conflicting | pass | 1.000 | - |
| EXP-009 | expenses | multi_step | pass | 0.968 | - |
| EXP-010 | expenses | edge | pass | 1.000 | - |
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
| LIQ-001 | liquidity | simple | pass | 1.000 | - |
| LIQ-002 | liquidity | simple | pass | 1.000 | - |
| LIQ-003 | liquidity | simple | pass | 0.829 | - |
| LIQ-004 | liquidity | multi_step | pass | 0.829 | - |
| LIQ-005a | liquidity | multi_step | pass | 0.936 | - |
| LIQ-005b | liquidity | multi_step | pass | 0.968 | - |
| LIQ-005c | liquidity | multi_step | pass | 0.871 | - |
| LIQ-006 | liquidity | multi_step | pass | 1.000 | - |
| LIQ-007 | liquidity | multi_step | pass | 1.000 | - |
| LIQ-008a | liquidity | edge | pass | 0.829 | - |
| LIQ-008b | liquidity | edge | pass | 0.829 | - |
| LIQ-008c | liquidity | edge | pass | 0.829 | - |
| LIQ-009 | liquidity | edge | pass | 0.887 | - |
| LIQ-010 | liquidity | edge | pass | 0.953 | - |
| LIQ-011 | liquidity | conflicting | pass | 1.000 | - |
| LIQ-012 | liquidity | missing_information | pass | 0.968 | - |
| LIQ-013 | liquidity | edge | pass | 0.829 | - |
| LIQ-014 | liquidity | edge | pass | 1.000 | - |
| LIQ-015 | liquidity | conflicting | pass | 0.936 | - |
| LIQ-016 | liquidity | multi_step | pass | 0.829 | - |
| LIQ-017 | liquidity | conflicting | pass | 1.000 | - |
| LIQ-018 | liquidity | multi_step | pass | 0.936 | - |
| LIQ-019 | liquidity | simple | pass | 1.000 | - |
| LIQ-020 | liquidity | edge | pass | 0.829 | - |
| REC-001 | receivables_payables | simple | pass | 0.957 | - |
| REC-002 | receivables_payables | multi_step | pass | 0.875 | - |
| REC-003 | receivables_payables | simple | pass | 0.875 | - |
| REC-004 | receivables_payables | multi_step | partial | 0.671 | - |
| REC-005 | receivables_payables | conflicting | pass | 1.000 | - |
| REC-006 | receivables_payables | conflicting | pass | 1.000 | - |
| REC-007 | receivables_payables | multi_step | pass | 1.000 | - |
| REC-008 | receivables_payables | multi_step | pass | 1.000 | - |
| REC-009 | receivables_payables | conflicting | pass | 1.000 | - |
| REC-010 | receivables_payables | edge | pass | 1.000 | - |
| REC-011 | receivables_payables | multi_step | pass | 1.000 | - |
| REC-012 | receivables_payables | conflicting | pass | 1.000 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
