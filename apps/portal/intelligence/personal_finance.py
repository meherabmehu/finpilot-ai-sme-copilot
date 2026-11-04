"""Consumer cash decisions reuse the dated Decimal timeline; no ledger writes."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal
import hashlib
import json
import re

from django.utils import timezone
from ..engine import money
from .financial_state import build_state,cash_timeline
from .question_language import normalize_question

ZERO=Decimal('0')


def overview(state):
    available=state['complete'] and state['known_cash'] is not None
    bills=[e for e in state['events'] if e['direction']=='outflow']
    expected=[e for e in state['events'] if e['id'] in state['collection_event_ids']]
    reserve=Decimal(state['policy']['reserve'])
    conservative=cash_timeline(Decimal(state['known_cash']),bills,date.fromisoformat(state['as_of']),state['policy']['horizon_days'],reserve) if available else {'available':False}
    room=money(max(ZERO,Decimal(conservative['minimum_balance'])-reserve)) if available else None
    risk=('Review missing records' if not available else 'Essential bills exceed recorded cash' if Decimal(conservative['minimum_balance'])<0 else
          'Reserve depends on future income' if Decimal(conservative['funding_gap'])>0 else 'Reserve covered under recorded bills')
    priorities=[]
    for event in sorted(bills,key=lambda e:(not e.get('critical',False),e['date'],e['id'])):
        original=next((r['date'] for r in state['overdue'] if f"tx:{r['id']}"==event['id']),event['date'])
        priorities.append({**event,'date':original,'essential':event.get('critical',False),'priority':'Overdue essential' if original<state['as_of'] and event.get('critical') else 'Essential' if event.get('critical') else 'Review due date',
            'note':'Check the contract and consequences before discussing any date change. No postponement permission is inferred.'})
    return {'cash':state['known_cash'],'currency':state['currency'],'available':available,'bills':str(money(sum((Decimal(e['amount']) for e in bills),ZERO))),
        'expected_income':str(money(sum((Decimal(e['amount']) for e in expected),ZERO))),
        'overdue_income':str(money(sum((Decimal(e['amount']) for e in state['overdue'] if e['direction']=='inflow' and e['date']<state['as_of']),ZERO))),
        'expected_ending':state['projection'].get('ending_balance'),
        'after_bills':conservative.get('ending_balance'),'reserve':str(money(reserve)),
        'safe_to_spend':str(room) if room is not None else None,'savings_room':str(room) if room is not None else None,
        'conditional_headroom':str(money(max(ZERO,Decimal(state['projection']['minimum_balance'])-reserve))) if available else None,
        'risk':risk,'next_action':'Confirm expected income timing before committing more money.' if available and Decimal(conservative['funding_gap'])>0 else
          'Review completeness and add missing bills.' if not available else 'Keep the reserve separate and review bills before spending.',
        'priorities':priorities,'baseline':state['projection'],'without_future_income':conservative,
        'basis':'Safe-to-spend and savings room exclude every future receipt and preserve the lowest dated bill balance and emergency reserve. Future income is never available cash. No unrecorded daily spending is assumed.'}


def personal_state(business):
    if business.mode!='personal':
        raise ValueError('A personal workspace is required.')
    return build_state(business)


def simulate(state,kind,amount=None,event_date=None,delay_days=7,reduction=20,income_reference=''):
    if not state['complete'] or state['known_cash'] is None:
        raise ValueError('Confirm complete cash records and dated bills before simulating.')
    events=deepcopy(state['events'])
    today,end=date.fromisoformat(state['as_of']),date.fromisoformat(state['end_date'])
    if kind=='delay':
        if int(delay_days) not in (7,14,30):
            raise ValueError('Choose a seven, fourteen or thirty-day delay.')
        event=next((e for e in events if e['id']==income_reference and e['id'] in state['collection_event_ids']),None)
        if not event:
            raise ValueError('Select an expected income reference from this workspace.')
        event['date']=(date.fromisoformat(event['date'])+timedelta(days=int(delay_days))).isoformat()
        assumptions=f"Assume only {income_reference} arrives {delay_days} days later, on {event['date']}. This is not a confirmed payment date."
    elif kind in ('expense','savings'):
        value=Decimal(str(amount)) if amount is not None else ZERO
        if not value.is_finite() or not ZERO<value<=1000000000 or money(value)!=value:
            raise ValueError('Enter a positive bounded amount with at most two decimal places.')
        day=date.fromisoformat(str(event_date))
        if not today<day<=end:
            raise ValueError('Choose a future date inside the displayed planning horizon.')
        events.append({'id':'hypothetical:'+kind,'date':str(day),'amount':str(money(value)),'direction':'outflow',
            'category':'Savings assumption' if kind=='savings' else 'Unexpected expense assumption','critical':kind=='expense'})
        assumptions=f"Assume a {state['currency']} {money(value)} {'savings transfer out of available spending cash' if kind=='savings' else 'extra expense'} on {day}. No money is actually moved."
    elif kind=='reduced':
        if int(reduction) not in (10,20,30):
            raise ValueError('Choose a ten, twenty or thirty percent reduction.')
        count=0
        for event in events:
            if event['id'] in state['collection_event_ids']:
                event['amount']=str(money(Decimal(event['amount'])*(1-Decimal(reduction)/100)))
                count+=1
        if not count:
            raise ValueError('Add dated expected income before testing an income reduction.')
        assumptions=f'Assume every dated expected income in this horizon is {reduction}% lower; already received money and bills stay unchanged.'
    else:
        raise ValueError('Choose a supported personal scenario.')
    result=cash_timeline(Decimal(state['known_cash']),events,today,state['policy']['horizon_days'],Decimal(state['policy']['reserve']))
    outside=[{'reference':e['id'],'date':e['date'],'amount':e['amount']} for e in events if e['date']>state['end_date']]
    return {'kind':'personal_v1','scenario':kind,'currency':state['currency'],'as_of':state['as_of'],'source_fingerprint':state['fingerprint'],
        'starting_cash':state['known_cash'],'baseline':state['projection'],'simulated':result,'assumptions':assumptions,
        'ending_difference':str(money(Decimal(result['ending_balance'])-Decimal(state['projection']['ending_balance']))),
        'excluded_beyond_horizon':outside,'goal_satisfied':Decimal(result['funding_gap'])==0,
        'next_step':'Check receipt timing and discuss options before essential bill deadlines; no bill can be assumed legally postponable.' if Decimal(result['funding_gap'])>0 else
          'The reserve holds under these dated assumptions. Confirm receipts and missing living costs before acting.',
        'basis':'Hypothetical comparison only. Actual ledger and savings balances are unchanged; overdue income is not assumed recovered.'}


def question_analysis(state,question):
    text=normalize_question(question)
    data=overview(state)
    lines=[f"Available paid cash: {data['cash'] or 'Unknown'} {state['currency']}; emergency reserve: {data['reserve']}.",
        f"Bills in this dated horizon: {data['bills']} {state['currency']}; cash after bills without future receipts: {data['after_bills'] or 'Unknown'}.",
        f"Conservative spending/savings room: {data['safe_to_spend'] if data['safe_to_spend'] is not None else 'Unknown'} {state['currency']}. Future receipts are excluded and missing daily expenses remain unknown."]
    sections=[{'title':'Personal cash, bills and reserve','lines':lines}]
    if 'overdue' in text:
        sections.insert(0,{'title':'Overdue expected personal income','lines':[
            f"Recorded overdue income: {data['overdue_income']} {state['currency']}. Only unpaid income due before {state['as_of']} is overdue; due-today and future income are separate.",
            'It is not added to available cash or assumed received tomorrow. Confirm the amount and a realistic receipt date before revising your plan.']})
    if any(w in text for w in ('prioriti','bill','essential','medical')):
        sections.insert(0,{'title':'Essential bills and due dates','lines':[
            f"{e['id']}: {e['amount']} {state['currency']} due {e['date']}; essential: {e['essential']}. {e['note']}" for e in data['priorities'][:8]] or ['No dated bill is recorded; add missing obligations before deciding payment priority.']})
    amount=re.search(r'\b(?:spend|save|expense(?: of)?)\s+(?:[A-Z]{3}\s+)?([\d,]+(?:\.\d{1,2})?)',text,re.I)
    foreign=[c for c in ('bdt','usd','gbp','eur','inr','sgd','cad','aud','aed','brl') if re.search(r'\b'+c+r'\b',text) and c!=state['currency'].lower()]
    if foreign:
        sections.insert(0,{'title':'Currency needs clarification','lines':[f"This workspace uses {state['currency']}. The question names another currency; no exchange rate, conversion or affordability amount has been inferred."]})
        return {'intent':{'categories':['liquidity'],'no_borrowing':True,'combined':False,'reserve_target':None},'sections':sections,'overdue_total':'0.00'}
    if amount:
        value=money(Decimal(amount.group(1).replace(',','')))
        allowed=data['safe_to_spend'] is not None and value<=Decimal(data['safe_to_spend'])
        sections.insert(0,{'title':'Requested spending or saving','lines':[f"Requested {value} {state['currency']}; room excluding future income {data['safe_to_spend'] or 'Unknown'}. {'Fits the recorded-bills buffer' if allowed else 'Not supported by the conservative buffer'}. This is not a guarantee; the horizon and recorded obligations limit this calculation."]})
    if re.search(r'\b(delay\w*|late)\b',text):
        incomes=[e for e in state['events'] if e['id'] in state['collection_event_ids']]
        explicit=next((e for e in incomes if e['id'].casefold() in text),None)
        chosen=explicit or (incomes[0] if len(incomes)==1 else None)
        delay=re.search(r'\b(7|14|30|seven|fourteen|thirty)\b',text)
        if chosen and delay and state['complete']:
            days={'seven':7,'fourteen':14,'thirty':30}.get(delay.group(1),delay.group(1))
            case=simulate(state,'delay',delay_days=int(days),income_reference=chosen['id'])
            sections.insert(0,{'title':'Delayed personal income sensitivity','lines':[case['assumptions'],f"Baseline ending cash {case['baseline']['ending_balance']}; delayed ending cash {case['simulated']['ending_balance']}; lowest cash {case['simulated']['minimum_balance']} on {case['simulated']['lowest_date']}; reserve gap {case['simulated']['funding_gap']} {state['currency']}.",case['next_step']]})
        else:
            sections.insert(0,{'title':'Income timing needs confirmation','lines':['Choose the dated income reference and a 7, 14 or 30-day delay in Personal Planning. No payment or date was guessed.']})
    if 'unexpected' in text or 'medical' in text:
        sections.append({'title':'Unexpected expense options','lines':['Enter the amount and payment date in Personal Planning to compare the extra expense with essential bills and the emergency reserve. Medical affordability is a financial calculation, not medical advice. No emergency cost or available support is invented.']})
    return {'intent':{'categories':['liquidity'],'no_borrowing':True,'combined':False,'reserve_target':None,'basis':'Personal dated cash evidence'},
        'sections':sections,'overdue_total':str(money(sum((Decimal(r['amount']) for r in state['overdue'] if r['direction']=='inflow'),ZERO)))}


def demo_state():
    today=timezone.localdate()
    events=[{'id':'demo-income','date':str(today+timedelta(days=4)),'amount':'10000.00','direction':'inflow','category':'Freelance income','critical':False},
            {'id':'demo-bill','date':str(today+timedelta(days=7)),'amount':'12000.00','direction':'outflow','category':'Essential bills','critical':True}]
    state={'workspace_mode':'personal','known_cash':'18000.00','currency':'BDT','complete':True,'as_of':str(today),'end_date':str(today+timedelta(days=30)),
        'policy':{'reserve':'8000.00','horizon_days':30},'events':events,'collection_event_ids':['demo-income'],'overdue':[],
        'personal_context':{'income_type':'freelance','savings_target':'5000.00'},'blocking_reasons':[]}
    state['projection']=cash_timeline(Decimal(18000),events,today,30,Decimal(8000))
    state['fingerprint']=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
    return state
