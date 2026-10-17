# Database

Business UUID is the workspace key. Membership links Django users to owner/viewer roles with a unique business/user constraint. FinancialAccount belongs to a business. Transactions include type, amount, status, currency, account, due date, reference and notes. Amounts are positive Decimal values; direction follows transaction type. Imports have unique content/mapping hashes per business and row fingerprints prevent duplicate confirmed rows.

DataImport preserves preview rows and row errors, then confirms atomically under a row lock. Scenario stores assumptions and calculated results separately from transactions. LoanProduct normalizes provider, country, currency, term, rates, fees, source and illustrative status. Conversation/Message stores workspace and user scoped chats. Alert is unique by business/code. AuditEvent records actor, action, object and transaction edit snapshots.

Apply checked-in migrations with `python manage.py migrate`. Financial transactions and audit records use protected business relationships. Voiding excludes entries from summaries while retaining the original row. This is an operating record system, not a statutory double-entry general ledger. RecurringObligation stores dated weekly/monthly/yearly expected cash movements. LoanComparison stores explicit assumptions and calculated illustrations. Dedicated invoice-line and retained report-file tables are not implemented; receivable/payable transaction types represent invoice-level obligations.

Currency and opening date cannot change after entries exist. Account selection is validated against the active workspace. Do not write through the ORM without equivalent service validation: production database RLS and composite tenant/account constraints are not configured.
