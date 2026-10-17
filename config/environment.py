"""Validate hosted configuration without exposing connection strings in errors."""

import hashlib
from urllib.parse import parse_qs, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured


def database_from_url(value, require_ssl=False):
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname or not parsed.path.strip("/"):
            raise ValueError
        port = parsed.port or 5432
        options = {"connect_timeout": 10}
        query = parse_qs(parsed.query)
        sslmode = query.get("sslmode", ["require" if require_ssl else "prefer"])[0]
        if sslmode not in ("disable", "allow", "prefer", "require", "verify-ca", "verify-full"):
            raise ValueError
        if require_ssl and sslmode in ("disable", "allow", "prefer"):
            raise ValueError
        options["sslmode"] = sslmode
        if "channel_binding" in query:
            binding = query["channel_binding"][0]
            if binding not in ("disable", "prefer", "require"):
                raise ValueError
            options["channel_binding"] = binding
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname,
            "PORT": port,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": options,
        }
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured("DATABASE_URL must be a valid PostgreSQL URL with compatible TLS settings.") from exc


def secret_from_seed(seed):
    # Render generates 32 random bytes encoded as 44 characters. Derive a stable
    # signing key long enough for Django's deployment checks; entropy stays 256 bits.
    if len(seed) < 43:
        raise ImproperlyConfigured("SECRET_KEY_SEED must contain at least 43 characters of random secret material.")
    return hashlib.sha512(seed.encode("utf-8")).hexdigest()


def hosted_domains(environ):
    domains = []
    for key in ("RENDER_EXTERNAL_HOSTNAME", "VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_URL"):
        value = environ.get(key, "").strip()
        if not value:
            continue
        if any(char in value for char in ("/", "\\", ":", " ", "*")):
            raise ImproperlyConfigured(f"{key} must be a plain hostname.")
        domains.append(value)
    return list(dict.fromkeys(domains))
