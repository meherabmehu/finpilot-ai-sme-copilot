from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.portal.models import FinancialPolicy
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.question_analysis import analyze_question, question_comparison
from apps.portal.intelligence.scenario_engine import evaluate_plan, compare_plans
from apps.portal.intelligence.decision_memory import decide
from apps.portal.advisor import answer


def test_overdue_question_uses_actual_dates_not_invented_reasons(owner, business, entry, settings):
    today = timezone.localdate()
    overdue = entry(kind='receivable', status='pending', amount=400, reference='invoice-A', due_date=today-timedelta(days=9))
    entry(kind='receivable', status='pending', amount=200, reference='invoice-B', due_date=today+timedelta(days=2))
    entry(kind='receivable', status='pending', amount=100, reference='invoice-C', due_date=today)
    entry(kind='payable', status='pending', amount=1200, due_date=today+timedelta(days=3))
    FinancialPolicy.objects.create(business=business, max_borrowing=1000)
    question = 'Why are customer collections overdue and how can I improve cash flow without taking a loan?'
    item = run_investigation(owner, business.pk, question)
    analysis = item.result['analysis']
    assert analysis['overdue_total'] == '400.00'
    text = str(analysis['sections'])
    assert '9 days overdue' in text and 'invoice-A' in text and 'actual reason for nonpayment is unknown' in text
    assert 'invoice-B' not in text and 'invoice-C' not in text
    assert all(a['kind'] != 'finance' for p in item.result['comparison']['plans'] for a in p['actions'])
    recovery = next(p for p in item.result['comparison']['plans'] if p['name'] == 'Assume overdue recovery in 1 days')
    assert recovery['timeline']['ending_balance'] == '400.00'
    assert item.snapshot['projection']['ending_balance'] == '0.00'  # includes future B 200, but no overdue A
    assert recovery['dependencies']
    assert any(node['id'] == f'tx:{overdue.pk}' for node in item.result['evidence_graph']['nodes'])
    settings.LLM_API_KEY = settings.LLM_MODEL = ''
    result = answer(owner, business, question)
    assert '9 days overdue' in result and 'invoice-A' in result


def test_materially_different_questions_receive_different_evidence(business, entry):
    today = timezone.localdate()
    entry(kind='expense', amount=100, category='Marketing', date=today-timedelta(days=40))
    entry(kind='expense', amount=150, category='Marketing')
    state = build_state(business)
    expenses = analyze_question(state, 'Explain expense growth')
    collections = analyze_question(state, 'Explain overdue customer receivables')
    assert [s['title'] for s in expenses['sections']] == ['Expense growth']
    assert [s['title'] for s in collections['sections']] == ['Overdue collections']
    assert '50.00%' in str(expenses) and 'Marketing' in str(expenses)
    assert 'No recorded overdue receivables' in str(collections)


def test_feasible_reduction_can_leave_reserve_unresolved(business, entry):
    business.opening_balance = Decimal('70860')
    business.low_cash_threshold = Decimal('70000')
    business.save()
    bill = entry(kind='payable', amount=5400, category='Inventory', status='pending', due_date=timezone.localdate()+timedelta(days=3))
    state = build_state(business)
    assert state['projection']['minimum_balance'] == '65460.00'
    result = compare_plans(state, [{'name': 'Ask for scope reduction', 'actions': [{'kind': 'reduce', 'event_id': f'tx:{bill.pk}', 'amount': '2700'}]}])
    plan = result['plans'][0]
    assert plan['feasible'] and not plan['goal_satisfied']
    assert plan['timeline']['minimum_balance'] == '68160.00'
    assert result['unresolved_gap'] == '1840.00'
    assert result['recommendation_status'] == 'reserve unresolved'
    assert 'UNKNOWN' in str(plan['dependencies'])
    shift = evaluate_plan(state, {'name': 'Delay', 'actions': [{'kind': 'shift', 'event_id': f'tx:{bill.pk}', 'days': 7}]})
    assert shift['timeline']['ending_balance'] == '65460.00'
    assert 'ending cash' in str(shift['tradeoffs'])


def test_no_borrowing_constraint_applies_to_custom_modification(owner, business, entry):
    FinancialPolicy.objects.create(business=business, max_borrowing=1000)
    entry(kind='payable', amount=1200, status='pending', due_date=timezone.localdate()+timedelta(days=3))
    item = run_investigation(owner, business.pk, 'Improve cash flow with no borrowing')
    plan = {'name': 'Loan', 'actions': [{'kind': 'finance', 'date': (timezone.localdate()+timedelta(days=1)).isoformat(), 'amount': '300', 'annual_rate': 12}]}
    assert question_comparison(item.snapshot, item.result['analysis'], [plan])['recommended'] is None
    with pytest.raises(ValidationError, match='Borrowing is excluded'):
        decide(owner, business.pk, item.decision.pk, 'modified', modified_plan=plan)
