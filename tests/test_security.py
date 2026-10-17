import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from pydantic import ValidationError
from apps.portal.models import Business, Membership, Conversation, Message, AuditEvent
from apps.portal.advisor import run_tool


@pytest.mark.parametrize("route", ["dashboard", "my_business", "advisor", "planning", "reports", "api_summary"])
def test_cross_tenant_read_rejected(client, business, route):
    outsider = User.objects.create_user("outsider", password="Test-password-919")
    client.force_login(outsider)
    assert client.get(reverse(route, args=[business.pk])).status_code == 404


def test_cross_tenant_report_and_chat_hidden(client, business):
    outsider = User.objects.create_user("outsider", password="Test-password-919")
    conversation = Conversation.objects.create(business=business, user=business.memberships.first().user)
    Message.objects.create(conversation=conversation, role="user", content="Private finances")
    client.force_login(outsider)
    assert client.get(reverse("reports", args=[business.pk]) + "?format=csv").status_code == 404
    response = client.get(reverse("advisor", args=[business.pk]))
    assert response.status_code == 404
    assert b"Private finances" not in response.content


def test_viewer_cannot_write(client, business):
    viewer = User.objects.create_user("viewer")
    Membership.objects.create(business=business, user=viewer, role="viewer")
    client.force_login(viewer)
    assert client.get(reverse("dashboard", args=[business.pk])).status_code == 200
    assert client.post(reverse("transaction_new", args=[business.pk]), {}).status_code == 403
    assert client.post(reverse("my_business", args=[business.pk]), {}).status_code == 403
    assert client.post(reverse("planning", args=[business.pk]) + "?tab=scenarios", {}).status_code == 403


def test_csrf_enforced(owner, business):
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    assert client.post(reverse("switch", args=[business.pk])).status_code == 403


def test_switch_and_private_cache(client, owner, business):
    client.force_login(owner)
    response = client.post(reverse("switch", args=[business.pk]))
    assert response.status_code == 302
    assert client.session["active_business"] == str(business.pk)
    page = client.get(response.url)
    assert page["Cache-Control"] == "no-store, private"
    assert "frame-ancestors" in page["Content-Security-Policy"]


def test_tool_authorization_and_injection(owner, business):
    outsider = User.objects.create_user("outsider")
    from django.http import Http404

    with pytest.raises(Http404):
        run_tool(outsider, business.pk, "get_business_overview", {})
    with pytest.raises(ValidationError):
        run_tool(owner, business.pk, "get_business_overview", {"business_id": "another-tenant"})
    with pytest.raises(PermissionDenied):
        run_tool(owner, business.pk, "execute_sql", {"query": "DROP TABLE"})


def test_foreign_account_rejected(client, owner, business):
    from apps.portal.models import FinancialAccount

    other = Business.objects.create(name="Other", country="US", currency="USD", category="Retail", opening_date=timezone.localdate())
    account = FinancialAccount.objects.create(business=other, name="Other")
    client.force_login(owner)
    response = client.post(
        reverse("transaction_new", args=[business.pk]),
        {
            "date": timezone.localdate(),
            "description": "Invalid",
            "amount": "20",
            "kind": "income",
            "category": "Sales",
            "account": account.pk,
            "status": "paid",
        },
    )
    assert response.status_code == 200
    assert not business.transactions.exists()


def test_transaction_creates_audit(client, owner, business):
    client.force_login(owner)
    response = client.post(
        reverse("transaction_new", args=[business.pk]),
        {
            "date": timezone.localdate(),
            "description": "Valid",
            "amount": "20",
            "kind": "income",
            "category": "Sales",
            "account": business.accounts.first().pk,
            "status": "paid",
        },
    )
    assert response.status_code == 302
    event = AuditEvent.objects.get(action="transaction.created")
    assert event.details["after"]["amount"] == "20"


def test_api_requires_login(client, business):
    assert client.get(reverse("api_summary", args=[business.pk])).status_code == 403
