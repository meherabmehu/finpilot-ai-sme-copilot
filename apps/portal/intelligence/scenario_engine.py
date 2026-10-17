"""Non-destructive counterfactual cash planning with explicit constraints."""

from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from pydantic import ValidationError

from ..engine import money, loan_schedule
from .financial_state import cash_timeline
from .schemas import PlanSpec

ZERO = Decimal('0')


def evaluate_plan(state, specification):
    plan = specification if isinstance(specification, PlanSpec) else PlanSpec.model_validate(specification)
    result = {'name': plan.name, 'actions': plan.model_dump(mode='json')['actions'], 'basis': 'simulated',
              'goal_satisfied': False, 'goal_status': 'unknown', 'explanation': '',
              'feasible': False, 'violations': [], 'dependencies': [], 'tradeoffs': [], 'timeline': {'available': False},
              'borrowing': '0.00', 'financing_cost': '0.00', 'action_count': len(plan.actions), 'deferred_liabilities': '0.00'}
    if not state['complete']:
        result['violations'].append('Cash timeline is unavailable because required data is incomplete.')
        return result
    policy = state['policy']
    as_of = date.fromisoformat(state['as_of'])
    horizon = policy['horizon_days']
    end = as_of + timedelta(days=horizon)
    events = deepcopy(state['events'])
    by_id = {e['id']: e for e in events}
    touched = set()
    borrowing = cost = ZERO
    restrictions = {c.casefold() for c in policy['restricted_categories']}
    for index, action in enumerate(plan.actions):
        if action.kind == 'collect':
            overdue = next((row for row in state['overdue'] if f"tx:{row['id']}" == action.event_id and row['direction'] == 'inflow'), None)
            if (not overdue or action.event_id in touched or action.amount <= 0 or action.amount > Decimal(overdue['amount'])
                    or not action.date or not as_of < date.fromisoformat(action.date) <= end):
                result['violations'].append('Assumed overdue collection requires an authorized unpaid receivable, bounded amount and future date in the horizon; each receipt can be changed only once.')
                continue
            touched.add(action.event_id)
            events.append({'id': action.event_id + ':assumed-recovery', 'date': action.date, 'amount': str(action.amount),
                           'direction': 'inflow', 'category': 'Collection assumption', 'description': 'Unconfirmed overdue receipt'})
            result['dependencies'].append('Customer confirmation and actual receipt are required. Recovery is hypothetical, not guaranteed cash; nonpayment reasons remain unknown unless recorded.')
            continue
        if action.kind == 'finance':
            if not action.date or not as_of < date.fromisoformat(action.date) <= end or action.amount <= 0:
                result['violations'].append('Financing requires a positive amount and date inside the planning horizon.')
                continue
            borrowing += action.amount
            if borrowing > Decimal(policy['max_borrowing']) or action.annual_rate > Decimal(policy['max_annual_rate']):
                result['violations'].append('Financing exceeds preferred borrowing or annual-rate limits.')
            schedule = loan_schedule(action.amount, action.annual_rate, action.months, action.fee)
            cost += Decimal(schedule['total_interest']) + action.fee
            events.append({'id': f'plan:finance:{index}', 'source': 'assumption', 'date': action.date, 'amount': str(action.amount), 'direction': 'inflow', 'category': 'Financing', 'description': 'Illustrative financing, not approved'})
            if action.fee:
                events.append({'id': f'plan:fee:{index}', 'source': 'assumption', 'date': action.date, 'amount': str(action.fee), 'direction': 'outflow', 'category': 'Financing fee', 'description': 'Assumed upfront fee'})
            for installment in schedule['schedule']:
                due = date.fromisoformat(action.date) + relativedelta(months=installment['month'])
                events.append({'id': f'plan:repayment:{index}:{installment["month"]}', 'source': 'assumption', 'date': due.isoformat(), 'amount': installment['payment'], 'direction': 'outflow', 'category': 'Loan repayment', 'description': 'Illustrative repayment'})
            result['dependencies'].append('A lender must agree and disburse on the assumed date; no approval is inferred.')
            result['tradeoffs'].append(f"Full financing cost is {money(Decimal(schedule['total_interest']) + action.fee)} {state['currency']}; repayments beyond the timeline remain liabilities.")
            continue
        event = by_id.get(action.event_id)
        if not event:
            result['violations'].append('Referenced event does not belong to the authorized snapshot.')
            continue
        if action.event_id in touched:
            result['violations'].append('Each obligation can be changed only once per plan; conflicting actions are rejected.')
            continue
        touched.add(action.event_id)
        protected = (event.get('payroll') and policy['protect_payroll']) or (event.get('critical') and policy['protect_critical_suppliers'])
        if event['direction'] == 'outflow' and (protected or event['category'].casefold() in restrictions):
            result['violations'].append('This payroll, critical supplier or restricted category is protected by business policy.')
            continue
        original_day = date.fromisoformat(event['date'])
        if action.kind == 'shift':
            shifted = original_day + timedelta(days=action.days)
            if not as_of < shifted <= end:
                result['violations'].append('Shifted dates must stay inside the reviewed horizon; obligations cannot be hidden after it.')
                continue
            if event['direction'] == 'outflow' and (action.days < 0 or action.days > policy['max_delay_days']):
                result['violations'].append('Payment delay exceeds the business preference or is negative.')
                continue
            if event['direction'] == 'inflow' and action.days >= 0:
                result['violations'].append('Earlier collection plans require a negative day adjustment.')
                continue
            event['date'] = shifted.isoformat()
            result['dependencies'].append('Customer agreement and actual receipt are required.' if event['direction'] == 'inflow' else 'Supplier agreement is required; no payment permission is implied.')
            result['tradeoffs'].append('Timing changes do not change total payments or ending cash when both dates remain inside the horizon; they may only bridge an interim gap.')
            result['tradeoffs'].append(f"Move {event['id']} from {original_day} to {shifted}; its amount is unchanged.")
        elif action.kind == 'split':
            later = original_day + timedelta(days=action.days)
            amount = Decimal(event['amount'])
            if event['direction'] != 'outflow' or not 0 < action.amount < amount or not 0 < action.days <= policy['max_delay_days'] or later > end:
                result['violations'].append('Split must retain a positive original payment and an agreed later remainder within allowed dates.')
                continue
            event['amount'] = str(money(action.amount))
            events.append({**event, 'id': event['id'] + ':remainder', 'date': later.isoformat(), 'amount': str(money(amount - action.amount))})
            result['tradeoffs'].append('Splitting defers part of the same obligation; the total remains payable inside this horizon and ending cash is unchanged.')
            result['dependencies'].append('Supplier must approve the installment split; late fees are not known.')
        elif action.kind == 'reduce':
            if event['direction'] != 'outflow' or action.amount <= 0 or action.amount > Decimal(event['amount']):
                result['violations'].append('A reduction must be positive and no greater than its outflow.')
                continue
            event['amount'] = str(money(Decimal(event['amount']) - action.amount))
            result['dependencies'].append('Adjustability is UNKNOWN: a genuine supplier invoice is not freely discretionary. Confirm cancellation, credit note or scope change; otherwise the full amount remains owed.')
            result['dependencies'].append('The owner and counterparty must confirm the cost can be cancelled or reduced without undisclosed penalties.')
            result['tradeoffs'].append('Expense reduction may reduce service or growth; no automatic revenue benefit is assumed.')
    result['borrowing'], result['financing_cost'] = str(money(borrowing)), str(money(cost))
    result['dependencies'] = list(dict.fromkeys(result['dependencies']))
    result['deferred_liabilities'] = str(money(sum(Decimal(e['amount']) for e in events if e['direction'] == 'outflow' and date.fromisoformat(e['date']) > end)))
    result['timeline'] = cash_timeline(Decimal(state['known_cash']), events, as_of, horizon, Decimal(policy['reserve']))
    result['events'] = events
    result['feasible'] = not result['violations']
    if result['timeline'].get('available'):
        result['goal_satisfied'] = result['feasible'] and Decimal(result['timeline']['funding_gap']) == 0
        result['goal_status'] = 'reserve met under assumptions' if result['goal_satisfied'] else 'reserve unresolved'
        result['explanation'] = ('Action feasibility is not financial-goal satisfaction. Remaining reserve gap: '
                                 + result['timeline']['funding_gap'] + ' ' + state['currency'] + '. External dependencies still require confirmation.')
        result['remaining_gap'] = result['timeline']['funding_gap']
        result['cash_required'] = result['timeline']['funding_gap']
        result['expected_ending_cash'] = result['timeline']['ending_balance']
    return result


