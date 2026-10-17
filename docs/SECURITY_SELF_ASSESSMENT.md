# Security self-assessment

Covered by automated tests: unauthorized workspace page/API access, report and conversation isolation, viewer write denial, CSRF on switching, authenticated account ownership, allowlisted AI tools and rejection of alternate tenant arguments, malformed uploads, formula exports and transaction audit creation.

Implemented controls also include signed expiring verification, validated passwords, no-store tenant responses, a strict CSP, server-side owner checks, safe parsers and atomic imports. Financial input is untrusted; no arbitrary SQL/tool execution is available.

Open work before production: penetration test, dependency advisory review, shared rate limiting, SMTP delivery testing, live LLM adversarial testing, production PostgreSQL tests, backups/restoration, deletion/retention workflow, operator privacy contact and TLS/proxy validation. RLS and MFA are not claimed. Audit tables are application-managed, not cryptographically tamper-proof.
