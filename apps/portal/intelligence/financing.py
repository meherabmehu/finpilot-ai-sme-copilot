"""Debt sensitivity derived from recorded commitments, never lender approval claims."""

from datetime import date, timedelta
from decimal import Decimal
from ..engine import loan_schedule, money
from .scenario_engine import evaluate_plan


def financing_assessment(state, principal, annual_rate, months, fee=0):
    result = loan_schedule(principal, annual_rate, months, fee)
    stressed = loan_schedule(principal, Decimal(str(annual_rate))+2, months, fee)
    surplus = Decimal(state['trends']['cash_inflows'])-Decimal(state['trends']['cash_outflows'])
    date_value = (date.fromisoformat(state['as_of'])+timedelta(days=1)).isoformat()
    evaluated = evaluate_plan(state, {'name': 'Financing sensitivity', 'actions': [{'kind': 'finance', 'date': date_value,
                              'amount': str(principal), 'annual_rate': str(annual_rate), 'months': months, 'fee': str(fee)}]})
    return {'currency': state['currency'], 'need_estimate': state['projection'].get('funding_gap'),
            'historical_30_day_net_cash': str(money(surplus)), 'repayment': result, 'rate_plus_two_points_payment': stressed['payment'],
            'payment_exceeds_historical_net_cash': Decimal(result['payment']) > surplus, 'cash_impact': evaluated,
            'limitation': 'Affordability indicator only. Historical cash is not guaranteed repayment capacity; no available credit, approval or customer agreement is inferred. Compare collection/payment alternatives first.'}
