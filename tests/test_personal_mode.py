"""Independent consumer arithmetic, authorization, no-write simulation and SME regressions."""
from datetime import timedelta
from decimal import Decimal
import io
import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import Client

from apps.portal.models import Business,Membership,PersonalProfile,FinancialAccount,Transaction,Scenario
from apps.portal.intelligence.personal_finance import overview,simulate,demo_state,personal_state,question_analysis
from apps.portal.advisor import answer
from apps.portal.personal_forms import PersonalOnboardingForm
from tests.test_competition_upgrade import reply


@pytest.fixture
def personal(owner):
    today=timezone.localdate()
    w=Business.objects.create(name='Synthetic freelancer',mode='personal',category='Personal',country='BD',currency='BDT',opening_balance=18000,
        opening_date=today,low_cash_threshold=8000,cash_records_complete=True)
    Membership.objects.create(business=w,user=owner)
    PersonalProfile.objects.create(workspace=w,income_type='freelance',savings_target=5000)
    account=FinancialAccount.objects.create(business=w,name='Personal cash')
    for kind,amount,offset,critical,category in [('receivable',10000,4,False,'Freelance income'),('payable',12000,7,True,'Rent')]:
        Transaction.objects.create(business=w,account=account,date=today,kind=kind,amount=amount,status='pending',due_date=today+timedelta(days=offset),
            currency='BDT',description='Synthetic '+category,category=category,is_critical=critical)
    return w


def test_existing_workspaces_default_to_business(business):
    assert business.mode=='business' and not PersonalProfile.objects.filter(workspace=business).exists()


def test_independent_cash_and_reserve_without_expected_income(personal):
    state=personal_state(personal)
    result=overview(state)
    assert result['cash']=='18000.00' and result['bills']=='12000.00'
    assert result['expected_income']=='10000.00' and result['after_bills']=='6000.00'
    assert result['safe_to_spend']==result['savings_room']=='0.00'
    assert result['baseline']['ending_balance']=='16000.00'
    assert result['without_future_income']['funding_gap']=='2000.00'
    assert result['priorities'][0]['essential']


@pytest.mark.parametrize('days,ending,gap',[(7,'16000.00','2000.00'),(14,'16000.00','2000.00'),(30,'6000.00','2000.00')])
def test_delays_change_timing_without_inventing_receipts(personal,days,ending,gap):
    state=personal_state(personal)
    ref=state['collection_event_ids'][0]
    result=simulate(state,'delay',delay_days=days,income_reference=ref)
    assert result['simulated']['ending_balance']==ending and result['simulated']['funding_gap']==gap
    assert bool(result['excluded_beyond_horizon'])==(days==30)
    assert personal_state(personal)['fingerprint']==state['fingerprint']


@pytest.mark.parametrize('percent,expected',[(10,'15000.00'),(20,'14000.00'),(30,'13000.00')])
def test_reduced_income_only_changes_unreceived_assumptions(personal,percent,expected):
    state=personal_state(personal)
    result=simulate(state,'reduced',reduction=percent)
    assert result['simulated']['ending_balance']==expected
    assert result['starting_cash']=='18000.00'
    assert personal_state(personal)['fingerprint']==state['fingerprint']


@pytest.mark.parametrize('kind',['expense','savings'])
def test_expense_or_savings_assumption_is_not_actual_money_movement(personal,kind):
    state=personal_state(personal)
    result=simulate(state,kind,amount='5000',event_date=timezone.localdate()+timedelta(days=3))
    assert result['simulated']['ending_balance']=='11000.00' and result['ending_difference']=='-5000.00'
    assert personal_state(personal)['known_cash']=='18000.00'
    assert personal.transactions.count()==2


@pytest.mark.parametrize('value',['-1','0','0.001','NaN','Infinity','1000000001'])
def test_scenario_input_amounts_fail_closed(personal,value):
    with pytest.raises(ValueError):
        simulate(personal_state(personal),'expense',amount=value,event_date=timezone.localdate()+timedelta(days=2))


def test_other_workspace_income_reference_cannot_be_simulated(personal,business,entry):
    row=entry(kind='receivable',status='pending',due_date=timezone.localdate()+timedelta(days=1))
    with pytest.raises(ValueError):
        simulate(personal_state(personal),'delay',income_reference=f'tx:{row.pk}')


def test_unknown_records_do_not_turn_into_zero_spending_guarantee(personal):
    personal.cash_records_complete=False
    personal.save()
    data=overview(personal_state(personal))
    assert data['safe_to_spend'] is None and data['after_bills'] is None
    with pytest.raises(ValueError):
        simulate(personal_state(personal),'reduced',reduction=20)


def test_negative_cash_is_explicit_and_zero_income_is_not_invented(personal):
    personal.opening_balance=-50
    personal.save()
    personal.transactions.filter(kind='receivable').delete()
    result=overview(personal_state(personal))
    assert result['cash']=='-50.00' and result['expected_income']=='0.00'
    assert result['safe_to_spend']=='0.00' and result['after_bills']=='-12050.00'


