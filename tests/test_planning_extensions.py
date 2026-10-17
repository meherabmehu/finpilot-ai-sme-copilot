from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from apps.portal.models import RecurringObligation, Membership, LoanComparison
from apps.portal.engine import forecast
from apps.portal.advisor import run_tool


def test_cash_completeness_is_required(business, entry):
    entry()
    business.cash_records_complete = False
    assert not forecast(business)["available"]


def test_recurring_projection_never_changes_actuals(business, entry):
    today = timezone.localdate()
    entry(date=today - timedelta(days=9), amount=100)
    RecurringObligation.objects.create(
        business=business,
        description="Monthly lease",
        amount=250,
        direction="outflow",
        next_due=today + timedelta(days=3),
        frequency="monthly",
    )
    result = forecast(business, 7)
    assert result["ending_balance"] == "920.00"
    assert business.transactions.count() == 1


def test_recurring_owner_workflow_and_viewer_denial(client, owner, business):
    client.force_login(owner)
    response = client.post(
        reverse("recurring_add", args=[business.pk]),
        {
            "description": "Rent",
            "amount": "200",
            "direction": "outflow",
            "next_due": timezone.localdate() + timedelta(days=4),
            "frequency": "monthly",
        },
    )
    assert response.status_code == 302
    item = business.recurring_obligations.get()
    viewer = User.objects.create_user("viewer")
    Membership.objects.create(user=viewer, business=business, role="viewer")
    client.force_login(viewer)
    assert client.post(reverse("recurring_disable", args=[business.pk, item.pk])).status_code == 403
    client.force_login(owner)
    assert client.post(reverse("recurring_disable", args=[business.pk, item.pk])).status_code == 302
    item.refresh_from_db()
    assert not item.active


def test_financing_save_and_export(client, owner, business):
    client.force_login(owner)
    response = client.post(
        reverse("planning", args=[business.pk]) + "?tab=loans",
        {"amount": 10000, "annual_rate": 12, "months": 12, "fees": 50, "monthly_capacity": 2000, "save_comparison": 1},
    )
    assert response.status_code == 200
    assert LoanComparison.objects.filter(business=business).count() == 1
    response = client.get(reverse("reports", args=[business.pk]) + "?type=financing&format=csv")
    assert b"10000" in response.content
    assert b"loan offers or approvals" in response.content


def test_more_read_only_tools(owner, business, entry):
    entry(kind="expense", amount=40, category="Rent")
    expenses = run_tool(owner, business.pk, "get_expense_breakdown", {})
    assert expenses["categories"]["Rent"] == 40
    result = run_tool(owner, business.pk, "simulate_financial_scenario", {"marketing": "10"})
    assert result["expenses"] == "50.00"
    assert business.transactions.count() == 1
    loan = run_tool(owner, business.pk, "compare_financing_options", {"principal": "100", "annual_rate": 0, "months": 2})
    assert loan["payment"] == "50.00"
