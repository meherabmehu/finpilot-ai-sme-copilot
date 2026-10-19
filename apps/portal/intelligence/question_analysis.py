"""Deterministic intent and evidence; never infer a customer's reason for nonpayment."""
import re
from datetime import date, timedelta
from decimal import Decimal

from ..engine import money
from .scenario_engine import suggested_plans, compare_plans
from .question_language import normalize_question


def question_intent(question):
    text = normalize_question(question)
    categories = []
    if re.search(r'\b(sales?|revenue)\b', text):
        categories.append('sales')
    if any(word in text for word in ('overdue', 'collection', 'receivable', 'customer', 'nonpayment')):
        categories.append('collections')
    if any(word in text for word in ('expense', 'spending', 'cost growth', 'cost increase')):
        categories.append('expenses')
    if any(word in text for word in ('cash', 'liquidity', 'reserve', 'payroll', 'supplier', 'afford', 'payment')):
        categories.append('liquidity')
    if re.search(r'\b(loan|borrow\w*|debt|financing)\b', text) and not categories:
        categories.append('financing')
    if 'risk' in text or not categories:
        categories = list(dict.fromkeys(categories + ['collections', 'expenses', 'liquidity']))
    if re.search(r'\b(overdue|collections?|receivables?|customer payments?)\b', text) and re.search(r'\b(how much|which|list|total)\b', text) and not re.search(r'\b(cash|reserve|risk|supplier|payroll|borrow\w*|loan\w*|expense\w*|spend\w*)\b', text):
        categories = ['collections']
    no_borrowing = bool(re.search(r'\b(?:without\s+(?:(?:taking|a|any|out)\s+)*(?:loan|borrow|debt)|no[\s-]+(?:loan|borrow|debt)|do not borrow|don.t borrow|avoid\s+(?:loan|borrow|debt))', text))
    target = re.search(r'\b(?:protect|keep|reserve)\s+(?:at least\s+)?(?:[a-z]{3}\s+|\$|\u00a3)?([\d,]+(?:\.\d{1,2})?)', text)
    reserve_target = str(Decimal(target.group(1).replace(',', ''))) if target else None
    return {'categories': categories, 'no_borrowing': no_borrowing,
            'combined': bool(re.search(r'\b(combin\w*|close (?:the )?gap|protect at least)\b', text)),
            'reserve_target': reserve_target,
            'basis': 'deterministic keyword intent; ambiguous wording requires owner review'}


