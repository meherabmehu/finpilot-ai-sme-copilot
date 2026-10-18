"""Independent known-answer uncertainty tests and scoped UI/export regressions."""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
import io

import pytest
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook
from pypdf import PdfReader

from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.decision_memory import decide
from apps.portal.intelligence.scenario_engine import evaluate_plan
from apps.portal.intelligence.survival import collection_sensitivity, dashboard_survival
from apps.portal.engine import summary
from apps.portal.models import Business


def scheduled(entry):
    today = timezone.localdate()
    entry(kind='payable', status='pending', category='Payroll', amount=800, due_date=today + timedelta(days=3))
    entry(kind='receivable', status='pending', amount=700, due_date=today + timedelta(days=2))
    entry(kind='payable', status='pending', amount=500, due_date=today + timedelta(days=4))


def test_independent_collection_cash_results_and_immutability(business, entry):
    scheduled(entry)
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Keep dates', 'actions': []})
    before = deepcopy((state, plan))
    cases = collection_sensitivity(state, plan)
    # Cash 1000; +700 day 2, -800 day 3, -500 day 4.
    # Normal min 400; delay/no-receipt min -300. Reserve defaults to 1000.
    assert [c['timeline']['minimum_balance'] for c in cases] == ['400.00', '400.00', '-300.00', '-300.00']
    assert cases[2]['timeline']['ending_balance'] == '400.00'
    assert cases[3]['timeline']['ending_balance'] == '-300.00'
    assert (state, plan) == before
    assert business.transactions.filter(status='paid').count() == 0


def test_delayed_receipts_outside_horizon_are_not_cash(business, entry):
    today = timezone.localdate()
    entry(kind='receivable', status='pending', amount=500, due_date=today + timedelta(days=29))
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Keep dates', 'actions': []})
    cases = collection_sensitivity(state, plan)
    assert cases[1]['timeline']['ending_balance'] == '1500.00'
    assert cases[2]['timeline']['ending_balance'] == '1000.00'
    assert Decimal(cases[2]['receipts_outside_horizon']) == 500
    assert cases[2]['affected_receipts'] == 1


@pytest.mark.parametrize('early,delay', [(-1, 7), (3, 31), ('3', 7), (3, 1.5)])
def test_sensitivity_bounds(business, early, delay):
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Keep dates', 'actions': []})
    with pytest.raises(ValueError):
        collection_sensitivity(state, plan, early, delay)


def test_incomplete_and_no_receipt_cases_are_honest(business, entry):
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'No change', 'actions': []})
    cases = collection_sensitivity(state, plan)
    assert all(c['affected_receipts'] == 0 for c in cases)
    assert len({c['timeline']['ending_balance'] for c in cases}) == 1
    state['complete'] = False
    assert collection_sensitivity(state, plan) == []
    business.opening_balance = None
    business.save()
    state = build_state(business)
    result = dashboard_survival(state, summary(business), [])
    assert result['status'] == 'caution'
    assert 'information' in result['title']
    business.opening_balance = 1000
    business.low_cash_threshold = 0
    business.save()
    due = timezone.localdate() + timedelta(days=2)
    entry(kind='payable', status='pending', due_date=due, amount=1500)
    entry(kind='receivable', status='pending', due_date=due, amount=1000)
    state = build_state(business)
    assert state['projection']['funding_gap'] == '0.00'
    assert state['projection']['intraday_gap'] == '500.00'
    assert dashboard_survival(state, summary(business), [])['status'] == 'caution'


def test_finance_is_not_mislabeled_as_customer_receipts(business, entry):
    today = timezone.localdate()
    entry(kind='loan_disbursement', status='pending', amount=500, due_date=today + timedelta(days=2))
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Original dates', 'actions': []})
    cases = collection_sensitivity(state, plan)
    assert all(c['affected_receipts'] == 0 for c in cases)
    assert all(c['timeline']['ending_balance'] == '1500.00' for c in cases)
    legacy = deepcopy(state)
    legacy.pop('collection_event_ids')
    assert collection_sensitivity(legacy, plan) == []


