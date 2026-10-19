"""Debt sensitivity derived from recorded commitments, never lender approval claims."""

from datetime import date, timedelta
from decimal import Decimal
from ..engine import loan_schedule, money
from .scenario_engine import evaluate_plan


def financing_assessment(state, principal, annual_rate, months, fee=0):
    result = loan_schedule(principal, annual_rate, months, fee)
    stress_rate = Decimal(str(annual_rate))+2
    stressed = loan_schedule(principal, stress_rate, months, fee) if stress_rate <= 1000 else None
    # Debt proceeds are real cash, but cannot demonstrate recurring repayment capacity.
    surplus = Decimal(state['trends'].get('operating_cash_inflows', '0'))-Decimal(state['trends'].get('operating_cash_outflows', '0'))
    date_value = (date.fromisoformat(state['as_of'])+timedelta(days=1)).isoformat()
    if Decimal(str(principal)) > 1000000000 or months > 120 or Decimal(str(fee)) > 1000000000:
        return {'currency':state['currency'],'need_estimate':state['projection'].get('funding_gap'),
            'historical_30_day_net_cash':str(money(surplus)),'repayment':result,
            'rate_plus_two_points_payment':stressed['payment'] if stressed else None,
            'payment_exceeds_historical_net_cash':Decimal(result['payment'])>surplus,
            'cash_impact':{'remaining_gap':None,'financing_cost':result['financing_cost'],'deferred_liabilities':None,
                           'violations':['Quoted repayment calculation is available, but these terms exceed the bounded Decision Lab cash-impact simulator. Reserve safety remains unknown.']},
            'higher_rate_cash_impact':None,'limitation':'The custom calculator supports longer or larger quotations than the bounded planning simulator. No reserve-safety conclusion is inferred.'}
    evaluated = evaluate_plan(state, {'name': 'Financing sensitivity', 'actions': [{'kind': 'finance', 'date': date_value,
                              'amount': str(principal), 'annual_rate': str(annual_rate), 'months': months, 'fee': str(fee)}]})
    stress = evaluate_plan(state, {'name': 'Higher-rate financing sensitivity', 'actions': [{'kind': 'finance', 'date': date_value,
                              'amount': str(principal), 'annual_rate': str(stress_rate),
                              'months': months, 'fee': str(fee)}]}) if stressed else None
    return {'currency': state['currency'], 'need_estimate': state['projection'].get('funding_gap'),
            'historical_30_day_net_cash': str(money(surplus)), 'repayment': result, 'rate_plus_two_points_payment': stressed['payment'] if stressed else None,
            'payment_exceeds_historical_net_cash': Decimal(result['payment']) > surplus, 'cash_impact': evaluated, 'higher_rate_cash_impact': stress,
            'limitation': 'Affordability indicator only. Historical cash is not guaranteed repayment capacity; no available credit, approval or customer agreement is inferred. Compare collection/payment alternatives first.'}
