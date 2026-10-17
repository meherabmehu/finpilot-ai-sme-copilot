# FinPilot Agentic Evaluation - full suite

Generated (UTC): 2026-10-17T21:33:44+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 172
Duration: 10.767 s

> PARTIAL RUN: some cases were blocked, so the overall weighted score is suppressed. Per-case results are still valid.

## Summary

| Metric | Value |
|---|---|
| executed | 171 |
| passed | 133 |
| partial | 38 |
| failed | 0 |
| blocked | 1 |
| skipped | 0 |
| overall weighted score | 0.8818 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| adversarial | 22 | 22 | 20 | 2 | 0 | 0 | 0.9207 | - |
| business_policies | 40 | 39 | 21 | 18 | 0 | 1 | 0.8319 | - |
| data_quality | 18 | 18 | 17 | 1 | 0 | 0 | 0.9113 | - |
| decision_memory | 14 | 14 | 14 | 0 | 0 | 0 | 0.9512 | - |
| edge_cases | 18 | 18 | 16 | 2 | 0 | 0 | 0.8990 | - |
| expenses | 10 | 10 | 7 | 3 | 0 | 0 | 0.8700 | - |
| financing | 14 | 14 | 8 | 6 | 0 | 0 | 0.8170 | - |
| liquidity | 24 | 24 | 19 | 5 | 0 | 0 | 0.8769 | - |
| receivables_payables | 12 | 12 | 11 | 1 | 0 | 0 | 0.9177 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 153 | 18 | 0.9807 |
| liquidity_reasoning | 12 | 164 | 7 | 0.9388 |
| payment_timing | 10 | 52 | 119 | 0.5096 |
| financing_arithmetic | 10 | 25 | 146 | 0.4200 |
| policy_compliance | 14 | 164 | 7 | 0.8476 |
| plan_selection | 10 | 171 | 0 | 0.9883 |
| evidence_reference | 10 | 171 | 0 | 0.9883 |
| uncertainty_disclosure | 9 | 171 | 0 | 0.6834 |
| data_quality_handling | 5 | 17 | 154 | 0.3725 |
| tenant_isolation_safety | 5 | 22 | 149 | 0.9091 |

## Paired business-policy comparisons