def test_consumer_onboarding_creates_only_explicit_obligations(client,owner):
    client.force_login(owner)
    today=timezone.localdate()
    payload={'name':'My life','income_type':'freelance','country':'BD','currency':'BDT','available_cash':'18000','reserve':'8000',
        'savings_target':'5000','expected_income':'10000','income_date':today+timedelta(days=4),'monthly_essentials':'12000','bills_date':today+timedelta(days=7),'complete':'on'}
    response=client.post(reverse('personal_new'),payload)
    assert response.status_code==302
    w=Business.objects.get(name='My life')
    assert w.mode=='personal' and w.personal_profile.savings_target==Decimal('5000')
    assert overview(personal_state(w))['cash']=='18000.00'
    assert w.transactions.count()==1 and w.recurring_obligations.count()==1
    assert not w.transactions.filter(status='paid').exists()
    assert b'Essential monthly bills' in client.get(reverse('my_business',args=[w.pk])).content


def test_optional_income_requires_a_date():
    form=PersonalOnboardingForm({'name':'Test','income_type':'student','country':'BD','currency':'BDT','available_cash':'0','reserve':'0','expected_income':'100','complete':'on'})
    assert not form.is_valid() and 'income_date' in form.errors


@pytest.mark.parametrize('route',['dashboard','my_business','planning','advisor','reports'])
def test_personal_pages_use_consumer_mode(client,owner,personal,route):
    client.force_login(owner)
    response=client.get(reverse(route,args=[personal.pk]))
    assert response.status_code==200 and b'Personal Mode' in response.content
    assert b'>My Money<' in response.content
    if route in ('dashboard','planning','my_business','reports'):
        assert b'Supplier &amp; other payments' not in response.content


def test_cross_user_personal_data_isolation(client,personal):
    outsider=User.objects.create_user('another-person','another@example.test','test-only')
    client.force_login(outsider)
    for route in ('dashboard','my_business','planning','advisor','reports'):
        assert client.get(reverse(route,args=[personal.pk])).status_code==404
    assert client.post(reverse('my_business',args=[personal.pk]),{'reserve':'0','savings_target':'0','complete':'on'}).status_code==404


def test_viewer_cannot_save_scenarios_or_preferences(client,personal):
    viewer=User.objects.create_user('personal-viewer','viewer@example.test','test-only')
    Membership.objects.create(business=personal,user=viewer,role='viewer')
    client.force_login(viewer)
    assert client.post(reverse('my_business',args=[personal.pk]),{'reserve':'0','savings_target':'0','complete':'on'}).status_code==403
    state=personal_state(personal)
    response=client.post(reverse('planning',args=[personal.pk]),{'scenario':'delay','delay_days':'7','income_reference':state['collection_event_ids'][0],'save':'on'})
    assert response.status_code==403 and not personal.scenarios.exists()


def test_personal_scenario_save_does_not_touch_actual_ledger(client,owner,personal):
    client.force_login(owner)
    state=personal_state(personal)
    response=client.post(reverse('planning',args=[personal.pk]),{'scenario':'delay','delay_days':'7','income_reference':state['collection_event_ids'][0],'save':'on'})
    assert response.status_code==200 and b'Baseline vs your scenario' in response.content
    assert personal.scenarios.get().result['simulated']['funding_gap']=='2000.00'
    assert personal_state(personal)['fingerprint']==state['fingerprint']


@pytest.mark.parametrize('question',['Can I afford to spend 5,000 BDT this week?','What happens if my freelance payment arrives seven days late?',
    'How much can I save this month?','Which bill should I prioritize?','Why is my emergency reserve at risk?',
    'How can I handle an unexpected medical expense?'])
def test_personal_advisor_uses_personal_evidence(owner,personal,settings,question):
    settings.FINPILOT_AI_ENABLED=False
    text=answer(owner,personal,question)
    assert 'outside FinPilot' not in text and 'Please clarify which' not in text
    assert 'supplier' not in text.lower() and 'payroll' not in text.lower()
    assert '18000.00' in text or '12000.00' in text or '0.00' in text


def test_personal_groq_context_never_contains_other_workspace(owner,personal,business,entry,settings):
    entry(amount=999999,description='BUSINESS SECRET')
    settings.FINPILOT_AI_ENABLED=True
    settings.FINPILOT_AI_PROVIDER='groq'
    settings.GROQ_API_KEY='synthetic-test-key'
    from django.core.cache import cache
    cache.clear()
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post',return_value=reply({'evidence_ids':['F1'],'action_ids':['review'],'question_ids':[],'reasoning':[]})) as post:
        text=answer(owner,personal,'How much can I save this month?')
    payload=str(post.call_args.kwargs['json'])
    context=json.loads(post.call_args.kwargs['json']['messages'][1]['content'])
    assert '999999' not in payload and 'BUSINESS SECRET' not in payload and context['business_type']=='Personal'
    assert 'Groq-assisted' in text