def test_collections_do_not_remove_protected_obligations(business, entry):
    scheduled(entry)
    state = build_state(business)
    plan = evaluate_plan(state, {'name': 'Original dates', 'actions': []})
    cases = collection_sensitivity(state, plan)
    for case in cases:
        assert sum(Decimal(point['outflow']) for point in case['timeline']['points']) == 1300
    # Intraday order remains visible even when a closing balance meets reserve.
    assert 'payment_first_low' in cases[1]['timeline']['points'][3]


def test_all_steps_and_parameter_recovery_are_read_only(client, owner, business, entry):
    scheduled(entry)
    item = run_investigation(owner, business.pk, 'Can I protect payroll without taking a loan?')
    client.force_login(owner)
    url = reverse('investigation_detail', args=[business.pk, item.pk])
    before = business.transactions.count()
    for step in range(1, 6):
        page = client.get(url, {'step': step, 'early': 'broken', 'delay': 100, 'plan': 999})
        assert page.status_code == 200
        assert page.content.count(b'<h1>') == 1
        assert b'aria-current="step"' in page.content
    assert business.transactions.count() == before
    alien = Business.objects.create(name='Alien tenant', opening_date=timezone.localdate())
    assert client.get(reverse('investigation_detail', args=[alien.pk, item.pk])).status_code == 404


@pytest.mark.parametrize('kind', ['receivables', 'payables'])
@pytest.mark.parametrize('fmt', ['csv', 'xlsx', 'pdf'])
def test_new_exports_contain_real_scoped_records(client, owner, business, entry, kind, fmt):
    today = timezone.localdate()
    wanted = 'receivable' if kind == 'receivables' else 'payable'
    entry(kind=wanted, status='pending', description='Authorized invoice', reference='=HYPERLINK("unsafe")', amount=123)
    entry(kind=wanted, status='paid', description='Paid must be excluded', amount=88)
    entry(kind='expense', status='paid', description='Other kind must be excluded', amount=90)
    client.force_login(owner)
    url = reverse('reports', args=[business.pk])
    response = client.get(url, {'type': kind, 'format': fmt, 'start': today.isoformat(), 'end': today.isoformat()})
    assert response.status_code == 200
    if fmt == 'csv':
        content = response.content.decode('utf-8-sig')
        assert "'=HYPERLINK" in content
    elif fmt == 'xlsx':
        book = load_workbook(io.BytesIO(response.content))
        content = str(list(book.active.values))
        assert all(cell.data_type != 'f' for row in book.active for cell in row)
    else:
        content = ' '.join(' '.join(page.extract_text() for page in PdfReader(io.BytesIO(response.content)).pages).split())
    assert 'Authorized invoice' in content
    assert 'Paid must be excluded' not in content
    assert 'Other kind must be excluded' not in content
    assert 'Unknown' in content


def test_three_business_sections_preserve_old_links(client, owner, business):
    client.force_login(owner)
    for tab in ('overview', 'rules', 'transactions', 'sales', 'expenses', 'upload'):
        page = client.get(reverse('my_business', args=[business.pk]), {'tab': tab})
        assert page.status_code == 200
        assert b'Business profile' in page.content and b'Financial rules' in page.content and b'Data & accounts' in page.content


def test_saved_recovery_step_does_not_show_an_unselected_plan(client, owner, business, entry):
    scheduled(entry)
    item = run_investigation(owner, business.pk, 'Can I protect payroll without a loan?')
    chosen = next(p for index, p in enumerate(item.result['comparison']['plans']) if index > 0 and p['feasible'])
    decide(owner, business.pk, item.decision.pk, target='accepted', selected_plan=chosen['name'])
    client.force_login(owner)
    response = client.get(reverse('investigation_detail', args=[business.pk, item.pk]), {'step': 5, 'plan': 0})
    assert response.status_code == 200
    assert response.context['navigator']['selected']['plan']['name'] == chosen['name']