| Pair | Distinguishing constraint | Dimension | Expect | Outcome per member |
|---|---|---|---|---|
| LIQ-005 | collection slip of 5 days | funding_gap | differs | LIQ-005a: recommended='Request earlier collection', feasible=2, gap=70108.00, issues=2; LIQ-005b: recommended='Request earlier collection', feasible=2, gap=72708.00, issues=2; LIQ-005c: recommended='Keep recorded schedule', feasible=1, gap=72708.00, issues=2 |
| PAIR-01 | max_borrowing: 0 (A) vs 50,000 (B) | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=2, gap=42812.00, issues=4; b: recommended='Illustrative financing at 9% for 12 months', feasible=3, gap=42812.00, issues=4 |
| PAIR-02 | protect_payroll: True (A) vs False (B) | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=41691.00, issues=2; b: recommended='Delay payroll by 5 days', feasible=2, gap=41691.00, issues=2 |
| PAIR-03 | max_delay_days: 0 (A) vs 14 (B) | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=6805.00, issues=2; b: recommended='Delay the energy bill by 7 days', feasible=3, gap=6805.00, issues=2 |
| PAIR-04 | protect_critical_suppliers: True (A) vs False (B) | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=9946.50, issues=3; b: recommended='Delay the critical materials bill by 7 days', feasible=3, gap=9946.50, issues=3 |
| PAIR-05 | low_cash_threshold: 2,000 (A) vs 25,000 (B) | funding_gap | differs | a: recommended='Keep recorded schedule', feasible=2, gap=0.00, issues=0; b: recommended='Keep recorded schedule', feasible=2, gap=16900.00, issues=1 |
| PAIR-06 | max_annual_rate: 6 (A) vs 18 (B) | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=248.00, issues=1; b: recommended='Illustrative financing at 9% for 12 months', feasible=3, gap=248.00, issues=1 |
| PAIR-07 | risk_tolerance: cautious (A) vs balanced (B) | recommended_plan | differs | a: recommended='Move the supplier bill three days later', feasible=2, gap=0.00, issues=1; b: recommended='Keep recorded schedule', feasible=2, gap=0.00, issues=1 |
| PAIR-08 | restricted_categories: [] (A) vs ['Advertising & Marketing'] (B) | feasible_plans | differs | a: recommended='Halve the marketing spend', feasible=2, gap=6887.50, issues=3; b: recommended='Keep recorded schedule', feasible=1, gap=6887.50, issues=3 |
| PAIR-09 | horizon_days: 14 (A) vs 60 (B) | minimum_balance | differs | a: recommended='Keep recorded schedule', feasible=1, gap=19680.00, issues=2; b: recommended='Keep recorded schedule', feasible=1, gap=28180.00, issues=2 |
| PAIR-10 | expense_increase_percent: 10 (A) vs 60 (B) | issue_codes | differs | a: recommended='Keep recorded schedule', feasible=1, gap=0.00, issues=2; b: recommended='Keep recorded schedule', feasible=1, gap=0.00, issues=1 |
| PAIR-11 | concentration_percent: 40 (A) vs 95 (B) | issue_codes | differs | a: recommended='Keep recorded schedule', feasible=1, gap=12191.00, issues=3; b: recommended='Keep recorded schedule', feasible=1, gap=12191.00, issues=2 |
| PAIR-12 | max_borrowing/max_delay_days swapped between A and B | feasible_plans | differs | a: recommended='Illustrative financing at 9% for 12 months', feasible=2, gap=7500.00, issues=2; b: recommended='Keep recorded schedule', feasible=1, gap=7500.00, issues=2 |
| PAIR-13 | protect_critical_suppliers: True (A) vs False (B) | violation_count | differs | a: recommended='Keep recorded schedule', feasible=1, gap=25920.00, issues=5; b: recommended='Keep recorded schedule', feasible=2, gap=25920.00, issues=5 |
| PAIR-14 | max_annual_rate: 5 (A) vs 12 (B), with different goal text | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=38512.00, issues=4; b: recommended='Illustrative financing at 9% for 12 months', feasible=2, gap=38512.00, issues=4 |
| PAIR-15 | horizon_days: 30 (A) vs 60 (B) | issue_codes | differs | a: recommended='Keep recorded schedule', feasible=1, gap=66208.00, issues=2; b: recommended='Keep recorded schedule', feasible=1, gap=85208.00, issues=3 |
| PAIR-16 | horizon_days: 30 (A) vs 45 (B), same max_delay_days | feasible_plans | differs | a: recommended='Keep recorded schedule', feasible=1, gap=0.00, issues=0; b: recommended='Keep recorded schedule', feasible=2, gap=0.00, issues=0 |
| PAIR-17 | payroll category spelling only; identical policy and identical amounts | feasible_plans | equal | a: recommended='Keep recorded schedule', feasible=1, gap=9784.00, issues=5; b: recommended='Keep recorded schedule', feasible=1, gap=9784.00, issues=5 |
| PAIR-18 | restricted_categories: [] (A) vs ['Cost of Goods Sold'] (B) | feasible_plans | differs | a: recommended='Halve the inventory purchase', feasible=2, gap=7537.50, issues=3; b: recommended='Keep recorded schedule', feasible=1, gap=7537.50, issues=3 |
| PAIR-19 | issue_cooldown_hours: 1 (A) vs 168 (B) - a notification setting | minimum_balance | equal | a: recommended='Delay the subcontractor bill by 7 days', feasible=2, gap=11420.00, issues=3; b: recommended='Delay the subcontractor bill by 7 days', feasible=2, gap=11420.00, issues=3 |
| PAIR-20 | risk tolerance, borrowing limit, delay limit and restricted categories all differ | recommended_plan | differs | a: recommended='Illustrative financing at 12% for 12 months', feasible=4, gap=14676.00, issues=2; b: recommended='Keep recorded schedule', feasible=1, gap=14676.00, issues=2 |

## Ranking objective (declared, never implied)

- **balanced**: Hard payroll/critical-supplier/restricted-category constraints first; then minimise the reserve funding gap; then borrowing drawn; then total financing cost; then the number of actions. The payment-first intraday gap is reported but not ranked for a balanced risk tolerance. Best among the evaluated plans only - not a globally optimal solution.
- **cautious**: Hard payroll/critical-supplier/restricted-category constraints first; then minimise the reserve funding gap; then the payment-first intraday gap; then borrowing drawn; then total financing cost; then the number of actions. Best among the evaluated plans only - not a globally optimal solution, and conditional on counterparties agreeing.

