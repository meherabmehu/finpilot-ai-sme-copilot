# Financial engine

`apps/portal/engine.py` uses Decimal and half-up cent rounding. Summary revenue includes income and receivable types minus refunds. Expenses include expense and payable types. Loan principal, repayments and internal transfers are excluded from operating surplus. Paid revenue/receivables/loan proceeds add cash; paid expenses/payables/refunds/repayments subtract it. Pending entries do not affect cash. Transfers have zero business-level net effect.

Cash is verified opening balance plus paid movements since opening date through the selected end date. The reporting window limits activity totals while opening cash remains cumulative. Unknown opening balance stays unknown. Recorded operating surplus is explicitly not audited net profit; inventory, tax, depreciation, loan interest allocation and completeness require further accounting support. Zero revenue yields no margin rather than division by zero.

Loans use the standard reducing-balance monthly annuity formula, with a zero-rate branch and adjusted final installment to clear rounding residue. Fees are upfront and included in total cost. Comparison flags payment above user-provided capacity. Variable rates, effective APR, tax and balloon payments are not modeled.

Known-answer and reconciliation tests exercise loans, zero rates, cash vs revenue, loans, refunds, pending obligations, transfers, date boundaries, archive behavior and scenarios.
