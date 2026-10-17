#!/bin/sh
set -eu

# Migrate before starting the single free-tier instance. On paid/multi-instance
# hosting, move migrations to the provider's pre-deploy job instead.
python manage.py migrate --noinput
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
