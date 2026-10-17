# Decision memory and outcomes

Lifecycle: Proposed → Accepted / Modified / Rejected; Modified → Accepted / Modified / Rejected; Accepted → Monitoring; Monitoring → Evaluated (service only); Evaluated or Rejected → Closed. Invalid transitions are rejected. Closing/acceptance retries are no-ops; identical modification retries do not duplicate events.

Decision history lives in Planning. Detail shows the original question/evidence, immutable-through-application snapshot, selected simulated plan, fixed review date, expected result, feedback, transition events and observed outcome. A stale snapshot banner appears when date, ledger or policy changes. Start a new investigation before accepting stale evidence.

Manual review is owner-only POST. Scheduled review is through `monitor_finances`. At/after review date, complete single-currency cash records and actual paid activity are required. Without them, outcome remains awaiting_data. Expected closing balance is compared with actual review-date cash and actual daily ledger minimum; no decision-caused improvement is inferred. Same-day actual minima are daily-net, not timestamp-ordered bank balances.

The deterministic `policy_feedback` service requires five evaluated outcomes and only suggests a reserve review; it does not change preferences or train a model. It is not yet presented as a user-facing feedback dashboard. No scheduler has been verified. Data completeness is an owner assertion, not a bank reconciliation or audit.
