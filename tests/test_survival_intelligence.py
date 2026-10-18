"""Known-answer arithmetic, no-mutation and tenant boundaries for final integration."""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
import io

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook
from pypdf import PdfReader

from apps.portal.models import Membership, FinancialPolicy, AuditEvent, Scenario, Business, FinancialAccount, Transaction
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.survival_insights import cash_runway, financial_health, payment_priorities, collection_risk
from apps.portal.intelligence.stress_testing import stress_test, StressAssumptions
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.decision_memory import decide
from apps.portal.intelligence.roadmap import recovery_roadmap, update_roadmap
from apps.portal.intelligence.survival import collection_sensitivity


def original_schedule():
    return {'name': 'Recorded schedule', 'actions': []}


def stress_inputs(**kwargs):
    values = StressAssumptions().model_dump(mode='json')
    values.update(kwargs)
    return values


def history(entry, direction='expense', amount=100):
    today = timezone.localdate()
    for offset in range(30):
        entry(date=today-timedelta(days=offset), kind=direction, amount=amount)


def test_runway_independent_known_answer_excludes_financing(business, entry):
    business.opening_balance = 10000
    business.save()
    history(entry)
    # 30 calendar days, 3000 cash out, balance 7000 => burn 100/day => 70 days.
    value = cash_runway(business, build_state(business))
    assert value['days'] == '70.0'
    assert value['daily_net_burn'] == '100.00'
    entry(kind='loan_disbursement', amount=1000)
    value = cash_runway(business, build_state(business))
    assert value['days'] == '80.0' and value['daily_net_burn'] == '100.00'


def test_runway_zero_burn_sparse_and_missing_are_unknown(business, entry):
    entry(amount=100)
    assert not cash_runway(business, build_state(business))['available']
    history(entry)
    history(entry, direction='income')
    value = cash_runway(business, build_state(business))
    assert value['days'] is None and 'positive' in value['reason']
    business.cash_records_complete = False
    business.save()
    state = build_state(business)
    assert not cash_runway(business, state)['available']
    assert financial_health(state)['label'] == 'Insufficient Data'


def test_health_and_protected_payment_priority(business, entry):
    today = timezone.localdate()
    entry(kind='payable', status='pending', amount=1200, category='Salaries & Wages', due_date=today+timedelta(days=3))
    entry(kind='payable', status='pending', amount=100, is_critical=True, due_date=today+timedelta(days=1))
    entry(kind='payable', status='pending', amount=80, category='Marketing', due_date=today+timedelta(days=1))
    state = build_state(business)
    rows = payment_priorities(state)
    assert [row['tier'] for row in rows] == [1, 2, 6]
    assert rows[0]['protected'] and rows[1]['protected']
    assert financial_health(state)['label'] == 'Critical'
    assert 'agreement' in rows[2]['dependency']


def test_partial_delayed_and_missing_collections_have_independent_results(business, entry):
    today = timezone.localdate()
    entry(kind='receivable', status='pending', amount=800, due_date=today+timedelta(days=2))
    entry(kind='payable', status='pending', category='Payroll', amount=1200, due_date=today+timedelta(days=3))
    state = build_state(business)
    before = deepcopy(state)
    result = stress_test(state, original_schedule(), stress_inputs(collection_percent='50'))
    full, partial, adverse = result['cases']
    # 1000 + 800 - 1200 = 600; half receipt gives 200; no receipt gives -200.
    assert [c['timeline']['minimum_balance'] for c in result['cases']] == ['600.00', '200.00', '-200.00']
    assert partial['unrealized_receipts'] == '400.00'
    assert adverse['protected_funding_status'] == 'Timing or funding risk'
    delayed = stress_test(state, original_schedule(), stress_inputs(collection_delay_days=7))
    assert delayed['cases'][1]['timeline']['minimum_balance'] == '-200.00'
    assert delayed['cases'][1]['timeline']['ending_balance'] == '600.00'
    assert state == before and business.transactions.filter(status='paid').count() == 0
    assert full['reserve_goal_met'] and not adverse['reserve_goal_met']
    from apps.portal.intelligence.scenario_engine import evaluate_plan
    plan = evaluate_plan(state, original_schedule())
    partial_case = collection_sensitivity(state, plan, partial_percent=50)[-1]
    assert partial_case['label'] == 'Partial collections'
    assert partial_case['timeline']['ending_balance'] == '200.00'
    assert partial_case['unrealized_receipts'] == '400.00'


