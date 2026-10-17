# Deployment

The Docker image builds Tailwind and packages Chart.js locally, installs Python dependencies, collects static files and serves Django through Gunicorn as a non-root user. Docker Compose includes PostgreSQL 17 with a persistent volume and healthcheck. Docker configuration is prepared; verify it on a Docker-capable host before release.

1. Copy `.env.example` to `.env`; set a unique random SECRET_KEY (at least 50 characters), database password, domain ALLOWED_HOSTS and SITE_URL.
2. Set DEBUG=false, configure SMTP and any LLM provider. Use a secret manager for production credentials.
3. Run `docker compose build`, then `docker compose run --rm web python manage.py migrate`.
4. Run `docker compose up -d`, behind an HTTPS reverse proxy. The application port is bound to host loopback.
5. Run `docker compose run --rm web python manage.py check --deploy` using production environment settings.
6. Create an admin with `docker compose run --rm web python manage.py createsuperuser` only if needed.

Terminate TLS at a trusted reverse proxy. Configure the app's trusted proxy SSL header only when that proxy strips spoofed incoming headers; the default deliberately does not trust forwarded headers. For local development use DEBUG=true and loopback. Configure CSRF trusted origins if using a separate trusted origin.

Schedule `docker compose exec -T web python manage.py monitor_finances` every hour using cron or Task Scheduler. Alerts are upserted by business/code; each run records an audit outcome. No outbound alerts or email notifications are sent by monitoring.

Backups: use `pg_dump -Fc` to encrypted storage under the deployment operator's access controls. Restore into an isolated PostgreSQL instance with `pg_restore`, run migrations and verify tenant isolation and report totals before switching traffic. Never commit backups or database files. Set retention and deletion schedules with the business owner. `/health/` checks database connectivity.
