from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_operator_account_is_active_normal_and_idempotent(monkeypatch):
    monkeypatch.setenv("FINPILOT_INITIAL_EMAIL", "new-owner@example.com")
    monkeypatch.setenv("FINPILOT_INITIAL_PASSWORD", "Operator-only-initial-password-87261")
    output = StringIO()
    call_command("provision_owner", stdout=output)
    user = User.objects.get(username="new-owner@example.com")
    assert user.is_active and not user.is_staff and not user.is_superuser
    assert user.check_password("Operator-only-initial-password-87261")
    monkeypatch.setenv("FINPILOT_INITIAL_PASSWORD", "Changed-env-must-not-reset-password-888")
    call_command("provision_owner", stdout=output)
    user.refresh_from_db()
    assert user.check_password("Operator-only-initial-password-87261")
    assert "Operator-only" not in output.getvalue()
    assert not user.membership_set.exists()


@pytest.mark.django_db
def test_pending_unused_account_can_be_provisioned(monkeypatch):
    User.objects.create_user("pending@example.com", email="pending@example.com", is_active=False)
    monkeypatch.setenv("FINPILOT_INITIAL_EMAIL", "pending@example.com")
    monkeypatch.setenv("FINPILOT_INITIAL_PASSWORD", "Operator-only-initial-password-87261")
    call_command("provision_owner")
    assert User.objects.get(username="pending@example.com").is_active


@pytest.mark.django_db
def test_provisioning_refuses_short_password_and_missing_settings(monkeypatch):
    monkeypatch.setenv("FINPILOT_INITIAL_EMAIL", "owner@example.com")
    monkeypatch.delenv("FINPILOT_INITIAL_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("provision_owner")
    monkeypatch.setenv("FINPILOT_INITIAL_PASSWORD", "123")
    with pytest.raises(CommandError):
        call_command("provision_owner")
    assert not User.objects.exists()
