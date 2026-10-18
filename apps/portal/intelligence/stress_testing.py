"""Typed dated-only scenarios. Explicit assumptions never become ledger facts."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

from pydantic import Field, model_validator

from ..engine import money
from .schemas import StrictModel
from .financial_state import cash_timeline
from .scenario_engine import evaluate_plan
from .categories import is_debt_service_category

ZERO = Decimal('0')


class StressAssumptions(StrictModel):
    collection_percent: Decimal = Field(default=Decimal('100'), ge=0, le=100, decimal_places=2)
    collection_delay_days: int = Field(default=0, ge=0, le=30)
    revenue_decrease_percent: Decimal = Field(default=ZERO, ge=0, le=100, decimal_places=2)
    expense_increase_percent: Decimal = Field(default=ZERO, ge=0, le=100, decimal_places=2)
    stress_collection_percent: Decimal = Field(default=ZERO, ge=0, le=100, decimal_places=2)
    stress_delay_days: int = Field(default=7, ge=0, le=30)
    stress_expense_percent: Decimal = Field(default=Decimal('10'), ge=0, le=100, decimal_places=2)
    supplier_event_id: str = Field(default='', max_length=100)
    supplier_delay_days: int = Field(default=0, ge=0, le=90)
    allow_borrowing: bool = False
    financing_amount: Decimal = Field(default=ZERO, ge=0, le=1000000000, decimal_places=2)
    annual_rate: Decimal = Field(default=ZERO, ge=0, le=1000, decimal_places=2)
    months: int = Field(default=12, ge=1, le=120)
    fee: Decimal = Field(default=ZERO, ge=0, le=1000000000, decimal_places=2)

    @model_validator(mode='after')
    def consistent(self):
        if self.financing_amount and not self.allow_borrowing:
            raise ValueError('Enable explicit borrowing assumptions before entering financing.')
        if bool(self.supplier_event_id) != bool(self.supplier_delay_days):
            raise ValueError('A supplier timing assumption requires both a recorded payment and a positive delay.')
        if self.stress_collection_percent > self.collection_percent or self.stress_delay_days < self.collection_delay_days or self.stress_expense_percent < self.expense_increase_percent:
            raise ValueError('Stress collections cannot exceed the user case; stress delay and expense increases cannot be lower.')
        return self


def stress_test(state, specification, assumptions):
    values = assumptions if isinstance(assumptions, StressAssumptions) else StressAssumptions.model_validate(assumptions)
    result = {'kind': 'dated_stress_v1', 'currency': state['currency'], 'as_of': state['as_of'],
              'available': False, 'cases': [], 'assumptions': values.model_dump(mode='json'), 'source_fingerprint': state['fingerprint'],
              'basis': 'Dated-only hypothetical cash cases; no probabilities, new trading averages or executed actions.',
              'limitations': list(state['limitations'])}
    if not state['complete'] or 'collection_event_ids' not in state:
        return result | {'reason': 'Complete dated records and typed receipt provenance are required. Re-investigate legacy evidence.'}
    if (values.revenue_decrease_percent and 'revenue_event_ids' not in state) or (max(values.expense_increase_percent, values.stress_expense_percent) and 'expense_estimate_event_ids' not in state):
        return result | {'reason': 'This historical snapshot lacks revenue/expense provenance. Start a fresh investigation before applying these adjustments.'}
    as_of = date.fromisoformat(state['as_of'])
    end = date.fromisoformat(state['end_date'])
    plan_spec = deepcopy(specification)
    plan_spec['actions'] = list(plan_spec.get('actions', []))
    if values.supplier_event_id:
        plan_spec['actions'].append({'kind': 'shift', 'event_id': values.supplier_event_id, 'days': values.supplier_delay_days})
    if values.financing_amount:
        plan_spec['actions'].append({'kind': 'finance', 'amount': str(values.financing_amount), 'date': (as_of+timedelta(days=1)).isoformat(),
                                     'annual_rate': str(values.annual_rate), 'months': values.months, 'fee': str(values.fee)})
    plan = evaluate_plan(state, plan_spec)
    if not values.allow_borrowing and any(a['kind'] == 'finance' for a in plan['actions']):
        plan['feasible'] = False
        plan['violations'].append('Borrowing is excluded by this scenario; an existing financing action is not silently removed.')
    result.update(plan_name=plan['name'], violations=plan['violations'], dependencies=plan['dependencies'],
                  borrowing=plan['borrowing'], financing_cost=plan['financing_cost'], deferred_liabilities=plan['deferred_liabilities'])
    if not plan['feasible'] or not plan['timeline'].get('available'):
        return result | {'reason': 'The plan violates current snapshot action constraints; review the listed restrictions.'}
    receipt_ids = set(state['collection_event_ids']) | {e['id'] for e in plan['events'] if e['id'].endswith(':assumed-recovery')}
    revenue_ids = set(state.get('revenue_event_ids', []))
    expense_ids = set(state.get('expense_estimate_event_ids', []))
    restricted = {s.casefold() for s in state['policy']['restricted_categories']}
    variants = [('Full receipt case', Decimal('100'), 0, ZERO, ZERO),
                ('Your assumptions', values.collection_percent, values.collection_delay_days, values.revenue_decrease_percent, values.expense_increase_percent),
                ('Stress case', values.stress_collection_percent, values.stress_delay_days, values.revenue_decrease_percent, values.stress_expense_percent)]
    for label, percent, delay, revenue_drop, expense_growth in variants:
        events = deepcopy(plan['events'])
        missing_receipts = ZERO
        adjusted_revenue = adjusted_expenses = 0
        for event in events:
            original = Decimal(event['amount'])
            if event['id'] in receipt_ids:
                receipt = original * percent / 100
                if event['id'] in revenue_ids:
                    receipt *= 1 - revenue_drop / 100
                    adjusted_revenue += 1
                event['amount'] = str(money(receipt))
                event['date'] = (date.fromisoformat(event['date'])+timedelta(days=delay)).isoformat()
                realized = Decimal(event['amount']) if date.fromisoformat(event['date']) <= end else ZERO
                missing_receipts += original-realized
            protected = event.get('payroll') or event.get('critical') or event.get('category', '').casefold() in restricted or is_debt_service_category(event.get('category', ''))
            if event['id'] in expense_ids and not protected:
                event['amount'] = str(money(original*(1+expense_growth/100)))
                adjusted_expenses += 1
        timeline = cash_timeline(Decimal(state['known_cash']), events, as_of, state['policy']['horizon_days'], Decimal(state['policy']['reserve']))
        points = {point['date']: point for point in timeline['points']}
        priority = [e for e in events if e['direction'] == 'outflow' and (e.get('payroll') or e.get('critical')) and e['date'] in points]
        funding_risk = any(Decimal(points[e['date']]['payment_first_low']) < 0 for e in priority)
        result['cases'].append({'label': label, 'timeline': timeline, 'collection_percent': str(percent), 'delay_days': delay,
                                'revenue_decrease_percent': str(revenue_drop), 'expense_increase_percent': str(expense_growth),
                                'unrealized_receipts': str(money(missing_receipts)), 'priority_payment_count': len(priority),
                                'protected_funding_status': 'Timing or funding risk' if funding_risk else 'No payment-first gap on priority dates' if priority else 'No priority payments recorded',
                                'reserve_goal_met': Decimal(timeline['funding_gap']) == 0,
                                'robust_under_case': Decimal(timeline['funding_gap']) == 0 and Decimal(timeline['intraday_gap']) == 0 and not funding_risk,
                                'revenue_events_adjusted': adjusted_revenue, 'expense_events_adjusted': adjusted_expenses})
    result['available'] = True
    result['robust_across_cases'] = all(case['robust_under_case'] for case in result['cases'])
    result['limitations'].extend([
        'Partial/uncollected amounts are unrealized cash assumptions; invoices are not canceled or settled.',
        'Revenue changes apply only to dated future income records; expense changes only to unprotected expense estimates/recurrences. Fixed payables, payroll and critical suppliers remain unchanged.',
        'Priority funding uses a conservative payments-first daily test. It does not confirm actual payment execution or exact intraday order.',
        'Original saved ranking is unchanged. Robustness is conditional on these explicit cases, not a learned probability or global optimum.',
    ])
    return result