def compare_plans(state, specifications, allow_borrowing=True):
    if len(specifications) > 8:
        raise ValueError('Compare at most eight bounded plans.')
    plans = []
    for specification in specifications:
        try:
            plan = evaluate_plan(state, specification)
            if not allow_borrowing and any(action['kind'] == 'finance' for action in plan['actions']):
                plan['feasible'] = plan['goal_satisfied'] = False
                plan['goal_status'] = 'borrowing constraint violated'
                plan['violations'].append('Borrowing is excluded by the financial question.')
            plans.append(plan)
        except (ValueError, ValidationError) as exc:
            # Invalid schemas never become partially valid financial claims.
            raise ValueError('Invalid counterfactual plan. Check event references, dates and bounded numeric inputs.') from exc
    cautious = state['policy']['risk_tolerance'] == 'cautious'

    def rank(plan):
        if not plan['feasible'] or not plan['timeline'].get('available'):
            return (1, Decimal('Infinity'), 0, 0, 0, 0)
        t = plan['timeline']
        # Payroll/supplier protection is a hard constraint. Then preserve reserve,
        # consider intraday payment risk, borrowing, full cost, and action count.
        return (0, Decimal(t['funding_gap']), Decimal(t['intraday_gap']) if cautious else 0,
                Decimal(plan['borrowing']), Decimal(plan['financing_cost']), plan['action_count'])

    plans.sort(key=rank)
    recommended = next((p['name'] for p in plans if p['feasible']), None)
    best = next((p for p in plans if p['name'] == recommended), None)
    return {'plans': plans, 'recommended': recommended,
            'recommendation_status': best['goal_status'] if best else 'unknown',
            'unresolved_gap': best.get('remaining_gap') if best else None,
            'recommendation_note': 'Best among evaluated candidates, not globally optimal. ' + (best['explanation'] if best else 'No eligible plan with sufficient evidence.'),
            'objective': 'Hard payroll/critical-supplier/category constraints, then minimize reserve gap, '
                         + ('payment-first intraday gap, ' if cautious else '')
                         + 'borrowing, full financing cost, then number of actions. Best among evaluated plans only; not a globally optimal solution.',
            'basis': 'deterministic ranking of simulated plans', 'limitations': state['limitations']}