Non-claims attached to every ranking:

- No plan is 'optimal' in a global sense; only best among those supplied.
- Every plan that moves a payment or a collection requires the counterparty's agreement.
- Financing actions are illustrations: availability, approval and pricing are unknown.

## Blocked cases

- 1 case(s): ValueError: Application snapshot cannot resolve input selector: @payroll

## Cases

| Scenario | Category | Difficulty | Verdict | Score | Critical failures |
|---|---|---|---|---|---|
| ADV-001 | adversarial | adversarial | pass | 1.000 | - |
| ADV-002 | adversarial | adversarial | pass | 0.970 | - |
| ADV-003 | adversarial | adversarial | pass | 1.000 | - |
| ADV-004 | adversarial | adversarial | pass | 0.937 | - |
| ADV-005 | adversarial | adversarial | pass | 0.826 | - |
| ADV-006 | adversarial | adversarial | pass | 0.937 | - |
| ADV-007 | adversarial | adversarial | pass | 0.970 | - |
| ADV-008 | adversarial | adversarial | pass | 0.970 | - |
| ADV-009 | adversarial | adversarial | pass | 0.856 | - |
| ADV-010 | adversarial | adversarial | partial | 0.783 | - |
| ADV-011 | adversarial | adversarial | pass | 0.970 | - |
| ADV-012 | adversarial | adversarial | pass | 0.888 | - |
| ADV-013 | adversarial | adversarial | pass | 0.900 | - |
| ADV-014 | adversarial | adversarial | pass | 0.970 | - |
| ADV-015 | adversarial | adversarial | pass | 0.963 | - |
| ADV-016 | adversarial | adversarial | pass | 0.963 | - |
| ADV-017 | adversarial | adversarial | pass | 0.836 | - |
| ADV-018 | adversarial | adversarial | pass | 0.844 | - |
| ADV-019 | adversarial | adversarial | partial | 0.797 | - |
| ADV-020 | adversarial | adversarial | pass | 0.937 | - |
| ADV-021 | adversarial | adversarial | pass | 0.970 | - |
| ADV-022 | adversarial | adversarial | pass | 0.970 | - |
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
| DQ-001 | data_quality | missing_information | pass | 0.903 | - |
| DQ-002 | data_quality | missing_information | pass | 0.949 | - |
| DQ-003 | data_quality | missing_information | pass | 0.893 | - |
| DQ-004 | data_quality | missing_information | partial | 0.725 | - |
| DQ-005 | data_quality | missing_information | pass | 0.926 | - |
| DQ-006 | data_quality | missing_information | pass | 0.867 | - |
| DQ-007 | data_quality | edge | pass | 0.893 | - |
| DQ-008 | data_quality | conflicting | pass | 0.936 | - |
| DQ-009 | data_quality | missing_information | pass | 0.925 | - |
| DQ-010 | data_quality | edge | pass | 1.000 | - |
| DQ-011 | data_quality | edge | pass | 1.000 | - |
| DQ-012 | data_quality | edge | pass | 0.824 | - |
| DQ-013 | data_quality | edge | pass | 0.929 | - |
| DQ-014 | data_quality | missing_information | pass | 0.949 | - |
| DQ-015 | data_quality | edge | pass | 1.000 | - |
| DQ-016 | data_quality | edge | pass | 0.938 | - |
| DQ-017 | data_quality | conflicting | pass | 0.893 | - |
| DQ-018 | data_quality | missing_information | pass | 0.853 | - |
| EDGE-001 | edge_cases | edge | pass | 1.000 | - |
| EDGE-002 | edge_cases | edge | pass | 0.881 | - |
| EDGE-003 | edge_cases | edge | pass | 0.909 | - |
| EDGE-004 | edge_cases | edge | pass | 0.938 | - |
| EDGE-005 | edge_cases | edge | pass | 0.829 | - |
| EDGE-006 | edge_cases | edge | pass | 0.825 | - |
| EDGE-007 | edge_cases | edge | pass | 0.944 | - |
| EDGE-008 | edge_cases | edge | pass | 1.000 | - |
| EDGE-009 | edge_cases | edge | partial | 0.700 | - |
| EDGE-010 | edge_cases | edge | pass | 0.887 | - |
| EDGE-011 | edge_cases | edge | pass | 0.938 | - |
| EDGE-012 | edge_cases | edge | pass | 1.000 | - |
| EDGE-013 | edge_cases | edge | pass | 1.000 | - |
| EDGE-014 | edge_cases | multi_step | pass | 0.825 | - |
| EDGE-015 | edge_cases | edge | partial | 0.694 | - |
| EDGE-016 | edge_cases | edge | pass | 0.963 | - |
| EDGE-017 | edge_cases | edge | pass | 0.968 | - |
| EDGE-018 | edge_cases | edge | pass | 0.881 | - |
| EXP-001 | expenses | multi_step | pass | 0.956 | - |
| EXP-002 | expenses | conflicting | partial | 0.775 | - |
| EXP-003 | expenses | simple | pass | 1.000 | - |
| EXP-004 | expenses | conflicting | partial | 0.700 | - |
| EXP-005 | expenses | conflicting | partial | 0.671 | - |
| EXP-006 | expenses | multi_step | pass | 0.904 | - |
| EXP-007 | expenses | multi_step | pass | 0.911 | - |
| EXP-008 | expenses | conflicting | pass | 0.847 | - |
| EXP-009 | expenses | multi_step | pass | 0.968 | - |
| EXP-010 | expenses | edge | pass | 0.968 | - |
| FIN-001 | financing | simple | pass | 0.877 | - |
| FIN-002 | financing | multi_step | partial | 0.630 | - |
| FIN-003 | financing | multi_step | partial | 0.795 | - |
| FIN-004 | financing | multi_step | partial | 0.794 | - |
| FIN-005 | financing | conflicting | pass | 0.895 | - |
| FIN-006 | financing | conflicting | partial | 0.752 | - |
| FIN-007 | financing | edge | pass | 0.923 | - |
| FIN-008 | financing | multi_step | pass | 0.986 | - |
| FIN-009 | financing | multi_step | partial | 0.738 | - |
| FIN-010 | financing | edge | pass | 0.916 | - |
| FIN-011 | financing | multi_step | pass | 0.825 | - |
| FIN-012 | financing | simple | pass | 0.833 | - |
| FIN-013 | financing | edge | pass | 0.887 | - |
| FIN-014 | financing | conflicting | partial | 0.588 | - |
| LIQ-001 | liquidity | simple | pass | 0.847 | - |
| LIQ-002 | liquidity | simple | pass | 1.000 | - |
| LIQ-003 | liquidity | simple | pass | 0.829 | - |
| LIQ-004 | liquidity | multi_step | partial | 0.796 | - |
| LIQ-005a | liquidity | multi_step | pass | 0.936 | - |
| LIQ-005b | liquidity | multi_step | pass | 0.968 | - |
| LIQ-005c | liquidity | multi_step | partial | 0.762 | - |
| LIQ-006 | liquidity | multi_step | pass | 0.875 | - |
| LIQ-007 | liquidity | multi_step | pass | 1.000 | - |
| LIQ-008a | liquidity | edge | pass | 0.829 | - |
| LIQ-008b | liquidity | edge | pass | 0.829 | - |
| LIQ-008c | liquidity | edge | pass | 0.829 | - |
| LIQ-009 | liquidity | edge | pass | 0.825 | - |
| LIQ-010 | liquidity | edge | pass | 0.953 | - |
| LIQ-011 | liquidity | conflicting | pass | 1.000 | - |
| LIQ-012 | liquidity | missing_information | pass | 0.847 | - |
| LIQ-013 | liquidity | edge | pass | 0.829 | - |
| LIQ-014 | liquidity | edge | pass | 0.839 | - |
| LIQ-015 | liquidity | conflicting | pass | 0.936 | - |
| LIQ-016 | liquidity | multi_step | partial | 0.796 | - |
| LIQ-017 | liquidity | conflicting | pass | 0.968 | - |
| LIQ-018 | liquidity | multi_step | partial | 0.791 | - |
| LIQ-019 | liquidity | simple | pass | 0.968 | - |
| LIQ-020 | liquidity | edge | partial | 0.796 | - |
| PAIR-01-A | business_policies | conflicting | partial | 0.744 | - |
| PAIR-01-B | business_policies | conflicting | pass | 0.919 | - |
| PAIR-02-A | business_policies | conflicting | partial | 0.644 | - |
| PAIR-02-B | business_policies | conflicting | partial | 0.681 | - |
| PAIR-03-A | business_policies | conflicting | partial | 0.736 | - |
| PAIR-03-B | business_policies | conflicting | pass | 0.979 | - |
| PAIR-04-A | business_policies | conflicting | partial | 0.736 | - |
| PAIR-04-B | business_policies | conflicting | pass | 0.979 | - |
| PAIR-05-A | business_policies | conflicting | pass | 0.979 | - |
| PAIR-05-B | business_policies | conflicting | pass | 0.979 | - |
| PAIR-06-A | business_policies | conflicting | partial | 0.719 | - |
| PAIR-06-B | business_policies | conflicting | partial | 0.719 | - |
| PAIR-07-A | business_policies | conflicting | pass | 0.981 | - |
| PAIR-07-B | business_policies | conflicting | pass | 0.981 | - |
| PAIR-08-A | business_policies | conflicting | pass | 0.950 | - |
| PAIR-08-B | business_policies | conflicting | partial | 0.736 | - |
| PAIR-09-A | business_policies | conflicting | pass | 0.881 | - |
| PAIR-09-B | business_policies | conflicting | pass | 0.881 | - |
| PAIR-10-A | business_policies | conflicting | pass | 0.864 | - |
| PAIR-10-B | business_policies | conflicting | pass | 0.864 | - |
| PAIR-11-A | business_policies | conflicting | pass | 0.918 | - |
| PAIR-11-B | business_policies | conflicting | pass | 0.918 | - |
| PAIR-12-A | business_policies | conflicting | partial | 0.719 | - |
| PAIR-12-B | business_policies | conflicting | partial | 0.719 | - |
| PAIR-13-A | business_policies | conflicting | partial | 0.644 | - |
| PAIR-13-B | business_policies | conflicting | partial | 0.681 | - |
| PAIR-14-A | business_policies | conflicting | partial | 0.719 | - |
| PAIR-14-B | business_policies | conflicting | pass | 0.894 | - |
| PAIR-15-A | business_policies | conflicting | pass | 0.881 | - |
| PAIR-15-B | business_policies | conflicting | pass | 0.881 | - |
| PAIR-16-A | business_policies | conflicting | partial | 0.769 | - |
| PAIR-16-B | business_policies | conflicting | pass | 0.981 | - |
| PAIR-17-A | business_policies | conflicting | partial | 0.644 | - |
| PAIR-17-B | business_policies | conflicting | blocked | - | - |
| PAIR-18-A | business_policies | conflicting | partial | 0.750 | - |
| PAIR-18-B | business_policies | conflicting | partial | 0.736 | - |
| PAIR-19-A | business_policies | conflicting | pass | 0.981 | - |
| PAIR-19-B | business_policies | conflicting | pass | 0.981 | - |
| PAIR-20-A | business_policies | conflicting | pass | 0.928 | - |
| PAIR-20-B | business_policies | conflicting | partial | 0.750 | - |
| REC-001 | receivables_payables | simple | pass | 0.925 | - |
| REC-002 | receivables_payables | multi_step | pass | 0.875 | - |
| REC-003 | receivables_payables | simple | pass | 0.847 | - |
| REC-004 | receivables_payables | multi_step | partial | 0.671 | - |
| REC-005 | receivables_payables | conflicting | pass | 1.000 | - |
| REC-006 | receivables_payables | conflicting | pass | 1.000 | - |
| REC-007 | receivables_payables | multi_step | pass | 0.968 | - |
| REC-008 | receivables_payables | multi_step | pass | 0.972 | - |
| REC-009 | receivables_payables | conflicting | pass | 0.968 | - |
| REC-010 | receivables_payables | edge | pass | 0.972 | - |
| REC-011 | receivables_payables | multi_step | pass | 0.847 | - |
| REC-012 | receivables_payables | conflicting | pass | 0.968 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
