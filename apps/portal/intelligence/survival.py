"""Read-only presentation and collection sensitivity over authorized snapshots.

No probabilities, mutation, new ranking or provider calls. Original saved evidence
remains authoritative; sensitivities are explicitly hypothetical recalculations.
"""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

from .financial_state import cash_timeline
from ..engine import money


def collection_sensitivity(state, plan, early_days=3, delay_days=7, partial_percent=None):
    if not isinstance(early_days, int) or not isinstance(delay_days, int) or not 0 <= early_days <= 30 or not 0 <= delay_days <= 30:
        raise ValueError('Collection adjustments must be whole days from 0 to 30.')
    if partial_percent is not None and (not isinstance(partial_percent, int) or not 0 <= partial_percent <= 100):
        raise ValueError('Partial collection must be a whole percentage from 0 to 100.')
    if not state['complete'] or not plan.get('timeline', {}).get('available'):
        return []
    as_of = date.fromisoformat(state['as_of'])
    end = date.fromisoformat(state['end_date'])
    # Only customer/operating receipt assumptions are stressed. Financing does
    # not become a confirmed receipt merely because it is excluded here.
    if 'collection_event_ids' not in state:
        # Legacy snapshots remain readable, but lack typed receipt provenance.
        # Re-investigate rather than guessing which inflows are customer cash.
        return []
    receipt_ids = set(state['collection_event_ids'])
    receipt_ids.update(e['id'] for e in plan['events'] if e['id'].endswith(':assumed-recovery'))
    variants = [('Earlier collections', -early_days, 100), ('Plan dates', 0, 100), ('Delayed collections', delay_days, 100), ('No customer collections', None, 0)]
    if partial_percent is not None:
        variants.append(('Partial collections', 0, partial_percent))
    results = []
    for label, shift, percent in variants:
        events = deepcopy(plan['events'])
        excluded = Decimal('0')
        unrealized = Decimal('0')
        for event in events:
            if event['id'] not in receipt_ids:
                continue
            original = Decimal(event['amount'])
            event['amount'] = str(money(original*percent/100))
            unrealized += original-Decimal(event['amount'])
            if shift is None:
                excluded += original
                event['date'] = (end + timedelta(days=1)).isoformat()
            else:
                day = max(as_of + timedelta(days=1), date.fromisoformat(event['date']) + timedelta(days=shift))
                event['date'] = day.isoformat()
                if day > end:
                    excluded += Decimal(event['amount'])
                    unrealized += Decimal(event['amount'])
        timeline = cash_timeline(Decimal(state['known_cash']), events, as_of, state['policy']['horizon_days'], Decimal(state['policy']['reserve']))
        results.append({'label': label, 'shift_days': shift, 'collection_percent': percent, 'timeline': timeline,
                        'reserve_met': plan['feasible'] and Decimal(timeline['funding_gap']) == 0,
                        'receipts_outside_horizon': str(excluded), 'unrealized_receipts': str(money(unrealized)), 'affected_receipts': len(receipt_ids),
                        'basis': 'Hypothetical collection assumption; no probability or customer agreement is inferred.'})
    return results


def dashboard_survival(state, stats, issues):
    projection = state['projection']
    risk_date = projection.get('reserve_breach')
    if not projection.get('available'):
        title, status = 'Your cash outlook needs more information', 'caution'
        explanation = projection.get('reason', 'Review opening cash and record completeness.')
    elif risk_date:
        days = (date.fromisoformat(risk_date) - date.fromisoformat(state['as_of'])).days
        title = 'Cash is below your minimum reserve today' if days == 0 else f'Cash may fall below your reserve in {days} days'
        status = 'risk'
        explanation = f"Dated-only estimate: reserve gap {state['currency']} {projection['funding_gap']} on {projection['lowest_date']}. Customer receipts remain uncertain."
    elif Decimal(projection.get('intraday_gap', '0')) > 0:
        title, status = 'Same-day payment timing could leave a cash gap', 'caution'
        explanation = f"Payments before receipts may leave a gap of {state['currency']} {projection['intraday_gap']}. Confirm receipt timing before committing payments."
    elif state['overdue']:
        title, status = 'Overdue records need your attention', 'caution'
        explanation = 'Review unpaid customer receipts and payments before committing to new spending.'
    else:
        title, status = 'No immediate cash shortfall identified', 'calm'
        explanation = 'Based on recorded dated commitments only. Unrecorded expenses and delayed receipts can change the outlook.'
    upcoming = sum((Decimal(e['amount']) for e in state['events'] if e['direction'] == 'outflow'), Decimal('0'))
    actions = []
    if any(e['direction'] == 'inflow' for e in state['overdue']):
        actions.append({'label': 'Review overdue customer payments', 'route': 'receivables'})
    if risk_date or issues:
        actions.append({'label': 'Compare recovery options', 'route': 'lab'})
    if any(e['category'].casefold() in ('marketing', 'discretionary') for e in state['events'] if e['direction'] == 'outflow'):
        actions.append({'label': 'Review discretionary spending', 'route': 'expenses'})
    if not state['complete']:
        actions.insert(0, {'label': 'Complete your financial records', 'route': 'quality'})
    if not actions:
        actions.append({'label': 'Review upcoming payments', 'route': 'payments'})
    return {'title': title, 'status': status, 'explanation': explanation, 'actions': actions[:3],
            'upcoming': str(upcoming), 'receivables': stats['receivables'], 'risk_date': risk_date}


def navigator(state, comparison, selected_index=0, early_days=3, delay_days=7, partial_percent=50):
    plans = comparison.get('plans', [])
    if not 0 <= selected_index < len(plans):
        selected_index = 0
    rows = []
    for index, plan in enumerate(plans):
        cases = collection_sensitivity(state, plan, early_days, delay_days, partial_percent)
        rows.append({'index': index, 'plan': plan, 'cases': cases,
                     'delay_reserve_met': cases[2]['reserve_met'] if cases else False,
                     'partial_reserve_met': cases[-1]['reserve_met'] if cases else False})
    selected = rows[selected_index] if rows else None
    checklist = []
    if selected:
        by_id = {e['id']: e for e in state['events']}
        for action in selected['plan']['actions']:
            event = by_id.get(action.get('event_id'), {})
            checklist.append({'action': action['kind'], 'description': event.get('description', 'Explicit simulated assumption'),
                              'reference': action.get('event_id', ''), 'date': action.get('date') or event.get('date'),
                              'amount': action.get('amount'), 'days': action.get('days'), 'status': 'Planned; requires confirmation'})
    return {'rows': rows, 'initial': rows[:3], 'more': rows[3:], 'selected': selected,
            'selected_index': selected_index, 'checklist': checklist,
            'any_goal_met': any(p.get('goal_satisfied') for p in plans), 'early_days': early_days, 'delay_days': delay_days, 'partial_percent': partial_percent}