def suggested_plans(state):
    plans = [{'name': 'Keep recorded schedule', 'actions': []}]
    if not state['complete']:
        return plans
    as_of = date.fromisoformat(state['as_of'])
    policy = state['policy']
    gap_day = state['projection'].get('first_shortfall') or state['projection'].get('reserve_breach')
    target = date.fromisoformat(gap_day) if gap_day else as_of + timedelta(days=7)
    inflow = next((e for e in state['events'] if e['direction'] == 'inflow' and date.fromisoformat(e['date']) > target), None)
    outflow = next((e for e in state['events'] if e['direction'] == 'outflow' and not e['payroll'] and not e['critical'] and date.fromisoformat(e['date']) <= target), None)
    if inflow:
        earlier = max(as_of + timedelta(days=1), target - timedelta(days=1))
        plans.append({'name': 'Request earlier collection', 'actions': [{'kind': 'shift', 'event_id': inflow['id'], 'days': (earlier-date.fromisoformat(inflow['date'])).days}]})
    if outflow and policy['max_delay_days']:
        delay = min(policy['max_delay_days'], (date.fromisoformat(state['end_date']) - date.fromisoformat(outflow['date'])).days)
        if delay > 0:
            plans.append({'name': 'Discuss supplier timing', 'actions': [{'kind': 'shift', 'event_id': outflow['id'], 'days': delay}]})
            plans.append({'name': 'Discuss a split payment', 'actions': [{'kind': 'split', 'event_id': outflow['id'], 'days': delay, 'amount': str(money(Decimal(outflow['amount'])/2))}]})
    discretionary = next((e for e in state['events'] if e['direction'] == 'outflow' and e['category'].casefold() in ('marketing', 'discretionary') and not e['critical'] and not e['payroll']), None)
    if discretionary:
        plans.append({'name': 'Review discretionary spending', 'actions': [{'kind': 'reduce', 'event_id': discretionary['id'], 'amount': str(money(Decimal(discretionary['amount'])/2))}]})
    gap = Decimal(state['projection']['funding_gap'])
    if gap > 0 and Decimal(policy['max_borrowing']) >= gap:
        plans.append({'name': 'Illustrative gap financing', 'actions': [{'kind': 'finance', 'date': (as_of+timedelta(days=1)).isoformat(), 'amount': str(gap), 'annual_rate': str(policy['max_annual_rate']), 'months': 12}]})
    if len(plans) >= 3 and inflow and outflow:
        plans.append({'name': 'Combine collection and payment discussions', 'actions': plans[1]['actions'] + plans[2]['actions']})
    return plans[:8]
