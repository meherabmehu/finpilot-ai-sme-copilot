"""Measured local synthetic comparisons; no external data, AI or accuracy claim."""
# ruff: noqa: E402
import json
import os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from apps.portal.models import Business
from apps.portal.intelligence.forecasting import operating_series, evaluate_series, forecast_with_evaluation

if not settings.DEBUG or settings.HOSTED:
    raise RuntimeError('This comparison requires explicitly synthetic local fixtures.')
rows = []
for business in Business.objects.filter(is_demo=True, name__in=['Competition Synthetic Retail', 'Competition Synthetic Restaurant']):
    # Fixed pre-demo cutoff: later explicitly entered browser receipts must not
    # silently change this reproducible historical comparison.
    from datetime import timedelta
    cutoff = business.opening_date+timedelta(days=499)
    result = evaluate_series(operating_series(business, cutoff))
    forecasts = []
    for horizon in (7, 15, 30, 90):
        value = forecast_with_evaluation(business, horizon)
        forecasts.append({k: value[k] for k in ('selected_method', 'selection_reason', 'minimum_balance', 'lowest_date', 'ending_balance', 'baseline_ending_balance')})
    rows.append({'synthetic_business': business.name, 'evaluation_as_of': cutoff.isoformat(), 'evaluation': result, 'forecasts': forecasts})
if len(rows) != 2:
    raise RuntimeError('Run seed_competition_demo first; no production data will be substituted.')
Path('test-results/competition-forecasts.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
for row in rows:
    print(row['synthetic_business'])
    for horizon in row['evaluation']['horizons']:
        selected = [m for m in horizon['metrics'] if m['method'] in ('moving_average', 'adaptive')]
        print(json.dumps({'horizon': horizon['horizon'], 'folds': horizon['folds'], 'denominator': horizon['denominator'], 'metrics': selected}))