def test_revenue_and_expense_adjust_only_typed_eligible_estimates(business, entry):
    today = timezone.localdate()
    entry(kind='income', status='pending', amount=500, due_date=today+timedelta(days=2))
    entry(kind='expense', status='pending', amount=100, due_date=today+timedelta(days=3))
    entry(kind='payable', status='pending', amount=200, due_date=today+timedelta(days=3))
    entry(kind='expense', category='Payroll', status='pending', amount=100, due_date=today+timedelta(days=3))
    result = stress_test(build_state(business), original_schedule(), stress_inputs(revenue_decrease_percent='20', expense_increase_percent='10'))
    # 1000 + 400 - 110 - fixed payable 200 - protected payroll 100 = 990.
    case = result['cases'][1]
    assert case['timeline']['ending_balance'] == '990.00'
    assert case['revenue_events_adjusted'] == 1 and case['expense_events_adjusted'] == 1


def test_supplier_consent_and_no_borrowing_constraints(business, entry):
    due = timezone.localdate()+timedelta(days=2)
    bill = entry(kind='payable', status='pending', amount=1200, due_date=due)
    state = build_state(business)
    moved = stress_test(state, original_schedule(), stress_inputs(supplier_event_id=f'tx:{bill.pk}', supplier_delay_days=3))
    assert moved['available'] and any('agreement' in d.lower() for d in moved['dependencies'])
    bill.refresh_from_db()
    assert bill.due_date == due
    bill.is_critical = True
    bill.save()
    denied = stress_test(build_state(business), original_schedule(), stress_inputs(supplier_event_id=f'tx:{bill.pk}', supplier_delay_days=3))
    assert not denied['available'] and denied['violations']
    denied = stress_test(state, original_schedule(), stress_inputs(allow_borrowing=True, financing_amount='300'))
    assert not denied['available']  # Business borrowing limit is zero.
    FinancialPolicy.objects.create(business=business, max_borrowing=500)
    allowed = stress_test(build_state(business), original_schedule(), stress_inputs(allow_borrowing=True, financing_amount='300', annual_rate='12'))
    assert allowed['available'] and Decimal(allowed['financing_cost']) > 0
    assert Decimal(allowed['deferred_liabilities']) > 300


@pytest.mark.parametrize('changes', [{'collection_percent': '101'}, {'collection_percent': '-1'},
    {'collection_percent': 'NaN'}, {'collection_delay_days': 31}, {'financing_amount': '100'},
    {'stress_collection_percent': 90, 'collection_percent': 50}])
def test_invalid_stress_inputs_fail_closed(changes):
    with pytest.raises(ValueError):
        StressAssumptions.model_validate(stress_inputs(**changes))


def test_receivable_risk_is_descriptive_and_scoped(business, entry):
    today = timezone.localdate()
    invoice = entry(kind='receivable', status='pending', amount=321, due_date=today-timedelta(days=4), reference='INV-test')
    data = collection_risk(business, build_state(business))
    assert data['overdue_count'] == 1 and data['overdue_amount'] == '321.00'
    assert data['invoices'][0]['days_overdue'] == 4
    assert data['invoices'][0]['id'] == invoice.pk
    assert data['invoices'][0]['reserve_gap_increase_if_uncollected'] is None
    assert 'identities' in data['basis']


def accepted(owner, business, entry):
    entry(kind='payable', status='pending', amount=200, due_date=timezone.localdate()+timedelta(days=2))
    item = run_investigation(owner, business.pk, 'Review upcoming commitments without borrowing')
    return decide(owner, business.pk, item.decision.pk, 'accepted', selected_plan=item.result['recommended'])


def test_roadmap_reports_preserve_lifecycle_and_ledger(owner, business, entry):
    decision = accepted(owner, business, entry)
    before = list(business.transactions.values())
    events = decision.events.count()
    roadmap = recovery_roadmap(business, decision)
    key = roadmap['actions'][0]['key']
    for _ in range(2):
        update_roadmap(owner, business.pk, decision.pk, key, 'owner_confirmed', responsible='Operations owner', note='Discussed; actual payment not recorded')
    updated = recovery_roadmap(business, decision)
    assert updated['actions'][0]['status'] == 'owner_confirmed'
    assert AuditEvent.objects.filter(action='roadmap.updated').count() == 1
    decision.refresh_from_db()
    assert decision.state == 'accepted' and decision.events.count() == events
    assert list(business.transactions.values()) == before
    viewer = User.objects.create_user('viewer-survival')
    Membership.objects.create(user=viewer, business=business, role='viewer')
    with pytest.raises(PermissionDenied):
        update_roadmap(viewer, business.pk, decision.pk, key, 'in_progress')
    with pytest.raises(ValidationError):
        update_roadmap(owner, business.pk, decision.pk, 'alien-action', 'owner_confirmed')


