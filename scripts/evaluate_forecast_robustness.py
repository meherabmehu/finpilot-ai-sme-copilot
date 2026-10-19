"""Reproducible noisy/sparse synthetic experiments, never an owner accuracy claim."""
# ruff: noqa: E402
import json
import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from random import Random

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from apps.portal.intelligence.forecasting import evaluate_series, reviewed_method


def datasets():
    rng=Random(20261019)
    result={}
    for name in ('stationary_noise','weekly_noise','trend_break','sparse_invoices','near_zero_net','volatile_shocks','short_history'):
        rows=[]
        length=40 if name=='short_history' else 600
        for i in range(length):
            day=date(2024,1,1)+timedelta(days=i)
            revenue=max(0,250+rng.gauss(0,65))
            expenses=max(0,180+rng.gauss(0,50))
            if name=='weekly_noise':
                revenue += 180 if day.weekday()>=5 else 0
            elif name=='trend_break':
                revenue += 140 if i>=470 else 0
                expenses += max(0,i-400)*.2
            elif name=='sparse_invoices':
                revenue=rng.uniform(900,1800) if i%19==0 else 0
                expenses=rng.uniform(600,1400) if i%23==0 else 0
            elif name=='near_zero_net':
                expenses=max(0,revenue+rng.gauss(0,2))
            elif name=='volatile_shocks':
                revenue += 1800 if i%61==0 else 0
                expenses += 2200 if i%73==0 else 0
            rows.append((day,Decimal(str(round(revenue,2))),Decimal(str(round(expenses,2)))))
        result[name]=rows
    return result


def main():
    output=[]
    for name,rows in datasets().items():
        result=evaluate_series(rows)
        for horizon in result['horizons']:
            selected,reason=reviewed_method(rows,horizon['horizon'],result)
            horizon['current_deployment_selection']={'method':selected,'reason':reason,
                'note':'Selection reuses historical validation; raw adaptive outer-fold errors below do not estimate performance of the added deployment gate.'}
        output.append({'dataset':name,'synthetic':True,**result})
    destination=Path('test-results/final-forecast-robustness.json')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,indent=2),encoding='utf-8')
    for case in output:
        for horizon in case['horizons']:
            metrics={m['method']:m for m in horizon['metrics']}
            print(json.dumps({'dataset':case['dataset'],'horizon':horizon['horizon'],'folds':horizon['folds'],
                'denominator':horizon['denominator'],'unstable':horizon['wape_unstable'],
                'moving_average':metrics['moving_average'],'adaptive':metrics['adaptive']}))


if __name__=='__main__':
    main()
