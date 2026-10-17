from datetime import timedelta
from decimal import Decimal, localcontext, ROUND_HALF_UP
from django.utils import timezone
from apps.portal.models import RecurringObligation, LoanProduct
from apps.portal.engine import forecast, backtest, loan_schedule
from django.urls import reverse


def test_linked_schedule_counted_once_and_gross_flows_preserved(business, entry):
    today = timezone.localdate()
    entry(date=today-timedelta(days=9), amount=100)
    due = today+timedelta(days=2)
    recurring = RecurringObligation.objects.create(business=business, description='Rent', amount=500, next_due=due)
    entry(kind='payable', status='pending', amount=500, due_date=due, recurring_obligation=recurring)
    entry(kind='receivable', status='pending', amount=300, due_date=due)
    result = forecast(business, 7)
    assert result['ending_balance'] == '970.00'  # 1100 + 70 baseline + 300 - 500
    assert result['points'][2]['inflow'] == '310.00'
    assert result['points'][2]['outflow'] == '500.00'
    assert 'Limited history' in result['reliability']
    assert result['adverse_ending_balance'] == '600.00'


def test_backtest_denominator_and_training_dates_are_explicit(business, entry):
    today = timezone.localdate()
    for day in range(120):
        entry(amount=100, date=today-timedelta(days=day))
        entry(kind='expense', amount=99, date=today-timedelta(days=day))
    entry(kind='loan_disbursement', amount=999999)  # excluded from operating-only target
    result = backtest(business)
    assert result['folds'] == 4
    assert result['mae'] == '0.00'
    assert result['wape'] == '0.00'
    assert result['wape_unstable']
    assert result['net_cash_denominator'] == '28.00'
    assert all(f['training_days'] == 90 and f['actual_net_cash'] == '7.00' for f in result['fold_details'])


def test_loan_schedule_independent_decimal_oracle():
    # Independent high-precision nominal monthly annuity calculation, then lender-style cent rounding.
    with localcontext() as ctx:
        ctx.prec = 50
        rate = Decimal('0.12')/12
        expected_payment = (Decimal(10000)*rate/(1-(1+rate)**-12)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    result = loan_schedule(10000, 12, 12, 200)
    assert Decimal(result['payment']) == expected_payment == Decimal('888.49')
    balance, interest_total = Decimal(10000), Decimal(0)
    for i in range(12):
        interest = (balance*Decimal('.01')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        paid = balance+interest if i == 11 else expected_payment
        balance -= paid-interest
        interest_total += interest
    assert interest_total == Decimal('661.86')
    assert Decimal(result['total_interest']) == interest_total
    assert result['financing_cost'] == '861.86'
    assert result['total_cost'] == '10861.86'
    assert sum(Decimal(r['payment']) for r in result['schedule']) + 200 == Decimal(result['total_cost'])
    assert loan_schedule(10000,12,12,100)['total_cost'] == '10761.86'


def test_manual_and_product_fee_assumptions_are_separate(client, owner, business):
    LoanProduct.objects.create(name='Synthetic example', provider='Demo lender', country='US', currency='USD',
                               minimum=100, maximum=20000, annual_rate=12, fee=100, min_months=1, max_months=24)
    client.force_login(owner)
    page = client.post(reverse('planning', args=[business.pk])+'?tab=loans',
                       {'amount':10000,'annual_rate':12,'months':12,'fees':200,'monthly_capacity':1000})
    assert page.status_code == 200
    assert b'10861.86' in page.content and b'10761.86' in page.content
    assert b'Product fees replace' in page.content
    assert b'Full financing cost' in page.content
