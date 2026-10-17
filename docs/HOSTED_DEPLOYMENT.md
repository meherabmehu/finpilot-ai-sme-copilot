# Hosted deployment: full Django backend and PostgreSQL

The repository includes a Render Blueprint (`render.yaml`) for a Docker web service and a separate PostgreSQL database, plus Vercel's Django entrypoint configuration. Responsive assets are served with the same Django app. No separate frontend or CORS setup is necessary.

## Render

Connect the Render integration to an authorized workspace. Use the Blueprint at branch `feat/finpilot-platform`, or create equivalent resources through the connected integration. Both resources are explicitly configured as free for evaluation; do not silently substitute a paid plan if unavailable. Render's free database expires after its documented evaluation period and free web services can sleep. Upgrade/backup decisions belong to the operator.

The Blueprint provisions a private PostgreSQL connection through `DATABASE_URL`, a random `SECRET_KEY_SEED`, and a one-worker Gunicorn service. The random seed is deterministically hashed to a stable long Django signing key; no secret is committed. Hostname and HTTPS origins are read from `RENDER_EXTERNAL_HOSTNAME`. The start command runs migrations before starting Gunicorn and honors `PORT`.

Use one instance for this startup migration strategy. For paid/multi-instance services, migrate in a pre-deploy job instead. Database cache/shared ingress throttling and scheduled monitoring remain operator setup tasks.

## Vercel

Connect the authorized Vercel account/team, import this repository and branch, and configure `DEBUG=false`, a unique `SECRET_KEY` of at least 50 characters (or a high-entropy `SECRET_KEY_SEED`), and `DATABASE_URL` for a persistent PostgreSQL integration. External database TLS is required by default on Vercel. The production and deployment hostnames are accepted from Vercel environment variables. Set `SITE_URL` to the canonical production HTTPS URL if needed.

Vercel discovers the WSGI entrypoint from `pyproject.toml`; its `[project]` metadata declares Python runtime dependencies. The build runs migrations through the direct database URL when the provider supplies one, and application requests use the pooled URL. Static assets are already compiled and committed, and Vercel runs collectstatic for Django. Function region is Singapore to match the provisioned database. Do not select a static-only framework preset or replace the database with ephemeral SQLite.

## Email and AI

External signup verification and password-reset email delivery require a real email backend/provider. Console email is for local development and does not deliver email to users. Confirm the selected hosting plan permits the provider's network connection; Render free web services block standard SMTP ports. No SMTP or AI credentials are included or fabricated. Live AI additionally requires `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL`.

## Acceptance after credentials are connected

Verify the provider deploy reaches a successful state, `/health/` returns 200 from a live database, the landing and static assets return 200, HTTPS does not loop, CSRF-protected forms work, and an authorized user can create a business and records that persist across redeployment. Run responsive checks using `BROWSER_BASE_URL` against the verified live URL with an authorized test account. Do not expose credentials in logs or copy the local demo database to hosting.

Prepared configuration is not proof of a completed deployment. The live URL must come from the provider's successful deployment result.

Sources: [Render Django](https://render.com/docs/deploy-django), [Render Blueprint specification](https://render.com/docs/blueprint-spec), [Render free-plan limits](https://render.com/docs/free), [Vercel Django](https://vercel.com/docs/frameworks/full-stack/django).
