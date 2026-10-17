from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.issue_detection import refresh_issues, health_dimensions
from apps.portal.models import FinancialIssue, RecurringObligation


def test_dated_timeline_reconciles_without_historical_double_count(business, entry):
    today = timezone.localdate()
    entry(amount=200, kind='expense', date=today-timedelta(days=1))
    bill = entry(amount=500, kind='payable', status='pending', due_date=today+timedelta(days=2))
    payroll = entry(amount=600, kind='payable', category='Payroll', status='pending', due_date=today+timedelta(days=3))
    entry(amount=700, kind='receivable', status='pending', due_date=today+timedelta(days=5))
    state = build_state(business)
    assert state['known_cash'] == '800.00'
    assert state['projection']['minimum_balance'] == '-300.00'
    assert state['projection']['ending_balance'] == '400.00'
    assert state['projection']['first_shortfall'] == (today+timedelta(days=3)).isoformat()
    assert f'tx:{payroll.pk}' in state['projection']['points'][3]['refs']
    assert f'tx:{bill.pk}' in state['projection']['points'][2]['refs']
    assert not business.investigations.exists()


def test_linked_recurring_occurrence_is_not_counted_twice(business, entry):
    due = timezone.localdate()+timedelta(days=3)
    obligation = RecurringObligation.objects.create(business=business, description='Payroll', category='Payroll', amount=400, next_due=due)
    entry(amount=400, kind='payable', status='pending', category='Payroll', recurring_obligation=obligation, due_date=due)
    state = build_state(business)
    assert len(state['events']) == 1
    assert state['projection']['ending_balance'] == '600.00'


def test_overdue_receipts_are_not_invented_and_incomplete_data_blocks(business, entry):
    entry(kind='receivable', status='pending', amount=500, due_date=timezone.localdate()-timedelta(days=1))
    state = build_state(business)
    assert state['projection']['ending_balance'] == '1000.00'
    assert len(state['overdue']) == 1
    business.cash_records_complete = False
    business.save()
    assert not build_state(business)['projection']['available']
    business.cash_records_complete = True
    business.opening_balance = None
    business.save()
    assert build_state(business)['known_cash'] is None


def test_mixed_currencies_block_projection(business, entry):
    entry(currency='EUR')
    state = build_state(business)
    assert state['known_cash'] is None
    assert not state['complete']


def test_detection_deduplicates_resolves_and_reopens(business, entry):
    bill = entry(kind='payable', status='pending', amount=1200, due_date=timezone.localdate()+timedelta(days=2))
    refresh_issues(business)
    issue = FinancialIssue.objects.get(business=business, code='negative_cash')
    surfaced = issue.surfaced_at
    refresh_issues(business)
    issue.refresh_from_db()
    assert issue.surfaced_at == surfaced
    assert issue.occurrence_count == 1
    bill.archived = True
    bill.save()
    refresh_issues(business)
    issue.refresh_from_db()
    assert issue.status == 'resolved'
    bill.archived = False
    bill.save()
    refresh_issues(business)
    issue.refresh_from_db()
    assert issue.status == 'open' and issue.occurrence_count == 2


def test_health_dimensions_are_explicit_not_a_blended_score(business, entry):
    entry(kind='expense', amount=300)
    dimensions = health_dimensions(build_state(business))
    assert len(dimensions) == 8
    assert all('rule' in dimension and 'basis' in dimension for dimension in dimensions)
    assert Decimal(next(d['value'] for d in dimensions if d['name'] == 'Cash coverage (days)')) == 70


def test_same_day_estimates_disclose_payment_first_risk(business, entry):
    due = timezone.localdate()+timedelta(days=2)
    entry(kind='receivable', status='pending', amount=900, due_date=due)
    entry(kind='payable', status='pending', amount=1500, due_date=due)
    state = build_state(business)
    assert state['known_cash'] == '1000.00'
    assert state['projection']['minimum_balance'] == '400.00'
    assert state['projection']['intraday_gap'] == '500.00'
    assert 'assumed' in state['events'][0]['basis']


def test_refresh_rejects_foreign_and_stale_snapshots(business, entry):
    import pytest
    state = build_state(business)
    entry(amount=10)
    with pytest.raises(ValueError, match='stale'):
        refresh_issues(business, state)
    state['business_id'] = 'not-this-business'
    with pytest.raises(ValueError, match='belong'):
        refresh_issues(business, state)


def test_fingerprint_includes_opening_date(business):
    before = build_state(business)
    business.opening_date -= timedelta(days=1)
    business.save()
    assert build_state(business)['fingerprint'] != before['fingerprint']
