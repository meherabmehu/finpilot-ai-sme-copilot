"""Deterministic intent and evidence; never infer a customer's reason for nonpayment."""
import re
from datetime import date, timedelta
from decimal import Decimal

from ..engine import money
from .scenario_engine import suggested_plans, compare_plans


def question_intent(question):
    text = question.casefold()
    categories = []
    if any(word in text for word in ('overdue', 'collection', 'receivable', 'customer', 'nonpayment')):
        categories.append('collections')
    if any(word in text for word in ('expense', 'spending', 'cost growth', 'cost increase')):
        categories.append('expenses')
    if any(word in text for word in ('cash', 'liquidity', 'reserve', 'payroll', 'supplier', 'afford', 'payment')):
        categories.append('liquidity')
    if 'risk' in text or not categories:
        categories = list(dict.fromkeys(categories + ['collections', 'expenses', 'liquidity']))
    no_borrowing = bool(re.search(r'\b(?:without\s+(?:(?:taking|a|any|out)\s+)*(?:loan|borrow|debt)|no[\s-]+(?:loan|borrow|debt)|do not borrow|don.t borrow|avoid\s+(?:loan|borrow|debt))', text))
    return {'categories': categories, 'no_borrowing': no_borrowing,
            'basis': 'deterministic keyword intent; ambiguous wording requires owner review'}


def analyze_question(state, question):
    intent = question_intent(question)
    today = date.fromisoformat(state['as_of'])
    sections = []
    overdue = [row for row in state['overdue'] if row['direction'] == 'inflow' and row['date'] < state['as_of']]
    if 'collections' in intent['categories']:
        total = money(sum((Decimal(row['amount']) for row in overdue), Decimal('0')))
        lines = [f"Total overdue receivables: {state['currency']} {total}. Only unpaid receipts with due dates before {today} are overdue."]
        for row in sorted(overdue, key=lambda r: r['date'])[:20]:
            lines.append(f"Transaction tx:{row['id']}: {row['amount']} {state['currency']}, due {row['date']}, {(today-date.fromisoformat(row['date'])).days} days overdue. Reference: {row.get('reference') or 'not recorded'}.")
            if row.get('recorded_note'):
                lines.append('Recorded note (unverified user data, not a confirmed cause): ' + row['recorded_note'])
        lines.extend(['The actual reason for nonpayment is unknown unless documented; the ledger alone cannot diagnose customer behavior.',
                      'Review the invoice and contact the customer to confirm receipt, dispute status and a realistic payment date. Record follow-up separately; no message is sent by this investigation.',
                      'Recovery scenarios below are assumptions only. Compare their receipt dates with payroll and supplier obligations; do not spend against an unconfirmed promise.'])
        if not overdue:
            lines.append('No recorded overdue receivables found. Merely pending or due-today invoices are not overdue; unrecorded customer balances remain unknown.')
        sections.append({'title': 'Overdue collections', 'lines': lines})
    if 'expenses' in intent['categories']:
        current, previous = Decimal(state['trends']['expenses']), Decimal(state['trends']['previous_expenses'])
        change = money((current-previous)/previous*100) if previous else None
        lines = [f"Recorded operating expenses {state['period_start']} to {today}: {state['currency']} {current}; previous 30 days {(today-timedelta(days=59))} to {(today-timedelta(days=30))}: {previous}.",
                 f"Change: {change}% versus the previous period." if change is not None else 'Percentage change is undefined because previous-period expenses are zero.',
                 'A recorded increase is not confirmed overspending: volume, timing, classification and incomplete records may explain it.']
        for category in state['expense_categories'][:10]:
            lines.append(f"Category {category['category']}: current {category['amount']}; previous {category.get('previous_amount', 'unknown')} {state['currency']}.")
        sections.append({'title': 'Expense growth', 'lines': lines})
    if 'liquidity' in intent['categories']:
        projection = state['projection']
        lines = [f"Actual recorded cash (opening cash + paid ledger only): {state['known_cash'] or 'Unknown'} {state['currency']}; reserve {state['policy']['reserve']}."]
        if projection.get('available'):
            lines.append(f"Dated-only minimum estimate {projection['minimum_balance']} on {projection['lowest_date']}; reserve gap {projection['funding_gap']}. Future receipts are uncertain, not actual cash.")
        else:
            lines.append(projection['reason'])
        for event in [e for e in state['events'] if e['direction'] == 'outflow'][:12]:
            lines.append(f"Obligation {event['id']}: {event['amount']} {state['currency']} on {event['date']}, category {event['category']}; protected payroll: {event['payroll']}; critical: {event['critical']}.")
        sections.append({'title': 'Liquidity and dated obligations', 'lines': lines})
    if intent['no_borrowing']:
        sections.append({'title': 'No-borrowing constraint', 'lines': ['Borrowing candidates are excluded from recommendations. Business policies still apply; supplier changes and customer receipts require external confirmation.']})
    return {'intent': intent, 'sections': sections, 'overdue_total': str(money(sum((Decimal(r['amount']) for r in overdue), Decimal('0'))))}


def question_comparison(state, analysis, custom_plans=None):
    plans = custom_plans if custom_plans is not None else suggested_plans(state)
    if custom_plans is None and 'collections' in analysis['intent']['categories'] and state['complete']:
        overdue = sorted([r for r in state['overdue'] if r['direction'] == 'inflow' and r['date'] < state['as_of']], key=lambda r: -Decimal(r['amount']))
        if overdue:
            row = overdue[0]
            receipts = [{'name': f'Assume overdue recovery in {days} days', 'actions': [
                {'kind': 'collect', 'event_id': f"tx:{row['id']}", 'amount': row['amount'],
                 'date': (date.fromisoformat(state['as_of'])+timedelta(days=days)).isoformat()}]}
                for days in (1, 7)]
            plans = [plans[0], *receipts, *plans[1:]][:8]
    if analysis['intent']['no_borrowing'] and custom_plans is None:
        plans = [p for p in plans if not any(a['kind'] == 'finance' for a in p['actions'])]
    return compare_plans(state, plans, allow_borrowing=not analysis['intent']['no_borrowing'])
