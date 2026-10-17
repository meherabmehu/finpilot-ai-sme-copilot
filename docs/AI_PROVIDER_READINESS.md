# AI provider readiness

## Configuration (operator only)
- `LLM_API_KEY`: secret configured in the deployment secret manager, never source, a committed .env or a URL.
- `LLM_BASE_URL`: trusted operator-controlled HTTPS OpenAI-compatible API root (for example a root ending in `/v1`). The adapter appends `/chat/completions`.
- `LLM_MODEL`: model identifier supported by that provider.
- Keep `DEBUG=false` in production, valid HTTPS `SITE_URL`, `ALLOWED_HOSTS`, trusted CSRF origins, PostgreSQL and secure proxy/cookie settings.

The provider must support Chat Completions function tools, JSON Schema parameters, tool-call IDs and tool-role responses. Compatibility with a named vendor/model is not independently verified. No live provider was connected for this hardening work. Without key/model the same financial question receives deterministic analysis, explicitly labeled not generative AI.

## Budgets and cost controls
- HTTP timeout: 12 seconds per request; no redirects.
- At most four provider rounds, eight total tool calls, six calls in a single reply; repeated identical calls are rejected.
- Checked total runtime budget: 40 seconds between requests, not a hard cancellation deadline for an in-flight request.
- `max_tokens=1500` per completion request (up to four completions, plus input/tool/history tokens). Actual provider costs, rate limits and tokenizer behavior vary; no fixed price is promised.
- Up to eight recent messages scoped to both business and user, truncated to 1500 characters each. Questions are bounded to 4000 characters. Deterministic financial context is added; review authorized fields and provider retention/privacy settings before enabling.
- Advisor HTTP POST throttling is per-process local cache (20 sensitive requests / five minutes); configure shared ingress/cache throttling and provider project spend limits for production. These limits are not a complete budget enforcement system.

## Financial and security boundaries
All financial arithmetic comes from Decimal-based deterministic services. Each tool reauthorizes membership and accepts typed allowlisted parameters. No arbitrary SQL, Python, file access, payment, loan application or outbound customer/supplier messaging tool is available. Record descriptions/notes and model output remain untrusted data, not instructions. User no-borrowing intent suppresses borrowing candidates/tools; custom saved modifications are checked too. Unknown nonpayment reasons must not be invented. Tool errors return safe schema/authorization messages, not upstream bodies or secrets.

The LLM remains fallible even with these boundaries: explanation quality is not independently guaranteed. Saved decisions always require explicit owner interaction; provider tools are read-only. Audit events do not store API credentials or upstream response bodies. Financial records and saved evidence still need operator-controlled retention and access protection.

## Isolated test strategy
Use `unittest.mock.patch` on `httpx.Client.post` with fixed test-only replies; never require a paid key for pytest. Existing tests cover authorized tool output, unknown SQL tool denial, invalid array arguments, injected descriptions and no-borrowing financing-tool rejection. Then test an operator-authorized sandbox provider with a dedicated low-limit key and synthetic workspace, verify numerical claims against deterministic output, timeouts/retries, provider errors and absence of cross-tenant context. No such live-provider result is claimed here.
