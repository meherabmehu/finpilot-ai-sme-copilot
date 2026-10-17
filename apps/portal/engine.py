"""Deterministic, Decimal-only financial calculations; never execute model code."""

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from django.utils import timezone

D = Decimal
ZERO = D("0")
CENT = D("0.01")


def money(value):
    return D(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def cash_effect(row):
    if row.status != "paid":
        return ZERO
    if row.kind in ("income", "receivable", "loan_disbursement"):
        return row.amount
    if row.kind in ("expense", "payable", "refund", "loan_repayment"):
        return -row.amount
    return ZERO


def summary(business, start=None, end=None):
    end = end or timezone.localdate()
    rows = business.transactions.filter(archived=False, date__lte=end)
    period = rows.filter(date__gte=start) if start else rows
    revenue = sum((r.amount for r in period if r.kind in ("income", "receivable")), ZERO)
    refunds = sum((r.amount for r in period if r.kind == "refund"), ZERO)
    expenses = sum((r.amount for r in period if r.kind in ("expense", "payable")), ZERO)
    cash_rows = rows.filter(date__gte=business.opening_date)
    cash = business.opening_balance + sum((cash_effect(r) for r in cash_rows), ZERO) if business.opening_balance is not None else None
    inflows = sum((max(cash_effect(r), ZERO) for r in period), ZERO)
    outflows = sum((-min(cash_effect(r), ZERO) for r in period), ZERO)
    net = revenue - refunds - expenses
    return {
        "revenue": revenue - refunds,
        "expenses": expenses,
        "operating_surplus": net,
        "cash": cash,
        "inflows": inflows,
        "outflows": outflows,
        "receivables": sum((r.amount for r in rows if r.kind == "receivable" and r.status == "pending"), ZERO),
        "payables": sum((r.amount for r in rows if r.kind == "payable" and r.status == "pending"), ZERO),
        "count": period.count(),
        "margin": money(net / (revenue - refunds) * 100) if revenue != refunds else None,
    }


def monthly_chart(business, months=6):
    today = timezone.localdate()
    anchor = today.year * 12 + today.month - 1
    keys = [divmod(anchor - i, 12) for i in reversed(range(months))]
    labels, revenues, expenses = [], [], []
    for year, month0 in keys:
        from datetime import date

        start = date(year, month0 + 1, 1)
        next_year, next_month0 = divmod(year * 12 + month0 + 1, 12)
        end = min(date(next_year, next_month0 + 1, 1) - timedelta(days=1), today)
        values = summary(business, start, end)
        labels.append(start.strftime("%b"))
        revenues.append(str(values["revenue"]))
        expenses.append(str(values["expenses"]))
    return {"labels": labels, "revenue": revenues, "expenses": expenses}


def forecast(business, days=30, as_of=None):
    if days not in (7, 15, 30, 90):
        raise ValueError("Choose 7, 15, 30 or 90 days.")
    today = as_of or timezone.localdate()
    current = summary(business, end=today)
    if business.transactions.filter(archived=False).exclude(currency=business.currency).exists():
        return {'available': False, 'reason': 'Mixed-currency records block forecasts; no implicit exchange conversion is allowed.'}
    if current["cash"] is None:
        return {"available": False, "reason": "Set a verified opening balance and date to forecast cash."}
    if not business.cash_records_complete:
        return {"available": False, "reason": "Review and confirm cash record completeness in My Business before forecasting."}
    history = list(
        business.transactions.filter(
            archived=False, status="paid", date__gte=max(business.opening_date, today - timedelta(days=89)), date__lte=today
        ).exclude(kind__in=["transfer", "loan_disbursement", "loan_repayment"])
    )
    if not history:
        return {"available": False, "reason": "Add actual cash records before creating a historical baseline."}
    span = min(90, (today - min(r.date for r in history)).days + 1)
    daily_in = sum((max(cash_effect(r), ZERO) for r in history), ZERO) / span
    daily_out = sum((-min(cash_effect(r), ZERO) for r in history), ZERO) / span
    scheduled_in, scheduled_out = defaultdict(lambda: ZERO), defaultdict(lambda: ZERO)
    covered = set(business.transactions.filter(archived=False, recurring_obligation__isnull=False).values_list('recurring_obligation_id', 'due_date', 'date'))
    covered = {(pk, due or day) for pk, due, day in covered}
    for row in business.transactions.filter(
        archived=False, status="pending", due_date__gt=today, due_date__lte=today + timedelta(days=days)
    ):
        if row.kind in ("income", "receivable"):
            scheduled_in[row.due_date] += row.amount
        elif row.kind in ("expense", "payable"):
            scheduled_out[row.due_date] += row.amount
    from dateutil.relativedelta import relativedelta

    for obligation in business.recurring_obligations.filter(active=True):
        for index in range(0, 1201):
            if obligation.frequency == "weekly":
                due = obligation.next_due + timedelta(weeks=index)
            elif obligation.frequency == "yearly":
                due = obligation.next_due + relativedelta(years=index)
            else:
                due = obligation.next_due + relativedelta(months=index)
            if due > today + timedelta(days=days):
                break
            if due > today and (obligation.pk, due) not in covered:
                target = scheduled_in if obligation.direction == 'inflow' else scheduled_out
                target[due] += obligation.amount
    # Scheduled obligations are added explicitly: baseline may overlap them; disclose conservatism.
    balance = current["cash"]
    adverse = balance
    points = [{"date": today.isoformat(), "balance": str(balance), "inflow": "0", "outflow": "0"}]
    for offset in range(1, days + 1):
        day = today + timedelta(days=offset)
        balance = money(balance + daily_in - daily_out + scheduled_in[day] - scheduled_out[day])
        adverse = money(adverse - daily_out - scheduled_out[day])
        points.append(
            {
                "date": day.isoformat(),
                "balance": str(balance),
                "inflow": str(money(daily_in + scheduled_in[day])),
                "outflow": str(money(daily_out + scheduled_out[day])),
            }
        )
    return {
        "available": True,
        "points": points,
        "ending_balance": str(balance),
        "history_days": span,
        "active_history_days": len({r.date for r in history}),
        "reliability": 'Limited history: fewer than 30 calendar days or 10 active days. Treat this baseline as low confidence.' if span < 30 or len({r.date for r in history}) < 10 else 'Unvalidated baseline, not a prediction guarantee. Inspect walk-forward error before relying on it.',
        "adverse_ending_balance": str(adverse),
        "adverse_assumption": 'Sensitivity only: no future receipts (historical or scheduled), unchanged historical outflows plus dated payments. Not a probability estimate.',
        "method": '90-day-window paid operating cash moving average plus explicit schedules',
        "overlap_warning": 'Historical averages may already contain similar recurring costs. Explicit linked invoice/recurrence occurrences are counted once, but unlinked duplicates and historical-pattern overlap cannot be inferred safely.',

        "daily_inflow": str(money(daily_in)),
        "daily_outflow": str(money(daily_out)),
        "minimum_balance": str(min(D(p["balance"]) for p in points)),
        "limitations": "Assumption-based moving average, not a trained model or confidence interval. Scheduled invoices and recurring commitments are additional to historical averages and may overlap historical patterns. Linked invoice/recurrence occurrences are counted once; avoid unlinked duplicate obligations. Pending collections are uncertain; record completeness is user-confirmed. No seasonality or guaranteed accuracy.",
    }


def backtest(business):
    """Ledger-date walk-forward evaluation of the operating moving-average component.

    Current pending schedules are NOT replayed backwards as if known at cutoffs.
    No historical as-known schedule/status snapshots exist; disclose that limit.
    """
    today = timezone.localdate()
    folds, errors, actuals, gross_actuals = [], [], [], []
    for offset in (28, 21, 14, 7):
        cutoff = today - timedelta(days=offset)
        history = list(business.transactions.filter(
            archived=False, currency=business.currency, status='paid',
            date__gte=max(business.opening_date, cutoff-timedelta(days=89)), date__lte=cutoff
        ).exclude(kind__in=['transfer', 'loan_disbursement', 'loan_repayment']))
        if len(history) < 30:
            continue
        span = (cutoff - min(r.date for r in history)).days + 1
        if span < 30 or len({r.date for r in history}) < 10:
            continue
        predicted = sum((cash_effect(r) for r in history), ZERO) / span * 7
        observed = list(business.transactions.filter(
            archived=False, currency=business.currency, status='paid', date__gt=cutoff, date__lte=cutoff+timedelta(days=7)
        ).exclude(kind__in=['transfer', 'loan_disbursement', 'loan_repayment']))
        actual = sum((cash_effect(r) for r in observed), ZERO)
        gross = sum((abs(cash_effect(r)) for r in observed), ZERO)
        error = abs(predicted-actual)
        errors.append(error)
        actuals.append(abs(actual))
        gross_actuals.append(gross)
        folds.append({'cutoff': cutoff.isoformat(), 'horizon_days': 7, 'training_days': span,
                      'predicted_net_cash': str(money(predicted)), 'actual_net_cash': str(money(actual)),
                      'absolute_error': str(money(error)), 'gross_cash_movement': str(money(gross))})
    denominator, gross = sum(actuals), sum(gross_actuals)
    unstable = not denominator or (gross > 0 and denominator < gross * D('0.10'))
    return {
        'folds': len(errors), 'fold_details': folds, 'horizon_days': 7,
        'mae': str(money(sum(errors)/len(errors))) if errors else None,
        'wape': str(money(sum(errors)/denominator*100)) if denominator else None,
        'net_cash_denominator': str(money(denominator)),
        'wape_unstable': unstable,
        'note': 'Weekly operating net-cash baseline, 90-day training window, ledger-date walk-forward; not the full schedule-overlay forecast. Net WAPE divides absolute errors by sum of absolute weekly net cash, not gross receipts. Near-zero net cash can make it unstable (flagged below 10% of gross movement). No accuracy or calibrated-interval claim; 15/30/90-day horizons and historical as-known schedule/status snapshots are not evaluated.',
    }


def simulate(business, assumptions):
    baseline = summary(business, timezone.localdate() - timedelta(days=29))
    revenue_change = D(str(assumptions.get("revenue_change", 0)))
    expense_change = D(str(assumptions.get("expense_change", 0)))
    employees = D(str(assumptions.get("employees", 0)))
    salary = D(str(assumptions.get("salary", 0)))
    inventory = D(str(assumptions.get("inventory", 0)))
    marketing = D(str(assumptions.get("marketing", 0)))
    collection_delay = D(str(assumptions.get("collection_delay", 0)))
    supplier_delay = D(str(assumptions.get("supplier_delay", 0)))
    financing = D(str(assumptions.get("financing", 0)))
    repayment = D(str(assumptions.get("repayment", 0)))
    rev = money(baseline["revenue"] * (1 + revenue_change / 100))
    exp = money(baseline["expenses"] * (1 + expense_change / 100) + employees * salary + marketing)
    cash_delta = money(
        rev - baseline["revenue"] - (exp - baseline["expenses"]) - inventory - collection_delay + supplier_delay + financing - repayment
    )
    return {
        "baseline_revenue": str(baseline["revenue"]),
        "revenue": str(rev),
        "baseline_expenses": str(baseline["expenses"]),
        "expenses": str(exp),
        "operating_surplus": str(rev - exp),
        "cash_delta": str(cash_delta),
        "assumption": "30-day illustration: incremental revenue and operating costs assumed paid in-period. Inventory treated as cash use, not immediate expense. Delayed collections/payments are explicit amounts. No automatic marketing revenue uplift. Not an accounting forecast.",
    }


def loan_schedule(principal, annual_rate, months, fee=0):
    principal, annual_rate, fee = D(str(principal)), D(str(annual_rate)), D(str(fee))
    if (
        not principal.is_finite()
        or not annual_rate.is_finite()
        or not fee.is_finite()
        or principal <= 0
        or annual_rate < 0
        or not 1 <= months <= 600
        or fee < 0
    ):
        raise ValueError("Invalid financing inputs.")
    rate = annual_rate / 1200
    payment = money(principal / months if rate == 0 else principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1))
    balance, schedule, total_interest = principal, [], ZERO
    for month in range(1, months + 1):
        interest = money(balance * rate)
        paid = money(balance + interest) if month == months else min(payment, money(balance + interest))
        capital = paid - interest
        balance = money(balance - capital)
        total_interest += interest
        schedule.append(
            {"month": month, "payment": str(paid), "interest": str(interest), "principal": str(capital), "balance": str(balance)}
        )
    return {
        "principal": str(money(principal)), "annual_rate": str(annual_rate), "months": months,
        "payment": str(payment),
        "total_repayment": str(money(principal + total_interest)),
        "financing_cost": str(money(total_interest + fee)),
        "total_interest": str(total_interest),
        "fees": str(fee),
        "total_cost": str(money(principal + total_interest + fee)),
        "schedule": schedule,
    }