def analyze_question(state, question):
    question = normalize_question(question)
    intent = question_intent(question)
    today = date.fromisoformat(state['as_of'])
    sections = []
    if 'sales' in intent['categories']:
        revenue = Decimal(state['trends']['revenue'])
        lines = [f"Recorded revenue in the last 30 days: {state['currency']} {revenue}; this includes accrued invoices, not only paid cash."]
        decline = re.search(r'\b(\d{1,3}(?:\.\d{1,2})?)\s*%', question)
        if decline and 0 <= Decimal(decline.group(1)) <= 100:
            percent = Decimal(decline.group(1))
            increase = bool(re.search(r'\b(increase|grow\w*|rise|higher)\b', question)) and not re.search(r'\b(decline|reduc\w*|fall|drop|lower)\b', question)
            direction, factor = ('increase', 1+percent/100) if increase else ('decline', 1-percent/100)
            lines.append(f"Illustrative {percent}% revenue {direction} against that recorded period: {money(revenue*percent/100)} {'more' if increase else 'less'} revenue, leaving {money(revenue*factor)}. This is not a weekly cash prediction or a guaranteed sales response.")
        lines.append('Use Scenario Simulation for dated future income shocks. Confirm future sales, receipt dates and essential operating costs before converting revenue assumptions into cash.')
        sections.append({'title': 'Sales and operating sensitivity', 'lines': lines})
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
            delta = money(Decimal(category['amount'])-Decimal(category.get('previous_amount', '0')))
            lines.append(f"Category {category['category']}: current {category['amount']}; previous {category.get('previous_amount', 'unknown')} {state['currency']}; recorded change {delta}. Changes identify ledger contributors, not verified operational causes.")
        sections.append({'title': 'Expense growth', 'lines': lines})
    if 'liquidity' in intent['categories']:
        projection = state['projection']
        lines = [f"Actual recorded cash (opening cash + paid ledger only): {state['known_cash'] or 'Unknown'} {state['currency']}; reserve {state['policy']['reserve']}."]
        lines.append(f"Planning horizon: {state['as_of']} to {state['end_date']}; estimated from dated commitments only, not guaranteed future trading.")
        if projection.get('available'):
            lines.append(f"Dated-only minimum estimate {projection['minimum_balance']} on {projection['lowest_date']}; reserve gap {projection['funding_gap']}. Future receipts are uncertain, not actual cash.")
        else:
            lines.append(projection['reason'])
        for event in [e for e in state['events'] if e['direction'] == 'outflow'][:12]:
            lines.append(f"Obligation {event['id']}: {event['amount']} {state['currency']} on {event['date']}, category {event['category']}; protected payroll: {event['payroll']}; critical: {event['critical']}.")
        sections.append({'title': 'Liquidity and dated obligations', 'lines': lines})
    if 'financing' in intent['categories']:
        trends = state['trends']
        surplus = money(Decimal(trends.get('operating_cash_inflows', '0'))-Decimal(trends.get('operating_cash_outflows', '0')))
        sections.append({'title': 'Loan safety requires an actual quotation', 'lines': [
            f"Recorded paid operating net cash over the last 30 days: {surplus} {state['currency']}; loan proceeds and repayments are excluded from this capacity indicator.",
            'No specific loan is identified by this question. Principal, nominal annual rate, term, fees, disbursement date and existing repayment obligations are required before calculating repayment and reserve stress.',
            'Use the Custom Loan Calculator to enter an actual quotation, inspect repayments and the higher-rate sensitivity, and compare no-loan recovery alternatives. A public program description is not approval or proof that borrowing is safe.']})
    if re.search(r'\bhalf\b|\b(?:customer|invoice|receivable)\b.*?\b\d+(?:\.\d+)?\s*%', question):
        percentage = re.search(r'(\d+(?:\.\d+)?)\s*%', question)
        percent = Decimal(percentage.group(1)) if percentage else Decimal('50')
        explicit = re.search(r'\btx:(\d+)\b', question)
        candidates = [r for r in overdue if not explicit or str(r['id']) == explicit.group(1)]
        if not 0 < percent <= 100:
            lines = ['Use a receipt percentage greater than zero and no greater than one hundred.']
        elif len(candidates) != 1:
            lines = ['Identify the overdue invoice with its tx reference and expected receipt date. Several or no eligible invoices match; no customer or collection amount has been guessed.']
        else:
            from .recovery_solver import recovery_case
            row = candidates[0]
            amount = money(Decimal(row['amount'])*percent/100)
            if amount <= 0:
                sections.insert(0, {'title':'Partial customer receipt sensitivity', 'lines':[
                    'The assumed partial receipt rounds below the supported currency precision. Enter an explicit positive amount in Scenario Simulation. No receipt was recorded.']})
                return {'intent':intent,'sections':sections,'overdue_total':str(money(sum((Decimal(r['amount']) for r in overdue),Decimal('0'))))}
            # Tomorrow is visibly illustrative, not a promise or inferred agreement.
            assumed = today+timedelta(days=1)
            recovery = recovery_case(state, {'recoveries': [{'event_id': f"tx:{row['id']}", 'amount': amount, 'date': assumed}]})
            plan = recovery['plan']
            lines = [f"Illustrative {percent}% receipt on tx:{row['id']}: {amount} {state['currency']} on {assumed}. This date is assumed only; confirm the customer and actual timing.",
                f"Baseline reserve gap {recovery['baseline'].get('remaining_gap', 'unknown')}; partial-receipt residual gap {plan.get('remaining_gap', 'unknown')} {state['currency']}; ending cash {plan.get('expected_ending_cash', 'unknown')}. Upcoming receipts already in baseline are not counted again.",
                'This is a scenario, not a recorded settlement. Actual cash and the unpaid invoice remain unchanged.']
        sections.insert(0, {'title': 'Partial customer receipt sensitivity', 'lines': lines})
    if intent['no_borrowing']:
        sections.append({'title': 'No-borrowing constraint', 'lines': ['Borrowing candidates are excluded from recommendations. Business policies still apply; supplier changes and customer receipts require external confirmation.']})
    if re.search(r'\b(prioriti\w*|criticality|critical payment)\b', question, re.I):
        from .business_domain import assess_payment
        lines = []
        for event in [e for e in state['events'] if e['direction'] == 'outflow'][:8]:
            assessment = assess_payment(event, state)
            lines.append(f"Payment {event['id']}: suggested {assessment['suggested_priority']}; urgency {assessment['urgency']}; due {event['date']}; {event['amount']} {state['currency']}. {assessment['impact']} Evidence: {assessment['evidence_sufficiency']}. Owner confirmation needed: {assessment['owner_confirmation_needed']}.")
        lines.append('Confirm operational dependency, contract penalties and alternatives. Preliminary industry/category inference never changes protection rules automatically.')
        sections.insert(0, {'title': 'Payment urgency and business criticality', 'lines': lines})
    return {'intent': intent, 'sections': sections, 'overdue_total': str(money(sum((Decimal(r['amount']) for r in overdue), Decimal('0'))))}


def question_comparison(state, analysis, custom_plans=None):
    if custom_plans is None and analysis['intent'].get('combined'):
        from .recovery_solver import combined_solutions
        return combined_solutions(state, no_borrowing=analysis['intent']['no_borrowing'], target_reserve=analysis['intent'].get('reserve_target'))['comparison']
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
