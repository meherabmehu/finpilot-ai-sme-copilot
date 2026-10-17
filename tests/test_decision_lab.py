from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.scenario_engine import evaluate_plan, compare_plans, suggested_plans
from apps.portal.models import FinancialPolicy


def pressure(entry):
    today = timezone.localdate()
    bill = entry(kind='payable', status='pending', amount=500, due_date=today+timedelta(days=2))
    payroll = entry(kind='payable', category='Payroll', status='pending', amount=800, due_date=today+timedelta(days=3))
    receipt = entry(kind='receivable', status='pending', amount=700, due_date=today+timedelta(days=5))
    return bill, payroll, receipt


def test_three_alternatives_have_known_cash_results(business, entry):
    bill, payroll, receipt = pressure(entry)
    state = build_state(business)
    result = compare_plans(state, suggested_plans(state))
    assert len(result['plans']) >= 3
    by_name = {p['name']: p for p in result['plans']}
    assert by_name['Keep recorded schedule']['timeline']['minimum_balance'] == '-300.00'
    assert by_name['Request earlier collection']['timeline']['minimum_balance'] == '400.00'
    assert by_name['Discuss supplier timing']['timeline']['minimum_balance'] == '200.00'
    assert result['recommended'] != 'Keep recorded schedule'
    assert business.transactions.count() == 3
    bill.refresh_from_db()
    assert bill.due_date == timezone.localdate()+timedelta(days=2)


def test_payroll_and_unknown_event_are_rejected(business, entry):
    bill, payroll, receipt = pressure(entry)
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Unsafe', 'actions': [{'kind': 'shift', 'event_id': f'tx:{payroll.pk}', 'days': 7}]})
    assert not plan['feasible']
    alien = evaluate_plan(state, {'name': 'Alien', 'actions': [{'kind': 'reduce', 'event_id': 'tx:999999', 'amount': 1}]})
    assert not alien['feasible']


def test_split_preserves_total_and_discloses_dependency(business, entry):
    bill, *_ = pressure(entry)
    result = evaluate_plan(build_state(business), {'name': 'Split', 'actions': [{'kind': 'split', 'event_id': f'tx:{bill.pk}', 'amount': 200, 'days': 7}]})
    assert result['feasible']
    assert sum(Decimal(e['amount']) for e in result['events'] if e['id'].startswith(f'tx:{bill.pk}')) == 500
    assert result['dependencies']


def test_conflicting_actions_and_hiding_payments_are_rejected(business, entry):
    bill, *_ = pressure(entry)
    state = build_state(business)
    duplicate = evaluate_plan(state, {'name': 'Conflict', 'actions': [{'kind': 'reduce', 'event_id': f'tx:{bill.pk}', 'amount': 10}]*2})
    assert not duplicate['feasible']
    late = evaluate_plan(state, {'name': 'Hide', 'actions': [{'kind': 'shift', 'event_id': f'tx:{bill.pk}', 'days': 90}]})
    assert not late['feasible']


def test_financing_is_constrained_and_carries_debt_beyond_horizon(business, entry):
    pressure(entry)
    spec = {'name': 'Loan', 'actions': [{'kind': 'finance', 'date': (timezone.localdate()+timedelta(days=1)).isoformat(), 'amount': 400, 'annual_rate': 12, 'months': 12, 'fee': 10}]}
    assert not evaluate_plan(build_state(business), spec)['feasible']
    FinancialPolicy.objects.create(business=business, max_borrowing=1000)
    result = evaluate_plan(build_state(business), spec)
    assert result['feasible'] and Decimal(result['financing_cost']) > 10
    assert Decimal(result['deferred_liabilities']) > 400


def test_restricted_category_changes_ranking_and_missing_data_never_recommends(business, entry):
    pressure(entry)
    FinancialPolicy.objects.create(business=business, restricted_categories=['General'])
    state = build_state(business)
    result = compare_plans(state, suggested_plans(state))
    assert not next(p for p in result['plans'] if p['name'] == 'Discuss supplier timing')['feasible']
    business.cash_records_complete = False
    business.save()
    state = build_state(business)
    assert compare_plans(state, suggested_plans(state))['recommended'] is None
    with pytest.raises(ValueError):
        compare_plans(state, [{'name': 'Bad', 'actions': [{'kind': 'execute_sql'}]}])
