"""Independent audit regressions; no external keys or production records."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
import json
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
import pytest

from apps.portal.advisor import answer
from apps.portal.intelligence.ai_grounding import scope, grounded_answer, selection_schema
from apps.portal.intelligence.business_domain import domain_context
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.financing import financing_assessment
from apps.portal.intelligence.forecasting import predict, evaluate_series
from apps.portal.intelligence.freshness import snapshot_comparison
from apps.portal.intelligence.grounded_reasoning import ConditionalReasoning, validate_reasoning
from apps.portal.intelligence.investigation import question_context, run_investigation
from apps.portal.intelligence.loan_catalog import discover
from apps.portal.intelligence.question_analysis import analyze_question
from apps.portal.intelligence.question_language import effective_question
from apps.portal.models import Conversation, Message, CollectionContext
from tests.test_competition_upgrade import reply


QUESTIONS = [
    'How much overdue money do I have?', 'Why is my reserve at risk on October 25?',
    'Which supplier payment should I prioritize?', 'Can I protect my reserve without borrowing?',
    'What if the customer pays only half?', 'Why did my restaurant operating expenses increase?',
    'What if sales decline by 20%?', 'Is this loan safe for my business?',
    'What should I do before my supplier deadline?',
    'আমার বকেয়া পাওনা কত?', 'কাস্টমার অর্ধেক টাকা দিলে?', 'ঋণ ছাড়া রিজার্ভ রাখবো কিভাবে?',
    'বিক্রি ২০% কমে গেলে?', 'bokeya paona koto?', 'customer ordhek dile?',
    'loan chara reserve protect korbo kivabe?', 'restaurant khoroch keno bereche?',
]


@pytest.mark.parametrize('question', QUESTIONS)
def test_mandatory_financial_questions_individually(owner, business, settings, question):
    settings.FINPILOT_AI_ENABLED = False
    assert scope(question) == 'financial'
    result = answer(owner, business, question)
    assert 'outside FinPilot' not in result and 'Please clarify which' not in result
    assert result


@pytest.mark.parametrize('question', ['Who won the FIFA World Cup in 2022?', 'ফুটবল বিশ্বকাপ কে জিতেছে?', 'football world cup ke jitse?'])
def test_unrelated_questions_load_no_financial_records(owner, business, settings, question):
    settings.FINPILOT_AI_ENABLED = False
    with patch('apps.portal.intelligence.ai_grounding.build_state', side_effect=AssertionError('No ledger loading')):
        assert 'outside FinPilot' in answer(owner, business, question)


def test_groq_badge_uses_selected_provider(client, owner, business, settings):
    client.force_login(owner)
    settings.FINPILOT_AI_ENABLED = True
    settings.FINPILOT_AI_PROVIDER = 'groq'
    settings.GROQ_API_KEY = 'synthetic-owner-key'
    settings.GROQ_MODEL = 'openai/gpt-oss-20b'
    settings.XAI_API_KEY = settings.LLM_API_KEY = ''
    response = client.get(reverse('advisor', args=[business.pk]))
    assert response.context['configured'] is True
    assert b'AI not configured' not in response.content
    settings.FINPILOT_AI_ENABLED = False
    assert not client.get(reverse('advisor', args=[business.pk])).context['configured']


def test_expense_question_does_not_become_sales_question(business, entry):
    business.category = 'Restaurant'
    business.save()
    today = timezone.localdate()
    entry(kind='expense', category='Food', amount=100, date=today-timedelta(days=35))
    entry(kind='expense', category='Food', amount=160)
    result = analyze_question(build_state(business), QUESTIONS[5])
    assert result['intent']['categories'] == ['expenses']
    text = str(result['sections'])
    assert '60.00%' in text and 'recorded change 60.00' in text
    assert 'Sales and operating sensitivity' not in text
    assert 'not verified operational causes' in text


def test_sales_increase_is_not_presented_as_decline(business, entry):
    entry(amount=100)
    text = str(analyze_question(build_state(business), 'What if sales increase by 20%?'))
    assert 'leaving 120.00' in text and 'revenue increase' in text


def test_half_customer_followup_uses_single_invoice_without_double_count(owner, business, entry, settings):
    settings.FINPILOT_AI_ENABLED = False
    business.opening_balance = 71010
    business.low_cash_threshold = 70000
    business.save()
    today = timezone.localdate()
    entry(kind='payable', status='pending', amount=5400, due_date=today+timedelta(days=6))
    entry(kind='receivable', status='pending', amount=400, due_date=today+timedelta(days=2))
    invoice = entry(kind='receivable', status='pending', amount=3600, due_date=today-timedelta(days=2))
    original = build_state(business)
    c = Conversation.objects.create(user=owner, business=business)
    Message.objects.create(conversation=c, role='user', content='How much overdue money do I have?')
    text = grounded_answer(owner, business, 'What if only half arrives?')
    assert '1800.00' in text and '2190.00' in text and '67810.00' in text
    assert 'date is assumed only' in text
    assert build_state(business)['fingerprint'] == original['fingerprint']
    entry(kind='receivable', status='pending', amount=200, due_date=today-timedelta(days=3))
    text = str(analyze_question(build_state(business), QUESTIONS[4]))
    assert 'Identify the overdue invoice' in text and 'no customer or collection amount has been guessed' in text
    text = str(analyze_question(build_state(business), f'What if half of tx:{invoice.pk} arrives?'))
    assert '1800.00' in text
    assert 'overdue' in effective_question('ordhek dile?', ['bokeya paona koto?'])


def test_debt_proceeds_do_not_establish_repayment_capacity(business, entry):
    entry(kind='income', amount=100)
    entry(kind='expense', amount=80)
    entry(kind='loan_disbursement', amount=100000)
    entry(kind='loan_repayment', amount=5000)
    state = build_state(business)
    assert state['known_cash'] == '96020.00'
    result = financing_assessment(state, 1000, 12, 12)
    assert result['historical_30_day_net_cash'] == '20.00'
    assert result['payment_exceeds_historical_net_cash']
    assert 'higher_rate_cash_impact' in result
    text = str(analyze_question(state, 'Is this loan safe for my business?'))
    assert '20.00' in text and 'Principal, nominal annual rate' in text


def test_long_term_quote_preserves_calculator_without_claiming_simulator_coverage(business):
    result=financing_assessment(build_state(business),10000,12,180)
    assert result['repayment']['months']==180 and result['cash_impact']['remaining_gap'] is None
    assert result['cash_impact']['violations'] and result['higher_rate_cash_impact'] is None


@pytest.mark.parametrize('question',['ঋণ নেবো না রিজার্ভ রাখবো','loan nibo na reserve protect korbo'])
def test_local_language_no_borrowing_constraint(question):
    from apps.portal.intelligence.question_analysis import question_intent
    assert question_intent(question)['no_borrowing']


def test_original_gap_4540_current_3990_remains_historical(owner, business, entry):
    today = timezone.localdate()
    business.opening_balance = 71010
    business.low_cash_threshold = 70000
    business.save()
    bill = entry(kind='payable', status='pending', amount=5950, due_date=today+timedelta(days=6))
    entry(kind='receivable', status='pending', amount=400, due_date=today+timedelta(days=2))
    investigation = run_investigation(owner, business.pk, 'Can I protect my reserve without borrowing?')
    original = deepcopy(investigation.snapshot)
    assert original['projection']['funding_gap'] == '4540.00'
    bill.amount = 5400
    bill.save()
    current = build_state(business)
    comparison = snapshot_comparison(business, original, current)
    assert comparison['original_gap'] == '4540.00' and comparison['current_gap'] == '3990.00' and comparison['stale']
    investigation.refresh_from_db()
    assert investigation.snapshot == original


def test_requested_supplier_date_has_its_own_cash_evidence(business, entry):
    today = date(2026,10,19)
    business.opening_date = date(2026,1,1)
    business.opening_balance = 71010
    business.low_cash_threshold = 70000
    business.save()
    entry(kind='payable', status='pending', amount=5400, date=today, due_date=date(2026,10,25))
    state=build_state(business, as_of=today)
    context=question_context('Why is my reserve at risk on October 25?',state)
    assert context['requested_date']=='2026-10-25'
    assert '65610.00' in str(context['analysis']['sections'][0])
    assert question_context('আমার রিজার্ভ ২৫ অক্টোবর কেন ঝুঁকিতে?',state)['requested_date']=='2026-10-25'


@pytest.mark.parametrize('category,ledger_category', [('Retail','Inventory'),('Restaurant','Food'),('E-commerce','Platform settlement'),
    ('Manufacturing','Raw material'),('Services','Project milestone'),('Wholesale','Customer credit'),('Other','General')])
def test_industry_context_uses_actual_matching_evidence(business, entry, category, ledger_category):
    business.category = category
    business.save()
    row = entry(kind='payable', category=ledger_category, status='pending', due_date=timezone.localdate()+timedelta(days=2))
    context = domain_context(business, build_state(business))
    assert context['type'] == category and context['question']
    assert context['matched_references'] == ([] if category == 'Other' else [f'tx:{row.pk}'])
    assert 'not contractual facts' in context['basis']


def test_conditional_synthesis_is_bounded_and_numerical_claims_rejected():
    facts = {'F1': 'Deterministically computed paid cash'}
    actions = {'review': 'Review actual records.'}
    valid = {'premise_ids': ['F1'], 'relationship': 'liquidity_dependency',
             'hypothesis': 'If the customer confirms the receipt date, earlier collection could reduce payment timing pressure.', 'action_id': 'review'}
    assert 'Unconfirmed operational hypothesis' in validate_reasoning([ConditionalReasoning(**valid)], facts, actions, ['liquidity'])[0]
    for text in ['If the customer pays, cash could reach 99999.', 'If you apply, you may qualify for a loan.',
                 'If the customer pays, you will survive.', 'If inventory is delayed, production could always continue.']:
        with pytest.raises(ValueError):
            validate_reasoning([ConditionalReasoning(**(valid | {'hypothesis':text}))], facts, actions, ['liquidity'])
    with pytest.raises(ValueError):
        validate_reasoning([ConditionalReasoning(**(valid | {'premise_ids':['other-business']}))], facts, actions, ['liquidity'])
    schema = selection_schema()
    assert set(schema['required']) == set(schema['properties'])


def test_groq_synthesis_reaches_answer_with_fact_grounding(owner, business, settings):
    cache.clear()
    settings.FINPILOT_AI_PROVIDER = 'groq'
    settings.FINPILOT_AI_ENABLED = True
    settings.GROQ_API_KEY = 'synthetic-key'
    payload = {'evidence_ids':['F1'], 'action_ids':['review'], 'question_ids':[], 'reasoning':[
        {'premise_ids':['F1'], 'relationship':'liquidity_dependency', 'hypothesis':'If the supplier confirms flexible terms, a timing discussion could reduce pressure on cash.', 'action_id':'review'}]}
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post', return_value=reply(payload)) as post:
        text = answer(owner,business,'What should I do before my supplier deadline?')
    assert 'Unconfirmed operational hypothesis' in text and 'model-generated and unconfirmed' in text
    assert 'intent_categories' in json.loads(post.call_args.kwargs['json']['messages'][1]['content'])


def test_public_program_purpose_restrictions_and_pricing(business):
    rows = discover(business, purpose='inventory working capital')
    fixed = next(r for r in rows if r['product']['id'] == 'us-sba-504')
    assert fixed['constraints'] and fixed['quotation_required']
    micro = next(r for r in rows if r['product']['id'] == 'us-sba-microloan')
    assert micro['product']['maximum'] == '50000' and micro['product']['max_months'] == 84
    assert micro['product']['annual_rate'] is None and '8%' in micro['product']['pricing_basis']


def test_moving_average_matches_original_activity_start_denominator():
    start = date(2025,1,1)
    rows = [(start+timedelta(days=i), Decimal('100') if i==80 else Decimal('0'), Decimal('0')) for i in range(90)]
    expected = predict(rows, 7, 'moving_average')
    assert all(r[1] == Decimal('10') for r in expected)


def test_new_explicit_question_does_not_inherit_unrelated_topic():
    assert effective_question('Is this loan safe for my business?', ['How much overdue money do I have?']) == 'is this loan safe for my business?'
    assert scope('ordhek dile?', ['bokeya paona koto?']) == 'follow_up'


def test_deployment_method_retains_baseline_when_history_does_not_support_candidate():
    from apps.portal.intelligence.forecasting import reviewed_method
    evaluation={'horizons':[{'horizon':7,'folds':4,'wape_unstable':False,'metrics':[
        {'method':'moving_average','mae':'100.00'},{'method':'weekday','mae':'110.00'}]}]}
    with patch('apps.portal.intelligence.forecasting.choose_method',return_value=('weekday','Inner folds favored weekday.')):
        method,reason=reviewed_method([],7,evaluation)
    assert method=='moving_average' and 'Retain baseline' in reason


def test_nested_evaluation_outer_tail_cannot_change_earlier_folds():
    start=date(2024,1,1)
    rows=[(start+timedelta(days=i),Decimal(100+i%11),Decimal(80+i%7)) for i in range(600)]
    before=evaluate_series(rows)
    rows[-1]=(rows[-1][0],Decimal('999999'),Decimal('0'))
    after=evaluate_series(rows)
    for original,changed in zip(before['horizons'],after['horizons']):
        assert original['details'][:-1] == changed['details'][:-1]


def test_solver_respects_owner_reported_disputes_and_promise_dates(business, entry):
    from apps.portal.intelligence.recovery_solver import combined_solutions
    today=timezone.localdate()
    disputed=entry(kind='receivable',status='pending',amount=1000,due_date=today-timedelta(days=3))
    promised=entry(kind='receivable',status='pending',amount=900,due_date=today-timedelta(days=2))
    CollectionContext.objects.create(transaction=disputed,dispute_status='active')
    CollectionContext.objects.create(transaction=promised,promised_date=today+timedelta(days=8))
    state=build_state(business)
    result=combined_solutions(state)
    assert result['excluded_recovery_references']==[f'tx:{disputed.pk}']
    actions=[a for p in result['comparison']['plans'] for a in p['actions'] if a['kind']=='collect']
    assert actions and all(a['event_id']==f'tx:{promised.pk}' and a['date']==str(today+timedelta(days=8)) for a in actions)
    assert build_state(business)['fingerprint']==state['fingerprint']
