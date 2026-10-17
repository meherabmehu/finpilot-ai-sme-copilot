"""Rule-driven Watchtower, independent from notifications and LLM calls."""

from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import FinancialIssue
from .financial_state import build_state


def detect_issues(state):
    issues = []
    projection, policy, trends = state['projection'], state['policy'], state['trends']
    reserve = Decimal(policy['reserve'])

    def add(code, title, severity, rule, refs=(), amount=None, due=None):
        issues.append({'code': code, 'title': title, 'severity': severity, 'evidence': {
            'business_id': state['business_id'], 'currency': state['currency'], 'as_of': state['as_of'],
            'rule': rule, 'references': list(refs), 'amount': str(amount) if amount is not None else None,
            'date': due, 'limitations': state['limitations'], 'investigation_type': 'dated liquidity and alternative actions',
            'state_fingerprint': state['fingerprint'], 'basis': 'calculated' if state['complete'] else 'unknown/incomplete'}})

    if not state['complete']:
        add('incomplete_records', 'Your cash timeline needs a more reliable foundation', 'high', 'Known opening cash, one currency, complete records and dated obligations are required.')
    if state['known_cash'] is not None and Decimal(state['known_cash']) < reserve:
        add('low_cash', 'Recorded cash is below your operating reserve', 'high', 'Recorded cash < configured safety reserve.', amount=Decimal(state['known_cash']), due=state['as_of'])
    if projection.get('available'):
        if projection['first_shortfall']:
            add('negative_cash', 'Scheduled commitments could take cash below zero', 'critical', 'Minimum closing balance < 0 on the dated-only timeline.',
                refs=[e['id'] for e in state['events']], amount=projection['funding_gap'], due=projection['first_shortfall'])
        elif projection['reserve_breach']:
            add('reserve_pressure', 'Your scheduled cash falls below the safety reserve', 'high', 'Minimum closing balance < safety reserve.',
                amount=projection['funding_gap'], due=projection['reserve_breach'])
        if Decimal(projection['intraday_gap']) > 0:
            add('same_day_timing', 'Same-day collections may arrive after payments', 'high', 'Payment-first intraday balance < 0, even if daily closing cash recovers.', amount=projection['intraday_gap'])
    today = date.fromisoformat(state['as_of'])
    near = [e for e in state['events'] if date.fromisoformat(e['date']) <= today + timedelta(days=7)]
    outflows = [e for e in near if e['direction'] == 'outflow']
    cash = Decimal(state['known_cash']) if state['known_cash'] is not None else None
    if outflows and cash is not None and sum(Decimal(e['amount']) for e in outflows) > max(cash - reserve, 0):
        add('near_term_payables', 'Near-term payments exceed cash above your reserve', 'high', 'Seven-day outflows > max(known cash − reserve, 0).', [e['id'] for e in outflows], sum(Decimal(e['amount']) for e in outflows))
    if any(e['payroll'] for e in outflows) and len(outflows) >= 2:
        add('overlapping_commitments', 'Payroll overlaps other near-term cash demands', 'high', 'Recorded payroll and other payments share the next seven-day window.', [e['id'] for e in outflows])
    loan_events = [e for e in outflows if e['category'].casefold() in ('loan repayment', 'debt service')]
    if loan_events:
        add('loan_repayments', 'Loan repayments are approaching', 'medium', 'Debt-service category outflows due within seven days.', [e['id'] for e in loan_events], sum(Decimal(e['amount']) for e in loan_events))
    critical_dates = [e['date'] for e in outflows if e['payroll'] or e['critical']]
    collections = [e for e in near if e['direction'] == 'inflow' and critical_dates and e['date'] <= max(critical_dates)]
    if collections:
        add('collection_dependency', 'Critical payments depend on expected collections', 'medium', 'Unconfirmed receipts are dated before payroll or protected obligations.', [e['id'] for e in collections], sum(Decimal(e['amount']) for e in collections))
    if any(e['direction'] == 'inflow' for e in state['overdue']):
        add('overdue_receivables', 'Some customer collections are overdue', 'medium', 'Pending receivables have due dates at or before the analysis date; they are not presumed collected.', [f"tx:{e['id']}" for e in state['overdue'] if e['direction'] == 'inflow'])
    previous, current = Decimal(trends['previous_expenses']), Decimal(trends['expenses'])
    if previous > 0 and current > previous * (1 + Decimal(policy['expense_increase_percent']) / 100):
        add('expense_increase', 'Recorded expenses grew beyond your review threshold', 'medium', f"Latest 30-day expenses exceed previous 30 days by more than {policy['expense_increase_percent']}%.", amount=current - previous)
    for category in state['expense_categories'][:1]:
        if category['share_percent'] and Decimal(category['share_percent']) >= policy['concentration_percent']:
            add('expense_concentration', 'One category dominates your recorded expenses', 'medium', f"Largest category share ≥ {policy['concentration_percent']}%; concentration is not automatically overspending.", amount=category['amount'])
    if Decimal(trends['recurring_outflows']) > Decimal(trends['revenue']) and Decimal(trends['recurring_outflows']) > 0:
        add('recurring_pressure', 'Scheduled recurring costs exceed recent recorded revenue', 'medium', 'Horizon recurring cash outflows > last 30-day revenue. Different periods and incomplete future trading limit interpretation.', amount=trends['recurring_outflows'])
    return issues


