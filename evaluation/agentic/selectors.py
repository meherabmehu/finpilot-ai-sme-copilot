"""Translate authored input selectors using only the application's authorized snapshot.

This is input adaptation, not answer generation. Unresolved requests are never dropped.
"""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

from apps.portal.engine import money


def resolve(state, specifications):
    plans = deepcopy(specifications)
    for plan in plans:
        for action in plan.get('actions', []):
            selector = action.get('event_id', '')
            events = state['events']
            outgoing = [e for e in events if e['direction'] == 'outflow']
            incoming = [e for e in events if e['direction'] == 'inflow']
            if selector.startswith('@'):
                if selector == '@payroll':
                    matches = [e for e in outgoing if e['payroll']]
                elif selector == '@critical':
                    matches = [e for e in outgoing if e['critical']]
                elif selector == '@largest_outflow':
                    matches = sorted(outgoing, key=lambda e: (-Decimal(e['amount']), e['date'], e['id']))
                elif selector.startswith('@category:'):
                    matches = [e for e in outgoing if e['category'].casefold() == selector[10:].casefold()]
                elif selector.startswith(('@outflow:', '@inflow:')):
                    index = int(selector.split(':')[1]) - 1
                    matches = (outgoing if selector.startswith('@outflow:') else incoming)[index:index + 1]
                else:
                    raise ValueError(f'Unsupported input selector: {selector}')
                if not matches:
                    raise ValueError(f'Application snapshot cannot resolve input selector: {selector}')
                action['event_id'] = matches[0]['id']
            for field in ('amount', 'fee'):
                value = action.get(field, '')
                if isinstance(value, str) and value.startswith('@'):
                    event = next((e for e in events if e['id'] == action.get('event_id')), None)
                    if value.startswith(('@funding_gap', '@percent_of_funding_gap:')):
                        if not state['projection'].get('available'):
                            raise ValueError('Funding-gap selector requires an available application projection')
                        amount = Decimal(state['projection']['funding_gap'])
                        percent = Decimal(value.split(':')[1]) if ':' in value else Decimal('100')
                    elif event:
                        amount = Decimal(event['amount'])
                        percent = Decimal('50') if value == '@half' else Decimal('100') if value == '@full' else (
                            Decimal(value.split(':')[1]) if value.startswith('@percent:') else None)
                    else:
                        raise ValueError(f'Cannot resolve input amount: {value}')
                    if percent is None:
                        raise ValueError(f'Unsupported input amount: {value}')
                    action[field] = str(money(amount * percent / 100))
            when = action.get('date', '')
            if when.startswith('@as_of'):
                offset = int(when.split('+')[1]) if '+' in when else 0
                action['date'] = (date.fromisoformat(state['as_of']) + timedelta(days=offset)).isoformat()
    return plans
