# Security

Django password hashing, password validation, signed expiring email verification, CSRF middleware, POST logout, secure production cookies, HTTPS redirects, HSTS, clickjacking protection, restrictive CSP and short sessions provide the baseline. Registration/login/reset/advisor POSTs are rate-limited. The local-memory throttle is per process; production must additionally use a shared ingress limit (or shared cache). No proxy forwarding headers are trusted for client identity.

All business routes resolve authenticated membership. Writes require owner role. AI tools reauthorize. Downloads use the same authorized business context. Conversations also constrain user. No-store response headers and full navigation reduce stale tenant state. Model output and uploaded text stay escaped. Spreadsheet exports prefix formula-like cells; XLSX formulas, macros, external links, oversized files and expanded ZIP bombs are rejected. Import confirmation is atomic and idempotent.

Audit snapshots contain financial metadata, so database access and backups require the same protection as records. Production disk encryption, encrypted backups, SMTP, reverse proxy TLS, shared rate limiting, restore exercises and retention policies are operator responsibilities. Do not claim RLS, MFA, malware scanning, compliance certification or bank-grade security: those are not included. Demo accounts must never be deployed with synthetic seed credentials enabled.

Viewer memberships can be provisioned through trusted administration/ORM; invitation and membership-management UI are not included. Default Django admin is restricted to staff and only exposes loan products beyond built-in user administration.


## Agentic continuation controls
Financial policy, investigation creation, decision transitions and manual review require owner membership, POST and CSRF. Historical reads and exports remain business-scoped; export_report itself reauthorizes. Request UUIDs deduplicate investigation submissions; row locks and transition validation protect lifecycle writes. Form recurring links are business-scoped. The ordinary application does not expose snapshot editing.

Business-row serialization now covers policy, record edits/archive, recurring mutations, import confirmation and decision acceptance, with issue refresh rejecting foreign/stale supplied snapshots. Isolated PostgreSQL 17 concurrent import/accept/monitor tests now pass; SQLite alone does not establish row-lock correctness, and these scoped tests do not cover every production race. Admin/ORM paths and external database writers must follow the same discipline.

At the initial checkpoints no pasted credential was used and push was blocked. Subsequently, on explicit user authorization, authentication was supplied only to an ephemeral Git subprocess for a normal push; no credential was stored in repository files, remote URLs or commits. Revoke any real credential shared in chat and configure a replacement through secure environment settings. The branch may auto-deploy; production migration readiness and scheduler must be checked by the operator before enabling release. No separate deployment or production data operation was invoked.


Final hardening adds business-locked/re-authorized import confirmation, explicit same-reference correction rejection, safe concurrency outcomes, manual form submission UUIDs, idempotent void audit, structured report formula escaping and provider argument-object validation. See QUALITY_HARDENING_AUDIT.md and TESTING.md for independent calculations, actual authorization checks and limitations. No full penetration-test or security certification is claimed. The local PostgreSQL test database and DEBUG synthetic demos contain no production records. Scheduler design and provider secret/cost controls are documented separately; neither was activated.
