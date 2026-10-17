# Agentic architecture

FinPilot remains a Django modular monolith, not an autonomous payment agent. Five primary pages expose an observe → diagnose → investigate → compare → recommend → record → monitor → review workflow.

## Data flow
1. `financial_state.build_state` reconciles the business opening balance and actual paid ledger, expands bounded dated commitments, captures policy and fingerprints the snapshot.
2. `issue_detection.detect_issues` calculates current rules without writes (Dashboard/Planning). `refresh_issues` persists deduplicated issue state under a business lock and rejects foreign/stale snapshots.
3. `investigation.run_investigation` reauthorizes an owner, executes at most six deterministic steps within a checked runtime budget and persists state, evidence, trace and an initial decision. UUID request keys prevent repeat creation.
4. `scenario_engine` validates up to eight plans, each with at most eight actions, using Decimal arithmetic and explicit hard constraints and lexicographic ranking.
5. `decision_memory.decide` records an intention, never accounting execution. Acceptance/modification checks the current state fingerprint. Snapshot JSON is not overwritten by later preference changes.
6. `monitor_finances` invokes monitoring explicitly. Review uses actual paid records at the fixed review date; incomplete records remain awaiting_data. No causal attribution or model training occurs.

## Application surface
- Dashboard: current Watchtower, timeline, last monitoring invocation and active decisions.
- My Business: financial preferences, critical flags and explicit recurring occurrence links.
- Advisor: optional OpenAI-compatible read-only tool adapter and deterministic no-provider explanation; explicit saved-investigation form.
- Planning: Decision Lab, comparison/evidence details, modification builder, decision history and financing sensitivity.
- Reports: decision, investigation/evidence and saved issue exports alongside original exports.

All UUID workspace routes require authenticated membership. Mutations require owner role, POST and CSRF. No sixth navigation page, service, outbound notification or financial execution is introduced.

## Persistence and concurrency
Uses the pre-existing additive migration 0004; no additional migration in this continuation. Business locks serialize policy/record mutation paths, issue refresh, investigation persistence and decision acceptance; decisions are separately locked for transitions. Import confirmation retains its atomic row lock. SQLite tests do not prove PostgreSQL lock behavior; direct administration/ORM writes must follow the same serialization discipline. Services do not enforce cryptographic or database-level snapshot immutability against trusted administrators.
