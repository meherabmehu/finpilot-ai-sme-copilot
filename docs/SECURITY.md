# Security

Django password hashing, password validation, signed expiring email verification, CSRF middleware, POST logout, secure production cookies, HTTPS redirects, HSTS, clickjacking protection, restrictive CSP and short sessions provide the baseline. Registration/login/reset/advisor POSTs are rate-limited. The local-memory throttle is per process; production must additionally use a shared ingress limit (or shared cache). No proxy forwarding headers are trusted for client identity.

All business routes resolve authenticated membership. Writes require owner role. AI tools reauthorize. Downloads use the same authorized business context. Conversations also constrain user. No-store response headers and full navigation reduce stale tenant state. Model output and uploaded text stay escaped. Spreadsheet exports prefix formula-like cells; XLSX formulas, macros, external links, oversized files and expanded ZIP bombs are rejected. Import confirmation is atomic and idempotent.

Audit snapshots contain financial metadata, so database access and backups require the same protection as records. Production disk encryption, encrypted backups, SMTP, reverse proxy TLS, shared rate limiting, restore exercises and retention policies are operator responsibilities. Do not claim RLS, MFA, malware scanning, compliance certification or bank-grade security: those are not included. Demo accounts must never be deployed with synthetic seed credentials enabled.

Viewer memberships can be provisioned through trusted administration/ORM; invitation and membership-management UI are not included. Default Django admin is restricted to staff and only exposes loan products beyond built-in user administration.
