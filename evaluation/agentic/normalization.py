"""Serialize/aggregate actual application output; no oracle or scenario-ID dispatch.

Unexposed diagnostics stay absent. Do not reconstruct a second cash/decision engine here.
"""
from datetime import date, timedelta
from decimal import Decimal

from apps.portal.engine import money
from apps.portal.intelligence.financing import financing_assessment
from apps.portal.intelligence.issue_detection import health_dimensions


def calculations(state, comparison, result):
    projection, trends = state['projection'], state['trends']
    values = {k: state.get(k) for k in ('known_cash', 'opening_balance', 'record_count')}
    values.update({
        'projection_available': str(bool(projection.get('available'))),
        'blocking_reasons': [] if state['complete'] else [projection['reason']],
        'state_fingerprint': state['fingerprint'], 'event_count': str(len(state['events'])),
        'horizon_end_date': state['end_date'], 'undated_pending_count': str(len(state['undated'])),
        'revenue_30d': trends['revenue'], 'expenses_30d': trends['expenses'],
        'previous_expenses_30d': trends['previous_expenses'], 'previous_revenue_30d': trends['previous_revenue'],
        'recurring_outflows_horizon': trends['recurring_outflows'],
        'overdue_receivable_total': result['analysis']['overdue_total'],
    })
    if projection.get('available'):
        values.update({k: projection[k] for k in ('minimum_balance', 'ending_balance', 'funding_gap', 'intraday_gap')})
        values.update({'date_of_cash_minimum': projection['lowest_date'], 'first_shortfall_date': projection['first_shortfall'],
                       'reserve_breach_date': projection['reserve_breach']})
        points = projection['points']
        values['intraday_low_date'] = min(points, key=lambda p: Decimal(p['payment_first_low']))['date']
    events = state['events']
    def total(items):
        return str(money(sum((Decimal(e['amount']) for e in items), Decimal('0'))))
    for direction in ('inflow', 'outflow'):
        values[f'{direction}s_horizon'] = total(e for e in events if e['direction'] == direction)
    values['outflows_7d'] = total(e for e in events if e['direction'] == 'outflow' and (
        date.fromisoformat(e['date']) <= date.fromisoformat(state['as_of']) + timedelta(days=7)))
    values['payroll_total_horizon'] = total(e for e in events if e['direction'] == 'outflow' and e['payroll'])
    values['overdue_payable_total'] = total(e for e in state['overdue'] if e['direction'] == 'outflow')
    values['recurring_occurrence_dates'] = [e['date'] for e in events if e['source'] == 'recurring']
    categories = state['expense_categories']
    values['largest_category'] = categories[0]['category'] if categories else None
    values['largest_category_share'] = categories[0]['share_percent'] if categories else None
    issues = {i['code'] for i in result['issues']}
    values['expense_increase_breaches_policy'] = str('expense_increase' in issues)
    values['concentration_breaches_policy'] = str('expense_concentration' in issues)
    coverage = next((h['value'] for h in health_dimensions(state) if h['name'] == 'Cash coverage (days)'), None)
    if coverage is not None:
        values['cash_coverage_days'] = coverage
    plans = comparison['plans']
    if plans:
        values['deferred_liabilities'] = plans[0]['deferred_liabilities']
        values['deferred_liabilities_baseline'] = next((p['deferred_liabilities'] for p in plans if not p['actions']), None)
    finance = next((a for p in plans for a in p['actions'] if a['kind'] == 'finance'), None)
    if finance:
        assessment = financing_assessment(state, finance['amount'], finance['annual_rate'], finance['months'], finance['fee'])
        repayment = assessment['repayment']
        values.update({'loan_payment': repayment['payment'], 'loan_payment_stressed': assessment['rate_plus_two_points_payment'],
                       'financing_cost': repayment['financing_cost'], 'financing_cost_with_fee': repayment['financing_cost'],
                       'total_cost_including_principal': repayment['total_cost'], 'loan_first_month_interest': repayment['schedule'][0]['interest'],
                       'repayment_total': repayment['total_repayment'],
                       'payment_exceeds_historical_net_cash': str(assessment['payment_exceeds_historical_net_cash'])})
    # Optional, real diagnostics added by the application stay optional for old snapshots.
    values.update(state.get('diagnostics', {}))
    return {k: str(v) if isinstance(v, (int, bool)) else v for k, v in values.items()}
