# Portable evaluation package adapter specification

Historical specification (superseded by [the actual integration](AGENTIC_EVALUATION_INTEGRATION.md) and [measured results](AGENTIC_EVALUATION_RESULTS.md)). The remainder records the earlier pre-package design, not current integration status.

Original status: specification only. `FinPilot-Agentic-Evaluation-Complete.zip` is not present, has not been inspected, and is not claimed integrated. Current fixes and independent known-answer tests do not depend on it.

## Boundary and execution
A future adapter must read versioned JSON/CSV fixture data, never execute code from the archive. Validate ZIP traversal/expanded size before extracting, reject extra schema fields, and run only against a disposable test database. Do not load production financial records. Do not install arbitrary evaluator dependencies or model artifacts automatically.

Suggested case schema (`finpilot-evaluation/v1`):

```json
{
  "schema_version": "finpilot-evaluation/v1",
  "case_id": "overdue-no-borrowing-001",
  "as_of": "2026-10-18",
  "business": {"currency": "USD", "opening_balance": "1000.00", "opening_date": "2026-09-01", "reserve": "200.00", "records_complete": true},
  "policy": {"max_borrowing": "0.00", "horizon_days": 30},
  "transactions": [
    {"logical_id": "customer-A", "date": "2026-10-01", "kind": "receivable", "status": "pending", "due_date": "2026-10-09", "amount": "400.00", "reference": "invoice-A"},
    {"logical_id": "supplier-A", "date": "2026-10-18", "kind": "payable", "status": "pending", "due_date": "2026-10-21", "amount": "1200.00", "category": "Supplies"}
  ],
  "question": "Improve overdue collections without taking a loan",
  "plans": [{"name": "Assumed recovery", "actions": [{"kind": "collect", "event": "customer-A", "amount": "400.00", "date": "2026-10-19"}]}],
  "expected": {"known_cash": "1000.00", "baseline_minimum": "-200.00", "overdue_total": "400.00", "plan_minimum": "200.00", "borrowing_recommended": false}
}
```

Financial values must be Decimal strings, dates ISO and assertions independently derived. Reference oracle amounts must not be copied from FinPilot's own results. Use one fixture business/account/owner per case and a second tenant for adversarial access cases. Map logical event identifiers to created row IDs: `tx:{pk}` for recorded transactions and `rec:{pk}:{occurrence_date}` for recurrence occurrences. Never assume a database primary key from an external package is authorized.

## Existing entry points
- `build_state(business, as_of=...)`: cash, completeness, timeline and snapshot.
- `detect_issues(state)`: non-mutating rule output.
- `analyze_question(state, question)` and `question_comparison(state, analysis, plans)`: deterministic intent/evidence and bounded alternatives.
- `evaluate_plan(state, spec)`: simulated arithmetic and action constraints; `goal_satisfied` is separate from `feasible`.
- `run_investigation(owner, business.pk, question, request_key=...)`: persistence, evidence and retry behavior. Patch timezone.localdate in isolated tests when freezing its as-of date, because this function does not accept an as_of argument.
- `decide(...)`, `monitor_decision(decision, as_of=...)`: lifecycle and fixed-date actual-vs-expected results.
- Authorized Django test client routes for owner/viewer, cross-tenant, CSRF and export checks.

Compare money exactly at cent precision, statuses and violation categories deterministically, and provenance references structurally. Compare explanatory requirements by meaning/required fields, not arbitrary prose exact matches. Test time ordering, missing data and no-borrowing negatives, not just the winning plan name. Reject case plans beyond existing bounds (eight plans/eight actions; horizon 7–90). Unknown account/currency/loan terms must remain unknown, never invented to satisfy an oracle.

## Result handoff
Emit per-case expected/actual values, pass/fail/unsupported, versions, date basis and limitations. Mark unavailable fields or unimplemented package features unsupported rather than silently passing. Preserve the external package checksum/version separately. No independent-package score or competition certification is claimed until the archive is supplied, validated and executed.
