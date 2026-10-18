"""Explainable descriptive insights over an already-authorized business.

No scores, inferred customer identities, payment changes or trained forecasts.
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from ..engine import cash_effect, money
from .financial_state import cash_timeline
from .categories import is_debt_service_category

ZERO = Decimal('0')


def cash_runway(business, state):
    result = {'available': False, 'days': None, 'months': None, 'daily_net_burn': None,
              'history_days': 0, 'active_days': 0, 'window_days': 90,
              'basis': 'Recorded operating net burn; excludes transfers and financing movements. '
                       'Assumes this average continues; future debt and dated commitments are assessed separately.'}
    if not state['complete']:
        return result | {'reason': 'Complete opening cash, currency and dated cash records before estimating runway.'}
    as_of = date.fromisoformat(state['as_of'])
    start = max(business.opening_date, as_of - timedelta(days=89))
    rows = list(business.transactions.filter(archived=False, status='paid', currency=business.currency,
                 date__gte=start, date__lte=as_of).exclude(kind__in=['transfer', 'loan_disbursement', 'loan_repayment'])[:20001])
    if not rows or len(rows) > 20000:
        return result | {'reason': 'No bounded operating cash history is available.'}
    days = (as_of - min(row.date for row in rows)).days + 1
    active = len({row.date for row in rows})
    result.update(history_days=days, active_days=active)
    if days < 30 or active < 10:
        return result | {'reason': 'Runway requires at least 30 calendar days and 10 active days of paid operating history.'}
    burn = -sum((cash_effect(row) for row in rows), ZERO) / days
    result.update(daily_net_burn=str(money(burn)), available=True)
    if burn <= 0:
        return result | {'reason': 'No positive historical operating net burn. A finite runway cannot be inferred; future obligations still matter.'}
    cash = max(Decimal(state['known_cash']), ZERO)
    estimate = cash / burn
    return result | {'days': str(estimate.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)),
                     'months': str((estimate/30).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)),
                     'reason': 'Average-burn estimate, not a promised survival date or the dated reserve-risk timeline.'}


def financial_health(state):
    projection = state['projection']
    if not state['complete'] or not projection.get('available'):
        label, tone, reason = 'Insufficient Data', 'caution', 'Required opening cash, dates, currency or completeness need review.'
    elif Decimal(state['known_cash']) < 0 or Decimal(projection['minimum_balance']) < 0:
        label, tone, reason = 'Critical', 'risk', 'Recorded or dated projected closing cash is below zero.'
    elif projection['reserve_breach'] or Decimal(projection['intraday_gap']) > 0 or state['overdue']:
        label, tone, reason = 'At Risk', 'caution', 'A reserve breach, payment-first funding gap or due/overdue record needs review.'
    else:
        label, tone, reason = 'Stable', 'calm', 'No rule flags a dated cash, reserve or overdue concern under current assumptions.'
    return {'label': label, 'tone': tone, 'reason': reason,
            'qualification': 'Rule-based status, not an audited safety guarantee. Missing expenses and delayed receipts can change it.'}


def payment_priorities(state):
    policy = state['policy']
    restricted = {value.casefold() for value in policy['restricted_categories']}
    overdue_dates = {f"tx:{row['id']}": row['date'] for row in state['overdue'] if row['direction'] == 'outflow'}
    rows = []
    for event in state['events']:
        if event['direction'] != 'outflow':
            continue
        if event.get('payroll') and policy['protect_payroll']:
            tier, label, protected = 1, 'Protected payroll', True
        elif event.get('critical') and policy['protect_critical_suppliers']:
            tier, label, protected = 2, 'Protected critical supplier', True
        elif event['category'].casefold() in restricted:
            tier, label, protected = 3, 'Protected category', True
        elif event.get('payroll') or event.get('critical'):
            tier, label, protected = 4, 'Priority payment; protection disabled in rules', False
        elif is_debt_service_category(event['category']):
            tier, label, protected = 4, 'Recorded debt-service commitment', False
        elif event['category'].casefold() in ('marketing', 'discretionary'):
            tier, label, protected = 6, 'Review discretionary spending', False
        else:
            tier, label, protected = 5, 'Dated payment commitment', False
        rows.append({**event, 'tier': tier, 'priority': label, 'protected': protected,
                     'recorded_due': overdue_dates.get(event['id'], event['date']),
                     'timing_note': 'Due/overdue; next-day timeline is a stress assumption.' if event['id'] in overdue_dates else event['basis'],
                     'dependency': 'Keep recorded dates and amounts under current policy.' if protected else
                                   'Any timing change requires agreement and review; no right to defer is inferred.'})
    return sorted(rows, key=lambda row: (row['tier'], row['recorded_due'], row['id']))


def collection_risk(business, state):
    """Invoice-level exposure; this schema contains no structured customer identity."""
    as_of = date.fromisoformat(state['as_of'])
    invoices = business.transactions.filter(archived=False, kind='receivable', status='pending', date__lte=as_of)
    shown = list(invoices.order_by('-amount', 'pk')[:21])
    rows = []
    for invoice in shown[:20]:
        overdue = max((as_of-invoice.due_date).days, 0) if invoice.due_date else None
        event_id = f'tx:{invoice.pk}'
        impact = None
        if state['complete'] and invoice.currency == state['currency'] and any(e['id'] == event_id for e in state['events']):
            without = cash_timeline(Decimal(state['known_cash']), [e for e in state['events'] if e['id'] != event_id], as_of,
                                    state['policy']['horizon_days'], Decimal(state['policy']['reserve']))
            impact = str(money(Decimal(without['funding_gap'])-Decimal(state['projection']['funding_gap'])))
        rows.append({'id': invoice.pk, 'reference': invoice.reference, 'description': invoice.description,
                     'amount': str(invoice.amount), 'currency': invoice.currency, 'due_date': invoice.due_date,
                     'days_overdue': overdue, 'reserve_gap_increase_if_uncollected': impact,
                     'note': 'Overdue receipts are excluded from dated cash until a recovery assumption is supplied.' if overdue else
                             'Unknown due date.' if invoice.due_date is None else 'Receipt on this date is unconfirmed.'})
    matching = [row for row in state['overdue'] if row['direction'] == 'inflow' and row['days_overdue'] > 0]
    return {'invoices': rows, 'truncated': len(shown) > 20, 'overdue_count': len(matching),
            'overdue_amount': str(money(sum((Decimal(row['amount']) for row in matching), ZERO))) if state['diagnostics']['foreign_currency_rows'] == '0' else None,
            'basis': 'Descriptive invoice exposure only. Customer identities and default probabilities are not recorded or inferred.'}


def survival_overview(business, state):
    priorities = payment_priorities(state)
    return {'health': financial_health(state), 'runway': cash_runway(business, state),
            'priorities': priorities, 'priority_amount': str(money(sum((Decimal(row['amount']) for row in priorities
                        if row.get('payroll') or row.get('critical')), ZERO))), 'collections': collection_risk(business, state)}
