# FinPilot Agentic Evaluation - policy suite

Generated (UTC): 2026-10-17T21:44:45+00:00
Adapter: **django** (connected)
Rubric version: 1.0.0
Selected cases: 40
Duration: 2.375 s

> Full run against a connected adapter; the overall weighted score is reportable.

## Summary

| Metric | Value |
|---|---|
| executed | 40 |
| passed | 23 |
| partial | 17 |
| failed | 0 |
| blocked | 0 |
| skipped | 0 |
| overall weighted score | 0.8723 |
| critical failure cases | 0 |
## Per-category results

| Category | Cases | Executed | Passed | Partial | Failed | Blocked | Mean score | Critical failures |
|---|---|---|---|---|---|---|---|---|
| business_policies | 40 | 40 | 23 | 17 | 0 | 0 | 0.8723 | - |

## Per-dimension means

| Dimension | Weight | Cases scored | Cases excluded | Mean score |
|---|---|---|---|---|
| cash_accuracy | 15 | 36 | 4 | 1.0000 |
| liquidity_reasoning | 12 | 40 | 0 | 0.9875 |
| payment_timing | 10 | 12 | 28 | 1.0000 |
| financing_arithmetic | 10 | 10 | 30 | 0.5000 |
| policy_compliance | 14 | 40 | 0 | 0.5250 |
| plan_selection | 10 | 40 | 0 | 1.0000 |
| evidence_reference | 10 | 40 | 0 | 1.0000 |
| uncertainty_disclosure | 9 | 40 | 0 | 0.8472 |
| data_quality_handling | 5 | 0 | 40 | - |
| tenant_isolation_safety | 5 | 0 | 40 | - |

## Paired business-policy comparisons

| Pair | Distinguishing constraint | Dimension | Expect | Outcome per member |
|---|---|---|---|---|
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

## Cases

| Scenario | Category | Difficulty | Verdict | Score | Critical failures |
|---|---|---|---|---|---|
| PAIR-01-A | business_policies | conflicting | partial | 0.762 | - |
| PAIR-01-B | business_policies | conflicting | pass | 0.938 | - |
| PAIR-02-A | business_policies | conflicting | partial | 0.757 | - |
| PAIR-02-B | business_policies | conflicting | pass | 0.800 | - |
| PAIR-03-A | business_policies | conflicting | partial | 0.757 | - |
| PAIR-03-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-04-A | business_policies | conflicting | partial | 0.757 | - |
| PAIR-04-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-05-A | business_policies | conflicting | pass | 1.000 | - |
| PAIR-05-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-06-A | business_policies | conflicting | partial | 0.762 | - |
| PAIR-06-B | business_policies | conflicting | partial | 0.762 | - |
| PAIR-07-A | business_policies | conflicting | pass | 1.000 | - |
| PAIR-07-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-08-A | business_policies | conflicting | pass | 0.971 | - |
| PAIR-08-B | business_policies | conflicting | partial | 0.757 | - |
| PAIR-09-A | business_policies | conflicting | pass | 0.963 | - |
| PAIR-09-B | business_policies | conflicting | pass | 0.963 | - |
| PAIR-10-A | business_policies | conflicting | pass | 0.891 | - |
| PAIR-10-B | business_policies | conflicting | pass | 0.891 | - |
| PAIR-11-A | business_policies | conflicting | pass | 0.945 | - |
| PAIR-11-B | business_policies | conflicting | pass | 0.945 | - |
| PAIR-12-A | business_policies | conflicting | partial | 0.762 | - |
| PAIR-12-B | business_policies | conflicting | partial | 0.762 | - |
| PAIR-13-A | business_policies | conflicting | partial | 0.757 | - |
| PAIR-13-B | business_policies | conflicting | pass | 0.800 | - |
| PAIR-14-A | business_policies | conflicting | partial | 0.762 | - |
| PAIR-14-B | business_policies | conflicting | pass | 0.938 | - |
| PAIR-15-A | business_policies | conflicting | pass | 0.963 | - |
| PAIR-15-B | business_policies | conflicting | pass | 0.963 | - |
| PAIR-16-A | business_policies | conflicting | partial | 0.787 | - |
| PAIR-16-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-17-A | business_policies | conflicting | partial | 0.757 | - |
| PAIR-17-B | business_policies | conflicting | partial | 0.757 | - |
| PAIR-18-A | business_policies | conflicting | partial | 0.771 | - |
| PAIR-18-B | business_policies | conflicting | partial | 0.757 | - |
| PAIR-19-A | business_policies | conflicting | pass | 1.000 | - |
| PAIR-19-B | business_policies | conflicting | pass | 1.000 | - |
| PAIR-20-A | business_policies | conflicting | pass | 0.944 | - |
| PAIR-20-B | business_policies | conflicting | partial | 0.789 | - |

---

Expected values in every case were produced by the independent Decimal oracles in `oracles/`, which are validated by hand-calculated known answers and invariant tests. The implementation under test was never used to generate them.
