"""Bounded financial snapshots. No LLM, currency conversion or invented cash."""

import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ..engine import cash_effect, money
from ..models import FinancialPolicy
from .schemas import CashEvent, PolicySpec

ZERO = Decimal('0')
MAX_RECORDS = 20000


def policy_for(business):
    saved = FinancialPolicy.objects.filter(business=business).first()
    values = {name: getattr(saved, name) for name in PolicySpec.model_fields} if saved else {}
    return PolicySpec.model_validate(values).model_dump(mode='json') | {
        'reserve': str(business.low_cash_threshold), 'source': 'business preferences' if saved else 'transparent defaults',
    }


def cash_timeline(cash, events, as_of, days, reserve=ZERO):
    """Closing balances assume dated collections precede payments on the same day.

    Also calculate payment-first intraday lows so same-day funding risk is visible.
    The first point is observed/reconciled cash, not a forecast.
    """
    if cash is None:
        return {'available': False, 'reason': 'Cash position is unknown.'}
    dated = defaultdict(lambda: {'inflow': ZERO, 'outflow': ZERO, 'refs': []})
    for event in events:
        item = event.model_dump(mode='json') if isinstance(event, CashEvent) else event
        day = date.fromisoformat(item['date'])
        if as_of < day <= as_of + timedelta(days=days):
            dated[day][item['direction']] += Decimal(str(item['amount']))
            dated[day]['refs'].append(item['id'])
    balance = money(cash)
    points = [{'date': as_of.isoformat(), 'balance': str(balance), 'inflow': '0.00', 'outflow': '0.00', 'refs': [], 'payment_first_low': str(balance)}]
    for offset in range(1, days + 1):
        day = as_of + timedelta(days=offset)
        item = dated[day]
        low = money(balance - item['outflow'])
        balance = money(balance + item['inflow'] - item['outflow'])
        points.append({'date': day.isoformat(), 'balance': str(balance), 'inflow': str(money(item['inflow'])),
                       'outflow': str(money(item['outflow'])), 'refs': item['refs'], 'payment_first_low': str(low)})
    minimum = min(points, key=lambda point: Decimal(point['balance']))
    shortfall = next((p['date'] for p in points if Decimal(p['balance']) < 0), None)
    reserve_breach = next((p['date'] for p in points if Decimal(p['balance']) < reserve), None)
    return {'available': True, 'basis': 'estimated from dated commitments only', 'points': points,
            'minimum_balance': minimum['balance'], 'lowest_date': minimum['date'], 'ending_balance': str(balance),
            'funding_gap': str(money(max(reserve - Decimal(minimum['balance']), ZERO))),
            'first_shortfall': shortfall, 'reserve_breach': reserve_breach,
            'intraday_gap': str(money(max(-min(Decimal(p['payment_first_low']) for p in points), ZERO)))}


