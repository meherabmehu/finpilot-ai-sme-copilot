# Baseline forecasting

Forecasts require a known opening balance, actual paid history, and user confirmation that cash records are complete. Up to 90 calendar days of ordinary cash activity yield daily average inflows/outflows. Loan movements and transfers are excluded from the historical repeating baseline. Pending obligations with future due dates and weekly/monthly/yearly recurring commitments are added explicitly. Month-end schedules anchor to the original due day. This conservative composition can overlap recurring obligations in historical averages or explicit pending invoices; the UI discloses the limitation.

Available horizons are 7, 15, 30 and 90 days. Each daily point includes expected inflow, outflow and ending cash. Lowest balance supports threshold monitoring. Sparse histories show their coverage, not an invented confidence score. These are assumption-based baselines, not trained ML predictions or statistical confidence intervals.

Walk-forward evaluation uses four historical weekly cutoffs when at least 30 observations are available, comparing a preceding 60-day net-cash average with realized next-week cash. It reports MAE and WAPE when the denominator is nonzero. This evaluates the historical-average component; it does not reconstruct historical knowledge of invoice schedules. No calibrated intervals are claimed.

Scenarios compare last-30-day activity with explicit revenue/expense percentages, employees and salary, marketing, inventory cash purchase, collection/payment delays, added financing and repayments. Marketing never implies automatic sales uplift. The latest three saved scenarios compare side by side. Saving changes no actual transaction.