@transaction.atomic
def refresh_issues(business, state=None):
    # Serialize same-business refreshes. No provider calls run under this lock.
    from ..models import Business
    Business.objects.select_for_update().get(pk=business.pk)
    state = state or build_state(business)
    now = timezone.now()
    detected = detect_issues(state)
    for values in detected:
        issue, created = FinancialIssue.objects.get_or_create(business=business, code=values['code'], defaults={
            'title': values['title'], 'severity': values['severity'], 'evidence': values['evidence'], 'surfaced_at': now})
        if not created:
            reopening = issue.status == 'resolved'
            issue.title, issue.severity, issue.evidence = values['title'], values['severity'], values['evidence']
            issue.status, issue.resolved_at = 'open', None
            if reopening:
                issue.occurrence_count += 1
            if not issue.surfaced_at or now - issue.surfaced_at >= timedelta(hours=state['policy']['issue_cooldown_hours']):
                issue.surfaced_at = now  # Eligible for UI attention; never sends a message.
            issue.save()
    FinancialIssue.objects.filter(business=business, status='open').exclude(code__in=[i['code'] for i in detected]).update(status='resolved', resolved_at=now, checked_at=now)
    return detected


def health_dimensions(state):
    """No blended or opaque score; each dimension retains its evidence and rule."""
    p, t = state['projection'], state['trends']
    outflows = Decimal(t['cash_outflows'])
    cash = Decimal(state['known_cash']) if state['known_cash'] is not None else None
    coverage = str(round(cash / (outflows / 30), 2)) if cash is not None and outflows > 0 else None
    return [
        {'name': 'Liquidity', 'value': state['known_cash'], 'basis': state['cash_basis'], 'rule': 'Opening cash + recorded paid inflows − paid outflows', 'status': 'unknown' if cash is None else 'review' if cash < Decimal(state['policy']['reserve']) else 'above configured reserve'},
        {'name': 'Cash coverage (days)', 'value': coverage, 'basis': 'calculated', 'rule': 'Known cash / average daily last-30-day paid outflows; historical indicator only', 'status': 'unknown' if coverage is None else 'historical coverage'},
        {'name': 'Upcoming obligations', 'value': str(sum(Decimal(e['amount']) for e in state['events'] if e['direction'] == 'outflow')), 'basis': 'assumed dated cash outflows', 'rule': 'Sum of scheduled outflows during policy horizon', 'status': 'review commitments'},
        {'name': 'Expense pressure', 'value': t['expenses'], 'basis': 'recorded last 30 days', 'rule': 'Compare with previous expenses ' + t['previous_expenses'], 'status': 'review trend'},
        {'name': 'Receivable exposure', 'value': str(sum(Decimal(e['amount']) for e in state['events'] if e['direction'] == 'inflow')), 'basis': 'unconfirmed future collections', 'rule': 'Scheduled inflows are not current cash', 'status': 'collection-dependent'},
        {'name': 'Data completeness', 'value': str(state['complete']), 'basis': 'user assertion and validation', 'rule': 'Opening balance, currency, due dates and cash-completeness assertion', 'status': 'usable with limitations' if state['complete'] else 'unknown'},
        {'name': 'Financing burden', 'value': str(sum(Decimal(e['amount']) for e in state['events'] if e['category'].casefold() in ('debt service', 'loan repayment') and e['direction'] == 'outflow')), 'basis': 'recorded dated obligations', 'rule': 'Known debt-service amounts only; missing debts remain unknown', 'status': 'not independently verified'},
        {'name': 'Short-term resilience', 'value': p.get('funding_gap'), 'basis': 'estimated dated-only timeline', 'rule': 'max(reserve − lowest closing balance, 0)', 'status': 'unknown' if not p.get('available') else 'review' if Decimal(p['funding_gap']) > 0 else 'no gap under recorded assumptions'},
    ]
