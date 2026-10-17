import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings

from config.environment import database_from_url, hosted_domains, secret_from_seed


def test_postgres_url_decodes_credentials_without_mixing_currencies_or_databases():
    result = database_from_url("postgresql://fin%40pilot:pass%2Fword@db.example.com:5433/finance?sslmode=require")
    assert result["ENGINE"] == "django.db.backends.postgresql"
    assert result["USER"] == "fin@pilot"
    assert result["PASSWORD"] == "pass/word"
    assert result["NAME"] == "finance"
    assert result["PORT"] == 5433
    assert result["OPTIONS"]["sslmode"] == "require"
    assert result["CONN_MAX_AGE"] == 0


@pytest.mark.parametrize(
    "value", ["sqlite:///tmp/database", "postgresql://host", "postgresql://host:invalid/db", "https://secret:password@host/db"]
)
def test_invalid_database_url_fails_without_leaking_secrets(value):
    with pytest.raises(ImproperlyConfigured) as exc:
        database_from_url(value)
    assert value not in str(exc.value)
    assert "password" not in str(exc.value)


def test_external_database_tls_cannot_be_downgraded():
    assert database_from_url("postgresql://user:pass@host/db", require_ssl=True)["OPTIONS"]["sslmode"] == "require"
    with pytest.raises(ImproperlyConfigured):
        database_from_url("postgresql://user:pass@host/db?sslmode=disable", require_ssl=True)


def test_render_generated_secret_is_stable_and_long():
    seed = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG="
    assert len(secret_from_seed(seed)) == 128
    assert secret_from_seed(seed) == secret_from_seed(seed)
    assert secret_from_seed(seed) != secret_from_seed(seed + "x")
    with pytest.raises(ImproperlyConfigured):
        secret_from_seed("too-short")


def test_hosted_domains_are_exact_and_deduplicated():
    assert hosted_domains({"RENDER_EXTERNAL_HOSTNAME": "finpilot.onrender.com", "VERCEL_URL": "finpilot.vercel.app"}) == [
        "finpilot.onrender.com",
        "finpilot.vercel.app",
    ]
    with pytest.raises(ImproperlyConfigured):
        hosted_domains({"RENDER_EXTERNAL_HOSTNAME": "*.onrender.com"})


@pytest.mark.django_db
@override_settings(
    SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"), SECURE_REDIRECT_EXEMPT=[r"^health/$"]
)
def test_hosted_ingress_https_does_not_redirect_forever():
    client = Client()
    assert client.get("/", HTTP_X_FORWARDED_PROTO="https").status_code == 200
    assert client.get("/").status_code == 301
    assert client.get("/health/").status_code == 200
