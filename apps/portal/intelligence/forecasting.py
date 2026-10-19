"""Small interpretable operating models, nested time-ordered evaluation, Decimal cash.

Schedules are not replayed into past folds: historical as-known statuses are absent.
No fitted ML, calibrated interval, or prediction-accuracy guarantee is claimed.
"""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from ..engine import cash_effect, forecast, money

ZERO = Decimal('0')
METHODS = ('moving_average', 'last_week', 'exponential', 'weekday')


def operating_series(business, as_of):
    rows = list(business.transactions.filter(archived=False, status='paid', currency=business.currency,
        date__gte=max(business.opening_date, as_of-timedelta(days=729)), date__lte=as_of)
        .exclude(kind__in=['transfer', 'loan_disbursement', 'loan_repayment']).order_by('date', 'pk')[:20001])
    if not rows or len(rows) > 20000:
        return []
    by_day = {}
    for row in rows:
        pair = by_day.setdefault(row.date, [ZERO, ZERO])
        effect = cash_effect(row)
        pair[0] += max(effect, ZERO)
        pair[1] -= min(effect, ZERO)
    return [(rows[0].date+timedelta(days=i), *by_day.get(rows[0].date+timedelta(days=i), [ZERO, ZERO]))
            for i in range((as_of-rows[0].date).days+1)]


def predict(training, horizon, method):
    window = training[-90:]
    if not window:
        return []
    means = [sum((r[c] for r in window), ZERO)/len(window) for c in (1, 2)]
    if method == 'last_week':
        means = [sum((r[c] for r in window[-7:]), ZERO)/len(window[-7:]) for c in (1, 2)]
    elif method == 'exponential':
        means = [window[0][c] for c in (1, 2)]
        for row in window[1:]:
            means = [Decimal('.2')*row[c]+Decimal('.8')*means[c-1] for c in (1, 2)]
    result = []
    for i in range(1, horizon+1):
        day = training[-1][0]+timedelta(days=i)
        pair = means
        if method == 'weekday' and len(training) >= 56:
            matching = [r for r in training[-84:] if r[0].weekday() == day.weekday()]
            pair = [sum((r[c] for r in matching), ZERO)/len(matching) for c in (1, 2)]
        result.append((day, *pair))
    return result


def eligible(training):
    return len(training) >= 56 and sum(bool(r[1] or r[2]) for r in training) >= 20


def choose_method(training, horizon):
    scores = {m: [] for m in METHODS}
    for offset in (3*horizon, 2*horizon, horizon):
        prior, observed = training[:-offset], training[-offset:][:horizon]
        if not eligible(prior) or len(observed) != horizon:
            continue
        actual = sum((r[1]-r[2] for r in observed), ZERO)
        for method in METHODS:
            expected = sum((r[1]-r[2] for r in predict(prior, horizon, method)), ZERO)
            scores[method].append(abs(expected-actual))
    if len(scores['moving_average']) < 3:
        return 'moving_average', 'Fewer than three valid training-only selection folds; retain baseline.'
    totals = {m: sum(v, ZERO) for m, v in scores.items()}
    best = min(METHODS, key=lambda m: totals[m])
    if totals[best] < totals['moving_average']*Decimal('.95'):
        return best, 'Chosen only after at least 5% lower absolute error on three training-only selection folds.'
    return 'moving_average', 'No candidate cleared the 5% improvement threshold; retain baseline.'


def evaluate_series(series):
    results = []
    for horizon in (7, 15, 30, 90):
        folds = []
        for offset in (4*horizon, 3*horizon, 2*horizon, horizon):
            training, observed = series[:-offset], series[-offset:][:horizon]
            if not eligible(training) or len(observed) != horizon:
                continue
            selected, reason = choose_method(training, horizon)
            actual = sum((r[1]-r[2] for r in observed), ZERO)
            gross = sum((r[1]+r[2] for r in observed), ZERO)
            errors = {}
            predictions = {}
            for method in (*METHODS, 'adaptive'):
                prediction = sum((r[1]-r[2] for r in predict(training, horizon, selected if method == 'adaptive' else method)), ZERO)
                errors[method] = abs(prediction-actual)
                predictions[method] = str(money(prediction))
            folds.append({'cutoff': training[-1][0].isoformat(), 'actual': actual, 'gross': gross,
                          'errors': errors, 'predictions': predictions, 'selected': selected, 'reason': reason})
        denominator = sum((abs(f['actual']) for f in folds), ZERO)
        gross = sum((f['gross'] for f in folds), ZERO)
        metrics = []
        for method in (*METHODS, 'adaptive'):
            error = sum((f['errors'][method] for f in folds), ZERO)
            metrics.append({'method': method, 'mae': str(money(error/len(folds))) if folds else None,
                            'wape': str(money(error/denominator*100)) if denominator else None})
        results.append({'horizon': horizon, 'folds': len(folds), 'metrics': metrics,
                        'denominator': str(money(denominator)), 'wape_unstable': not denominator or denominator < gross*Decimal('.1'),
                        'details': [{'cutoff': f['cutoff'], 'actual': str(money(f['actual'])), 'predictions': f['predictions'], 'selected': f['selected']} for f in folds]})
    return {'horizons': results, 'history_days': len(series),
            'basis': 'Non-overlapping outer folds; selection uses only earlier inner folds. MAE is per-horizon net movement error. WAPE denominator is sum of absolute actual horizon net cash, not revenue. Current ledger-date history, not reconstructed as-known evidence. Sparse/missing data and status edits limit reliability.'}


def forecast_with_evaluation(business, days=30):
    base = forecast(business, days)
    if not base.get('available'):
        return base
    today = timezone.localdate()
    series = operating_series(business, today)
    method, reason = choose_method(series, days)
    result = dict(base)
    # Retain the exact previous forecast when selection lacks evidence.
    if method != 'moving_average':
        # Recover the unrounded old mean, avoiding cent-rounding drift in overlays.
        old = predict(series, days, 'moving_average')
        new = predict(series, days, method)
        balance = Decimal(base['points'][0]['balance'])
        points = [base['points'][0]]
        for original, old_day, new_day in zip(base['points'][1:], old, new):
            inflow = money(Decimal(original['inflow'])-money(old_day[1])+money(new_day[1]))
            outflow = money(Decimal(original['outflow'])-money(old_day[2])+money(new_day[2]))
            balance = money(balance+inflow-outflow)
            points.append({**original, 'balance': str(balance), 'inflow': str(inflow), 'outflow': str(outflow)})
        result.update(points=points, ending_balance=str(balance), minimum_balance=str(min(Decimal(p['balance']) for p in points)))
    lowest = min(result['points'], key=lambda p: Decimal(p['balance']))
    result.update(lowest_date=lowest['date'], selected_method=method, selection_reason=reason,
                  evaluation=evaluate_series(series), baseline_ending_balance=base['ending_balance'],
                  baseline_minimum_balance=base['minimum_balance'], method=f'{method} operating estimate plus explicit schedules')
    result['limitations'] = base['limitations'] + ' Candidate selection is conditional, not a guarantee of future improvement. No trained ML or calibrated probability is claimed.'
    result['minimum_explanation'] = 'The same early cash dip may be the minimum across several horizons; compare each ending balance. Recorded schedules and estimated operating movements have different assumptions from the dated-only Decision Lab.'
    return result
