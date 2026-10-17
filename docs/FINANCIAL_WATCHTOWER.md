# Financial Watchtower

The Dashboard computes current issues from authorized records on every read without persisting changes from GET. Saved issue detail links appear when monitoring/investigation has persisted that issue code. Rules include missing data, low cash, dated shortfall/reserve pressure, same-day timing, approaching obligations, overlapping payroll, overdue receipts and expense trends/concentration.

Each card shows severity, rule, amount/date where known, limitations and a path to investigate. No blended health percentage is calculated. Absence of flags does not establish safety.

`python manage.py monitor_finances --business BUSINESS_UUID` persists deduplicated issues and decision reviews. One row per business/code, resolution and reopen counts, timestamps and cooldown are separate from notifications. No messages are sent. Dashboard displays the last invocation, not a claim of continuous operation. Scheduler deployment is not verified.
