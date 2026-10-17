# Accounting and import semantics

Recorded revenue includes dated income and earned receivables, less refunds, regardless of paid/pending status. Operating expenses include expenses and supplier payables, paid or pending. Operating surplus is recorded revenue minus those operating expenses, not audited net profit. Loan proceeds and repayments affect cash, not operating revenue/expense. Paid ledger movements reconcile opening cash; pending receivables never become cash until the same entry is marked paid. Do not add a second income entry for settlement of an already-recorded receivable. Cash inflows/outflows include financing movements; they are not identical to revenue or operating expense.

For the three-row example (250 paid income, 100 paid expense, 400 pending receivable): recorded revenue 650; expenses 100; operating surplus 550; cash change +150; outstanding receivables 400. This is the existing earned/recorded operating basis, not a new accounting formula.

## Import identity and corrections
- Exact file bytes + column mapping have a business-scoped SHA-256 digest. Re-upload returns the original batch; confirmed previews clearly say Already imported and cannot confirm again.
- A repeated confirmation returns 0 without a second audit event. Business and import locks serialize previews/confirmation. Existing business/digest and business/fingerprint database constraints remain.
- A nonblank reference, transaction type and currency identify an event within a business. A matching reference is blocked even if a corrected amount changes the row hash. Use unique event references (including line/installment identity if needed) for distinct events. References are not assumed to be unique customer names.
- Without references, full normalized content fingerprints detect ambiguous matching records. Equal legitimate events can be distinguished with unique reference values, including within one file; no global cross-business identity is used.
- Files are append-only batches, not an upsert interface. Correct existing records using edit/void so audit history survives. A changed file with overlapping rows is rejected atomically, not partially imported. A file with entirely new references is new data, so review it carefully; the application cannot infer real-world duplication across arbitrary changed references.
- Confirmation revalidates identities and business setup after preview. Currency/opening-date or intervening record changes reject the entire batch. CSV/XLSX limits, formula rejection and tenant/owner controls remain unchanged.
