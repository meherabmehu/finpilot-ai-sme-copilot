from decimal import Decimal
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from apps.portal.models import Business, Membership, FinancialAccount, Transaction


@pytest.fixture
def owner(db):
    return User.objects.create_user("owner@example.com", "owner@example.com", "Strong-test-password-982", first_name="Alex")


@pytest.fixture
def business(owner):
    from datetime import timedelta

    b = Business.objects.create(
        name="Test Shop",
        category="Retail",
        country="US",
        currency="USD",
        opening_balance=1000,
        opening_date=timezone.localdate() - timedelta(days=180),
        cash_records_complete=True,
    )
    Membership.objects.create(business=b, user=owner)
    FinancialAccount.objects.create(business=b, name="Bank")
    return b


@pytest.fixture
def entry(business):
    def create(**kwargs):
        values = {
            "business": business,
            "account": business.accounts.first(),
            "date": timezone.localdate(),
            "description": "Sale",
            "amount": Decimal("100"),
            "currency": "USD",
            "kind": "income",
            "status": "paid",
        }
        values.update(kwargs)
        return Transaction.objects.create(**values)

    return create
