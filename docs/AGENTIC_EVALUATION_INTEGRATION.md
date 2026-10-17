# Authoritative agentic evaluation integration

Development-only integration of the supplied Complete package, not an LLM benchmark or a production test.
The original ZIP and all proprietary scenarios/oracles stay outside this public repository. The notice
permits evaluation/review, not open-source redistribution; third-party commercial-sample terms remain
unresolved. No raw dataset or aggregate prior has been copied into the app. Review is supporting only.

## Verified sources

| Archive | Bytes | SHA-256 |
|---|---:|---|
| FinPilot-Agentic-Evaluation-Complete.zip | 1494153 | `77c1fa20b3f173031ad8e16a2720097643ef9d93e7c736e9feaf3e6097f81f25` |
| FinPilot-Agentic-Evaluation-Review.zip | 733793 | `cea3442711c9d3d1c99872c7d3897af9246d22bca9b3359dfba0b50a12b20e95` |

Actual HTTP download bytes, ZIP signature, CRC, exact size/hash, normalized paths, duplicates, symlinks,
special/encrypted files and bounded expanded sizes were checked before extraction. Complete has 264
entries / 9,787,907 expanded bytes; Review 143 / 4,488,948. Isolated source/evidence lives outside app/static.
No archive is needed at server startup. Dependencies are opt-in, `evaluation/agentic/requirements.txt`.

## Execution

1. Obtain the licensed Complete archive and independently verify the above identity. Extract safely outside the checkout/public paths.
2. Install application requirements and development evaluation requirements in a development environment.
3. Standalone: from the extracted root, run `python -m pytest`, `python -m scripts.validate_scenarios`,
   and `python -m scripts.run_evaluation --suite full --adapter reference` / `negative_control`.
4. From this checkout:

```sh
FINPILOT_EVAL_DJANGO=1 python -m evaluation.agentic.run \
  --benchmark-root /private/FinPilot-Agentic-Evaluation \
  --adapter django --suite full --out-dir /private/evaluation-results
```

The CLI checks the pinned source-file SHA-256 manifest before importing external benchmark code.
Default is disposable in-memory SQLite, **not** the configured application database. The SQLite
upper-cent boundary is unsuitable for EDGE-008; use a separately initialized local PostgreSQL cluster:

```sh
initdb -D /private/eval-pg --encoding=UTF8
mkdir -p /private/eval-socket
# Start postgres with this private Unix socket and no TCP listener.
# Create this explicit marker only on YOUR disposable test cluster, never a production socket.
touch /private/eval-socket/FINPILOT-ISOLATED-CLUSTER
# Add: --postgres-socket /private/eval-socket --postgres-port 55433
```

The runner creates a fresh random `test_finpilot_agentic_*` database, explicitly UTF-8, migrates it,
rolls each case back, asserts zero remaining tenants, closes connections, and drops only the newly
created database in `finally`. It never accepts a DATABASE_URL. Connection settings are overridden
before Django setup. No email, provider key, production fixture, scheduler or network tool is used.
CLI exit 3 means blocked, 2 means failed/critical, 0 means no failures (partials are NOT passes).

## Compatibility matrix (current app vs supplied scaffold)

| Contract | Current application path | Mapping / limitations |
|---|---|---|
| Tenant / actor / owner / viewer | models + `authorized_business` | deterministic synthetic UUIDs; membership checked before financial reads; portable actor requested/member aliases map to fixture tenant, never free-text IDs |
| Ledger/accounts/recurrence | actual ORM models | preserve amounts, dates, statuses, archive flags, links, currencies; separate accounts; explicit source IDs only in empty isolated DB; sequences reset for PostgreSQL |
| Policy/reserve | FinancialPolicy / `policy_for` | all declared policy fields; reserve remains Business.low_cash_threshold |
| State / issues / health | `build_state`, `detect_issues`, `health_dimensions` | frozen case date; no oracle arithmetic; unsupported diagnostic fields absent rather than fabricated |
| Investigation / question relevance | `run_investigation` | actual saved snapshot, focus, question-aware alternatives, graph and bounded trace; viewer uses read services after actual persisted-write denial |
| Authored counterfactuals | independent input selector translation → actual PlanSpec/engine | selectors resolve from actual state only; never expected.resolved_candidate_decisions; no silent fallback |
| Financing | `financing_assessment` / actual schedule | supplied actual finance action; no invented lender terms; absent finance candidates remain absent |
| Memory / modification | `decide` | authored lifecycle commands only; actual revalidation, idempotency and stale fingerprints; no snapshot injection |
| Observed outcomes | `monitor_business` → `monitor_decision` | harness explicitly supplies synthetic observed arrivals separately; never presented as payment execution |
| Evidence | actual graph/state references | serialized actual amounts/dates and formula; no expected citations |
| Benchmark score | unchanged external runner/scorer/schema | expected values remain host-only; response whitelists financial inputs; no oracle imports in adapter |
| Unsupported | unavailable app diagnostics, exact prose/hash conventions | not silently given credit; missing calculations score down, case execution errors remain blocked |

## Initial checkpoint

After fixture/date/sequence/backend adapter debugging, but **before application changes**, PostgreSQL
full run: selected 172; executed 171; passed 133; partial 38; failed 0; blocked 1; critical classes 0.
PAIR-17-B cannot resolve payroll from the actual snapshot. Overall **not reportable** because blocked;
0.881848 is the executed-subset mean, not a full score. Raw JSON/Markdown/environment in `evaluation/initial/`.
Earlier runs with adapter bugs are diagnostic only and are not used as baselines.

Important benchmark limitations found by source inspection: the upstream `paired_comparisons` table
contains **oracle expected values**, not measured adapter pair outputs; its lifecycle object also
contains expected script results, and lifecycle responses are not included in the ten-dimension
score. Supplemental independently labelled actual-pair/lifecycle checks are required; do not imply
that the upstream decision-memory pass count alone proves the lifecycle. Original expectations,
scoring and scenario files are not modified. `tested_against_live_application` means actual **local**
Django services executed, never a deployed production instance.

## Final outcome

See AGENTIC_EVALUATION_RESULTS.md for all eight executed suites, 21 measured groups and 83 lifecycle assertions. The initial blocked state above is historical, not the final result. Final code/test branch remains the existing feat/finpilot-platform.