def test_six_tabs_and_public_auth_have_real_routes(client, owner, business):
    public = client.get(reverse('landing'))
    assert b'action="/login/"' in public.content
    assert b'id_username' in public.content
    client.force_login(owner)
    for tab in ('overview', 'decisions', 'forecast', 'scenarios', 'loans', 'roadmap'):
        page = client.get(reverse('planning', args=[business.pk]), {'tab': tab})
        assert page.status_code == 200
        assert page.content.count(b'<h1>') == 1
        assert page.content.count(b'aria-current="page"') == 2  # Primary navigation plus active tab.
    token_client = Client(enforce_csrf_checks=True)
    token_client.force_login(owner)
    assert token_client.post(reverse('planning', args=[business.pk])+'?tab=scenarios', {'intent': 'stress'}).status_code == 403


@pytest.mark.parametrize('fmt', ['pdf', 'csv', 'xlsx'])
def test_saved_stress_and_survival_exports(client, owner, business, entry, fmt):
    today = timezone.localdate()
    entry(kind='receivable', status='pending', amount=400, due_date=today+timedelta(days=2))
    client.force_login(owner)
    payload = {'intent': 'stress', 'save_stress': '1', **{f'stress-{key}': value for key, value in
               {'name': 'Independent partial test', **stress_inputs(collection_percent='50')}.items()}}
    response = client.post(reverse('planning', args=[business.pk])+'?tab=scenarios', payload)
    assert response.status_code == 200
    saved = Scenario.objects.get(name='Independent partial test')
    assert saved.result['cases'][1]['timeline']['ending_balance'] == '1200.00'
    for kind, expected in [('scenarios', 'Independent partial test'), ('survival', 'Current financial survival summary')]:
        response = client.get(reverse('reports', args=[business.pk]), {'type': kind, 'format': fmt})
        assert response.status_code == 200
        if fmt == 'pdf':
            text = ' '.join(' '.join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages).split())
        elif fmt == 'xlsx':
            book = load_workbook(io.BytesIO(response.content))
            text = str(list(book.active.values))
            assert all(c.data_type != 'f' for row in book.active for c in row)
        else:
            text = response.content.decode('utf-8-sig')
        assert expected in text


def test_roadmap_and_scenario_sources_do_not_cross_tenants(client, owner, business, entry):
    decision = accepted(owner, business, entry)
    other = User.objects.create_user('other-survival-owner')
    alien = Business.objects.create(name='Other business', currency='USD', opening_balance=1000,
                                    opening_date=timezone.localdate()-timedelta(days=30), cash_records_complete=True)
    Membership.objects.create(user=other, business=alien)
    account = FinancialAccount.objects.create(business=alien, name='Other account')
    Transaction.objects.create(business=alien, account=account, date=timezone.localdate(), kind='receivable', status='pending',
                               currency='USD', amount=50, due_date=timezone.localdate()+timedelta(days=2), description='Other receipt')
    question = run_investigation(other, alien.pk, 'Review my cash')
    alien_decision = decide(other, alien.pk, question.decision.pk, 'accepted', selected_plan=question.result['recommended'])
    client.force_login(owner)
    assert client.get(reverse('planning', args=[business.pk]), {'tab': 'roadmap', 'decision': alien_decision.pk}).status_code == 404
    payload = {'intent': 'stress', 'save_stress': '1', **{f'stress-{key}': value for key, value in
        {'name': 'Forbidden source', 'source_decision': str(alien_decision.pk), **stress_inputs()}.items()}}
    response = client.post(reverse('planning', args=[business.pk])+'?tab=scenarios', payload)
    assert response.status_code == 200 and response.context['stress_form'].errors
    assert not Scenario.objects.filter(name='Forbidden source').exists()
    assert client.post(reverse('roadmap_update', args=[business.pk, alien_decision.pk]), {}).status_code == 404
    viewer = User.objects.create_user('viewer-progress')
    Membership.objects.create(user=viewer, business=business, role='viewer')
    client.force_login(viewer)
    assert client.post(reverse('roadmap_update', args=[business.pk, decision.pk]), {}).status_code == 403
    token_client = Client(enforce_csrf_checks=True)
    token_client.force_login(owner)
    assert token_client.post(reverse('roadmap_update', args=[business.pk, decision.pk]), {}).status_code == 403