def build_state(business, as_of=None):
    """Internal service: business must come from authorization or trusted monitoring."""
    as_of = as_of or timezone.localdate()
    policy = policy_for(business)
    days = policy['horizon_days']
    end = as_of + timedelta(days=days)
    rows = list(business.transactions.filter(archived=False).order_by('date', 'pk')[:MAX_RECORDS + 1])
    capped = len(rows) > MAX_RECORDS
    foreign_currency = any(row.currency != business.currency for row in rows)
    valid = [row for row in rows if row.currency == business.currency]
    limitations = ['Cash completeness is user-confirmed, not independently verified.',
                   'Dated-only estimates omit unrecorded future trading and expenses; no historical averages are silently added.',
                   'Collections and payment changes depend on customers or counterparties. Intraday payment-first risk is reported separately.']
    if capped:
        limitations.append('Record limit exceeded. No cash projection is produced; narrow/archive records or increase reviewed capacity.')
    if foreign_currency:
        limitations.append('Mixed-currency records detected. Cash projection blocked; no implicit conversion is permitted.')
    cash = None
    if business.opening_balance is not None and business.opening_date <= as_of and not capped and not foreign_currency:
        cash = money(business.opening_balance + sum((cash_effect(r) for r in valid if business.opening_date <= r.date <= as_of), ZERO))
    events, undated, overdue, categories = [], [], [], defaultdict(lambda: ZERO)
    previous_categories = defaultdict(lambda: ZERO)
    current_revenue = current_expenses = previous_revenue = previous_expenses = ZERO
    observed_in = observed_out = ZERO
    covered = {(r.recurring_obligation_id, r.due_date or r.date) for r in valid if r.recurring_obligation_id}
    for row in valid:
        if as_of - timedelta(days=29) <= row.date <= as_of:
            current_revenue += row.amount if row.kind in ('income', 'receivable') else -row.amount if row.kind == 'refund' else ZERO
            if row.kind in ('expense', 'payable'):
                current_expenses += row.amount
                categories[row.category] += row.amount
            observed_in += max(cash_effect(row), ZERO)
            observed_out -= min(cash_effect(row), ZERO)
        elif as_of - timedelta(days=59) <= row.date < as_of - timedelta(days=29):
            previous_revenue += row.amount if row.kind in ('income', 'receivable') else -row.amount if row.kind == 'refund' else ZERO
            previous_expenses += row.amount if row.kind in ('expense', 'payable') else ZERO
            if row.kind in ('expense', 'payable'):
                previous_categories[row.category] += row.amount
        direction = 'inflow' if row.kind in ('income', 'receivable', 'loan_disbursement') else 'outflow'
        if row.kind == 'transfer':
            continue
        due = row.due_date if row.status == 'pending' else row.date if row.date > as_of else None
        if row.status == 'pending' and not due:
            undated.append({'source': 'transaction', 'id': row.pk, 'amount': str(row.amount), 'direction': direction})
            continue
        if due and due <= as_of and row.status == 'pending':
            overdue.append({'source': 'transaction', 'id': row.pk, 'date': due.isoformat(), 'amount': str(row.amount), 'direction': direction, 'description': row.description,
                            'reference': row.reference, 'recorded_note': row.notes[:1000], 'days_overdue': (as_of-due).days})
            if direction == 'inflow':
                continue  # Never presume overdue receipts will arrive tomorrow.
            due = as_of + timedelta(days=1)
            limitations.append(f'Overdue payable transaction {row.pk} stress-tested on the next day; actual timing is unknown.')
        if due and as_of < due <= end:
            events.append(CashEvent(id=f'tx:{row.pk}', source='transaction', source_id=row.pk, date=due.isoformat(), amount=row.amount,
                                   direction=direction, category=row.category, description=row.description,
                                   payroll=row.category.casefold() in ('payroll', 'salary', 'salaries', 'wages'),
                                   critical=row.is_critical, basis='assumed payment on recorded due date'))
    recurring = list(business.recurring_obligations.filter(active=True).order_by('pk')[:1001])
    if len(recurring) > 1000:
        limitations.append('Recurring commitment limit exceeded; projection blocked.')
        capped = True
    recurring_total = ZERO
    for row in recurring[:1000]:
        for index in range(0, 1201):
            due = row.next_due + (timedelta(weeks=index) if row.frequency == 'weekly' else relativedelta(years=index) if row.frequency == 'yearly' else relativedelta(months=index))
            if due > end:
                break
            if as_of < due <= end and (row.pk, due) not in covered:
                if row.direction == 'outflow':
                    recurring_total += row.amount
                events.append(CashEvent(id=f'rec:{row.pk}:{due}', source='recurring', source_id=row.pk, date=due.isoformat(), amount=row.amount,
                                       direction=row.direction, category=row.category, description=row.description,
                                       payroll=row.category.casefold() in ('payroll', 'salary', 'salaries', 'wages'), critical=row.is_critical,
                                       basis='assumed recurring commitment; linked invoice occurrences suppressed'))
    if any(r.next_due < as_of - timedelta(days=365 * 20) for r in recurring):
        capped = True
        limitations.append('Very old recurring start dates require review; recurrence expansion is bounded.')
    if len(events) > 1000:
        capped = True
        limitations.append('More than 1,000 dated events require a narrower reviewed plan; projection blocked.')
        events = events[:1000]
    complete = bool(business.cash_records_complete and cash is not None and not capped and not foreign_currency and not undated)
    projection = cash_timeline(cash, events, as_of, days, Decimal(policy['reserve'])) if complete else {'available': False, 'reason': 'Confirm opening cash, currency consistency, dated obligations and complete records before estimating liquidity.'}
    state = {'business_id': str(business.pk), 'currency': business.currency, 'as_of': as_of.isoformat(), 'end_date': end.isoformat(),
             'known_cash': str(cash) if cash is not None else None, 'cash_basis': 'calculated from recorded paid movements and opening balance' if cash is not None else 'unknown',
             'opening_date': business.opening_date.isoformat(),
             'opening_balance': str(business.opening_balance) if business.opening_balance is not None else None,
             'complete': complete, 'record_count': len(rows), 'policy': policy,
             'period_start': (as_of - timedelta(days=29)).isoformat(), 'events': [event.model_dump(mode='json') for event in sorted(events, key=lambda e: (e.date, e.id))],
             'undated': undated, 'overdue': overdue, 'projection': projection, 'limitations': list(dict.fromkeys(limitations)),
             'trends': {k: str(money(v)) for k, v in {'revenue': current_revenue, 'expenses': current_expenses, 'previous_revenue': previous_revenue,
                        'previous_expenses': previous_expenses, 'cash_inflows': observed_in, 'cash_outflows': observed_out, 'recurring_outflows': recurring_total}.items()},
             'expense_categories': [{'category': key, 'amount': str(money(value)), 'previous_amount': str(money(previous_categories[key])), 'share_percent': str(money(value / current_expenses * 100)) if current_expenses else None} for key, value in sorted(categories.items(), key=lambda item: -item[1])]}
    state['fingerprint'] = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    return state
