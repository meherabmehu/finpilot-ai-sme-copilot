# Monitoring operations and scheduler readiness

## What exists and was tested
`python manage.py monitor_finances [--business BUSINESS_UUID]` refreshes internal issue state and reviews accepted/monitoring decisions. It does not create decisions, execute external financial actions or send notifications. A MonitoringRun records start/end timestamps, status, issue count, review count, fingerprint and notification_sent=false. Failures store/log exception type only and the command exits nonzero if a business invocation fails, so an external scheduler can alert its operator. Retry is permitted.

Issue rows are deduplicated by business/code; resolved conditions close and later reopening increments occurrences. Acceptance/monitoring uses business/decision locks. On disposable local PostgreSQL 17, simultaneous preview/confirmation produced one import batch, simultaneous acceptance produced one transition and simultaneous monitoring produced no duplicate decision/lifecycle events or issues. Each explicit monitor invocation still has its own run-history row. These tests are not proof against every production race or admin writer.

Dashboard distinguishes last management-command/service invocation from last manual owner decision review. Neither proves that a deployed schedule is active. Automatic monitoring has NOT been configured or verified in this assignment.

## Deployment-compatible option: external trusted runner
On an already authorized always-available host/container with access to the same database and secrets, run a scheduled job using the same application release and an operator-managed environment. For the prepared Docker Compose deployment, an example cron entry is:

```cron
0 * * * * cd /srv/finpilot && /usr/bin/flock -n /run/lock/finpilot-monitor.lock docker compose exec -T web python manage.py monitor_finances
```

Paths/container availability must be verified by the operator. Avoid overlapping runs with a scheduler-level lock; configure failure-exit alerts and inspect MonitoringRun. Never put database credentials in the cron command/log or run demo seed commands on production. A host cron job is not installed by documentation. Existing serverless request handlers must not run infinite loops or in-process recurring timers.

## Vercel Cron consideration (design only; not activated)
The repository's Vercel function configuration currently allows up to 120 seconds; actual plan limits, cron availability/frequency/cost and scheduler authentication behavior were not inspected and must be checked against the current account. No Vercel configuration, paid plan or production secret was changed.

If an authorized operator verifies feasibility, implement a dedicated disabled-by-default internal route with constant-time bearer-secret verification (`CRON_SECRET` in secret storage, never query parameters), a shared database lease/cooldown, strict method and business/work budgets, safe per-business failure history and ingress limits. A verified platform schedule—not a browser GET—would invoke it. Work exceeding request budget should be chunked/retried by the scheduler without duplicate transitions. Test missing/wrong secrets, concurrent requests, rate limits, timeouts and errors with synthetic records first. This authenticated endpoint is NOT implemented, since plan/scheduler feasibility was not established; the management command is the supported invocation today.
