"""Bounded combined search and explicit invoice recoveries; no ledger writes."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from itertools import combinations

from pydantic import Field, model_validator

from .schemas import StrictModel
from .scenario_engine import compare_plans, evaluate_plan, suggested_plans


class InvoiceRecovery(StrictModel):
    event_id: str = Field(max_length=100)
    amount: Decimal = Field(gt=0, le=1000000000, decimal_places=2)
    date: date


class RecoveryRequest(StrictModel):
    recoveries: list[InvoiceRecovery] = Field(default_factory=list, max_length=8)
    target_reserve: Decimal | None = Field(default=None, ge=0, le=1000000000, decimal_places=2)

    @model_validator(mode='after')
    def unique(self):
        if len({r.event_id for r in self.recoveries}) != len(self.recoveries):
            raise ValueError('Each invoice can be included once; combine its assumed partial amount in one row.')
        return self


def recovery_case(state, request):
    request = request if isinstance(request, RecoveryRequest) else RecoveryRequest.model_validate(request)
    authorized = {f"tx:{r['id']}" for r in state['overdue'] if r['direction'] == 'inflow' and r['date'] < state['as_of']}
    if any(r.event_id not in authorized for r in request.recoveries):
        raise ValueError('Recovery assumptions require unpaid overdue invoices from this financial snapshot.')
    working = deepcopy(state)
    target = request.target_reserve if request.target_reserve is not None else Decimal(state['policy']['reserve'])
    working['policy']['reserve'] = str(target)
    actions = [{'kind': 'collect', 'event_id': r.event_id, 'amount': str(r.amount), 'date': r.date.isoformat()} for r in request.recoveries]
    plan = evaluate_plan(working, {'name': 'Explicit invoice recovery assumptions', 'actions': actions})
    baseline = evaluate_plan(working, {'name': 'Recorded schedule without overdue recovery', 'actions': []})
    return {'kind': 'invoice_recovery_v1', 'currency': state['currency'], 'as_of': state['as_of'],
            'source_fingerprint': state['fingerprint'], 'target_reserve': str(target), 'plan': plan, 'baseline': baseline,
            'assumptions': request.model_dump(mode='json'),
            'included_upcoming': state['collection_event_ids'], 'new_recovery_references': [r.event_id for r in request.recoveries],
            'basis': 'Upcoming receipts already in the baseline are not added again. Only authorized unpaid overdue invoices may be recovered. Customer agreement and actual receipt remain unknown.'}


def combined_solutions(state, no_borrowing=True, target_reserve=None):
    working = deepcopy(state)
    if target_reserve is not None:
        target = Decimal(str(target_reserve))
        if not target.is_finite() or not 0 <= target <= 1000000000:
            raise ValueError('Use a bounded reserve target.')
        working['policy']['reserve'] = str(target)
    if not state['complete']:
        return {'comparison': compare_plans(working, [{'name': 'Recorded schedule', 'actions': []}]), 'evaluated': 1, 'search_limit': 64}
    tomorrow = (date.fromisoformat(state['as_of'])+timedelta(days=1)).isoformat()
    candidates = []
    excluded = []
    contexts = {f"tx:{r['transaction_id']}": r for r in state.get('collection_context', [])}
    for row in sorted(state['overdue'], key=lambda r: -Decimal(r['amount'])):
        if row['direction'] == 'inflow' and row['date'] < state['as_of']:
            reference = f"tx:{row['id']}"
            context = contexts.get(reference, {})
            promised = context.get('promised_date')
            if context.get('dispute_status') == 'active' or (promised and promised > state['end_date']):
                excluded.append(reference)
                continue
            assumed = max(tomorrow, promised) if promised else tomorrow
            candidates.append({'kind': 'collect', 'event_id': reference, 'amount': row['amount'], 'date': assumed})
        if len(candidates) >= 4:
            break
    for plan in suggested_plans(state):
        if len(plan['actions']) == 1:
            action = plan['actions'][0]
            if not no_borrowing or action['kind'] != 'finance':
                candidates.append(action)
    candidates = candidates[:8]
    specs = [{'name': 'Recorded schedule', 'actions': []}]
    for size in (1, 2, 3):
        for subset in combinations(candidates, size):
            refs = [a['event_id'] for a in subset if a.get('event_id')]
            if len(refs) != len(set(refs)):
                continue
            specs.append({'name': f'Bounded combination {len(specs)} ({size} actions)', 'actions': list(subset)})
            if len(specs) >= 64:
                break
        if len(specs) >= 64:
            break
    evaluated = [evaluate_plan(working, spec) for spec in specs]
    evaluated.sort(key=lambda p: (not p['feasible'], Decimal(p.get('remaining_gap', 'Infinity')),
                                  Decimal(p['borrowing']), Decimal(p['financing_cost']), p['action_count']))
    final = [{'name': 'Recorded schedule', 'actions': []}]
    final += [{'name': p['name'], 'actions': p['actions']} for p in evaluated if p['name'] != 'Recorded schedule'][:7]
    comparison = compare_plans(working, final, allow_borrowing=not no_borrowing)
    return {'comparison': comparison, 'evaluated': len(specs), 'search_limit': 64, 'max_actions': 3,
            'target_reserve': working['policy']['reserve'],
            'excluded_recovery_references': excluded,
            'pruning': 'At most four largest overdue receipts and eight candidate actions; subsets of at most three actions, at most 64 evaluations. Duplicate event actions excluded. This is not global optimization.',
            'basis': 'All recoveries and counterparty changes are conditional assumptions. Active disputes and promises beyond the horizon are excluded from automatic candidates; recorded future promises are not accelerated without an explicit owner scenario. A feasible action set may still leave a reserve gap.'}
