"""Independent known answers for demonstrated benchmark defects, no benchmark expectations imported."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.portal.intelligence.categories import is_payroll_category, is_debt_service_category
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.issue_detection import detect_issues, health_dimensions
from apps.portal.intelligence.scenario_engine import evaluate_plan
from apps.portal.models import RecurringObligation


@pytest.mark.parametrize('label', ['Salaries & Wages', 'Weekly pay run', 'Salary', 'WAGE', 'Pay-roll', 'Payroll - monthly'])
def test_explicit_pay_categories_are_protected(label):
    assert is_payroll_category(label)


@pytest.mark.parametrize('label', ['Employer NI Contributions', 'Employer Pension Contributions', '401(k) Employer Match',
                                  'Salaryman supplies', 'General', 'Wagering supplies'])
def test_unclear_oncosts_and_unrelated_words_are_not_inferred(label):
    assert not is_payroll_category(label)


@pytest.mark.parametrize('label', ['Loan instalment', 'Loan installment', 'Finance instalment', 'Debt repayment', 'Debt service'])
def test_debt_service_vocabulary(label):
    assert is_debt_service_category(label)


def test_payroll_compound_category_cannot_be_delayed_or_reduced(business, entry):
    due = timezone.localdate() + timedelta(days=2)
    row = entry(kind='payable', status='pending', category='Salaries & Wages', amount=500, due_date=due)
    state = build_state(business)
    for action in [{'kind': 'shift', 'event_id': f'tx:{row.pk}', 'days': 3},
                   {'kind': 'reduce', 'event_id': f'tx:{row.pk}', 'amount': '100.00'}]:
        plan = evaluate_plan(state, {'name': 'Attempt', 'actions': [action]})
        assert not plan['feasible'] and plan['violations']
    row.refresh_from_db()
    assert row.amount == Decimal('500') and row.due_date == due


def test_recurring_payroll_and_debt_use_same_vocabulary(business, entry):
    due = timezone.localdate() + timedelta(days=2)
    RecurringObligation.objects.create(business=business, description='Staff', category='Monthly pay run', amount=300, next_due=due)
    entry(kind='payable', status='pending', category='Loan instalment', amount=100, due_date=due)
    state = build_state(business)
    assert any(e['payroll'] for e in state['events'])
    assert 'loan_repayments' in {i['code'] for i in detect_issues(state)}
    assert Decimal(next(h['value'] for h in health_dimensions(state) if h['name'] == 'Financing burden')) == 100


def test_beyond_horizon_is_disclosed_not_added_to_cash(business, entry):
    today = timezone.localdate()
    row = entry(kind='payable', status='pending', amount=27500, due_date=today + timedelta(days=31))
    state = build_state(business)
    assert state['projection']['ending_balance'] == '1000.00'
    assert len(state['beyond_horizon']) == 1
    assert state['beyond_horizon'][0]['id'] == f'tx:{row.pk}'
    assert any('27500.00' in line and 'Beyond horizon' in line for line in state['limitations'])
    assert state['diagnostics']['events_beyond_horizon'] == '1'


def test_blocking_reasons_name_actual_missing_fields(business, entry):
    business.opening_balance = None
    business.cash_records_complete = False
    business.save()
    entry(kind='payable', status='pending', amount=250, due_date=None)
    state = build_state(business)
    assert state['known_cash'] is None and not state['projection']['available']
    assert len(state['blocking_reasons']) == 3
    assert 'opening balance' in state['projection']['reason']
    assert 'no due date' in state['projection']['reason']


def test_accrual_revenue_is_not_deleted_to_match_a_cash_expectation(business, entry):
    today = timezone.localdate()
    entry(kind='income', status='paid', amount=250)
    entry(kind='receivable', status='pending', amount=400, due_date=today + timedelta(days=5))
    entry(kind='expense', amount=100)
    state = build_state(business)
    assert state['trends']['revenue'] == '650.00'
    assert state['known_cash'] == '1150.00'
