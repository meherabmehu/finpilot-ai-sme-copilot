from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone
from apps.portal.engine import summary, forecast, simulate, loan_schedule, money, backtest


def test_emi_known_answer():
    result = loan_schedule(100000, 12, 12)
    assert result["payment"] == "8884.88"
    assert result["schedule"][-1]["balance"] == "0.00"
    assert sum(Decimal(r["principal"]) for r in result["schedule"]) == Decimal("100000")


def test_zero_interest_and_rounding():
    result = loan_schedule(100, 0, 3, 5)
    assert result["schedule"][-1]["payment"] == "33.34"
    assert result["total_cost"] == "105.00"
    assert money("1.005") == Decimal("1.01")


@pytest.mark.parametrize("principal,rate,months", [(0, 12, 12), (-1, 0, 1), (100, -1, 12), (100, 1, 0), ("NaN", 1, 12)])
def test_bad_loan_inputs(principal, rate, months):
    with pytest.raises(ValueError):
        loan_schedule(principal, rate, months)


def test_recorded_summary_distinguishes_profit_and_cash(business, entry):
    entry(amount=100)
    entry(kind="expense", amount=30)
    entry(kind="receivable", amount=50, status="pending")
    entry(kind="payable", amount=20, status="pending")
    entry(kind="loan_disbursement", amount=1000)
    entry(kind="loan_repayment", amount=100)
    entry(kind="transfer", amount=700)
    entry(kind="refund", amount=10)
    data = summary(business)
    assert data["revenue"] == 140
    assert data["expenses"] == 50
    assert data["operating_surplus"] == 90
    assert data["cash"] == 1960
    assert data["receivables"] == 50
    assert data["payables"] == 20


def test_date_boundary_and_archive(business, entry):
    today = timezone.localdate()
    entry(date=today - timedelta(days=30), amount=90)
    entry(amount=10)
    entry(amount=100, archived=True)
    entry(date=today + timedelta(days=1), amount=1000)
    assert summary(business, today)["revenue"] == 10


def test_missing_baseline_never_fabricates(business, entry):
    assert not forecast(business)["available"]
    business.opening_balance = None
    business.save()
    entry()
    assert summary(business)["cash"] is None
    assert not forecast(business)["available"]


def test_forecast_scheduled_obligation(business, entry):
    today = timezone.localdate()
    entry(date=today - timedelta(days=9), amount=100)
    entry(kind="payable", amount=500, status="pending", due_date=today + timedelta(days=2))
    result = forecast(business, 7)
    assert result["available"]
    assert result["history_days"] == 10
    assert result["ending_balance"] == "670.00"
    assert len(result["points"]) == 8


def test_scenario_does_not_change_actuals(business, entry):
    entry(amount=1000)
    entry(kind="expense", amount=500)
    result = simulate(business, {"revenue_change": "20", "employees": 1, "salary": 100, "inventory": 50})
    assert result["revenue"] == "1200.00"
    assert result["expenses"] == "600.00"
    assert result["cash_delta"] == "50.00"
    assert summary(business)["revenue"] == 1000


def test_insufficient_backtest_is_explicit(business):
    assert backtest(business)["mae"] is None
