# Architecture

Modular Django monolith: templates and vanilla JS use server-rendered, business-aware UUID routes. A DRF read-only summary endpoint exposes the same deterministic engine. Domain code is consolidated under `apps/portal` to avoid many nearly empty Django apps.

Every business route resolves a membership using the authenticated user. Mutation routes additionally require owner role. Viewer access is read-only for business financial data. Private conversations are scoped to both business and user. Switching is a CSRF-protected POST followed by a full navigation; private responses are `no-store` and back/forward cache restores reload. No business data is persisted in browser storage.

PostgreSQL is the production persistence layer. SQLite supports local development. Financial calculations use Decimal. The AI may request only validated, read-only tools bound to server-side workspace context. It cannot supply an alternate tenant or SQL.

The monitoring command is designed for an external scheduler. No Redis/Celery service is needed. HTMX is locally packaged for future partial rendering; current flows use full-page responses to keep tenant state simple.

External references: [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) and [Chart.js integration](https://www.chartjs.org/docs/latest/getting-started/integration.html).