@pytest.mark.parametrize('fmt',['pdf','csv','xlsx'])
def test_personal_exports_real_financial_values(client,owner,personal,fmt):
    client.force_login(owner)
    response=client.get(reverse('reports',args=[personal.pk])+f'?format={fmt}')
    assert response.status_code==200
    if fmt=='pdf':
        from pypdf import PdfReader
        text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)
    elif fmt=='xlsx':
        from openpyxl import load_workbook
        text=str(list(load_workbook(io.BytesIO(response.content)).active.values))
    else:
        text=response.content.decode('utf-8-sig')
    assert '18000' in text.replace(',','') and '6000' in text.replace(',','')
    assert 'Personal' in text and 'spending' in text


def test_public_demo_is_stateless_and_does_not_call_ai(client,db):
    before=(Business.objects.count(),Transaction.objects.count(),Scenario.objects.count(),User.objects.count())
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post',side_effect=AssertionError('Public demo never spends API quota')):
        assert client.get(reverse('personal_demo')).status_code==200
        result=client.post(reverse('personal_demo'),{'scenario':'delay','delay_days':'7','income_reference':'demo-income'})
        assert result.status_code==200 and b'2000.00' in result.content
        assert client.post(reverse('personal_demo'),{'question':'How much can I save?'}).status_code==200
        assert client.get(reverse('personal_demo')+'?format=pdf').content.startswith(b'%PDF')
    assert before==(Business.objects.count(),Transaction.objects.count(),Scenario.objects.count(),User.objects.count())


def test_public_demo_csrf_protection():
    c=Client(enforce_csrf_checks=True)
    assert c.post(reverse('personal_demo'),{'scenario':'reduced','reduction':'20'}).status_code==403


def test_direct_personal_calculations_and_demo_have_same_known_answer():
    state=demo_state()
    assert overview(state)['after_bills']=='6000.00'
    assert simulate(state,'delay',income_reference='demo-income',delay_days=7)['simulated']['funding_gap']=='2000.00'


def test_ai_explicit_spending_amount_has_deterministic_answer(personal):
    data=question_analysis(personal_state(personal),'Can I afford to spend 5,000 BDT this week?')
    assert '5000.00' in data['sections'][0]['lines'][0] and 'Not supported' in data['sections'][0]['lines'][0]


def test_actual_income_entry_recalculates_personal_cash(client,owner,personal):
    client.force_login(owner)
    response=client.post(reverse('transaction_new',args=[personal.pk]),{'date':timezone.localdate(),'description':'Actual personal receipt',
        'amount':'1000','kind':'income','category':'Salary','account':personal.accounts.first().pk,'status':'paid'})
    assert response.status_code==302
    assert personal_state(personal)['known_cash']=='19000.00'


def test_personal_question_does_not_convert_foreign_currency(personal):
    data=question_analysis(personal_state(personal),'Can I spend 50 USD?')
    assert data['sections'][0]['title']=='Currency needs clarification'


def test_overdue_essential_bill_keeps_original_deadline(personal):
    bill=personal.transactions.get(kind='payable')
    bill.due_date=timezone.localdate()-timedelta(days=2)
    bill.save()
    priority=overview(personal_state(personal))['priorities'][0]
    assert priority['date']==str(bill.due_date) and priority['priority']=='Overdue essential'


def test_due_today_recurring_total_is_not_silently_ignored(client,owner,personal):
    from apps.portal.personal_forms import PersonalRecurringForm
    form=PersonalRecurringForm({'description':'Rent','amount':'100','direction':'outflow','next_due':timezone.localdate(),'frequency':'monthly'})
    assert not form.is_valid() and 'next_due' in form.errors
    client.force_login(owner)
    response=client.get(reverse('my_business',args=[personal.pk]))
    assert b'Save recurring bill or income' in response.content


def test_linked_personal_paid_bill_suppresses_same_recurring_occurrence(client,owner,personal):
    from apps.portal.models import RecurringObligation
    due=timezone.localdate()+timedelta(days=2)
    recurring=RecurringObligation.objects.create(business=personal,description='Utilities',amount=100,category='Utilities',direction='outflow',next_due=due)
    client.force_login(owner)
    response=client.post(reverse('transaction_new',args=[personal.pk]),{'date':timezone.localdate(),'description':'Early paid utilities','amount':'100',
        'kind':'expense','category':'Utilities','account':personal.accounts.first().pk,'status':'paid','due_date':due,'recurring_obligation':recurring.pk})
    assert response.status_code==302
    state=personal_state(personal)
    assert state['known_cash']=='17900.00'
    assert not any(e['id'].startswith(f'rec:{recurring.pk}:') for e in state['events'])
