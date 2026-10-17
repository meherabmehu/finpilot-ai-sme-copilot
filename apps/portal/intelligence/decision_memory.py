"""Explicit decision transitions and observed outcomes; never writes accounting rows."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..access import authorized_business, audit
from ..engine import summary, money, cash_effect
from ..models import FinancialDecision, DecisionEvent, Business
from .financial_state import build_state
from .scenario_engine import evaluate_plan

TRANSITIONS = {'proposed': {'accepted', 'rejected', 'modified'}, 'modified': {'accepted', 'rejected', 'modified'},
               'accepted': {'monitoring'}, 'monitoring': {'evaluated'}, 'evaluated': {'closed'}, 'rejected': {'closed'}, 'closed': set()}


@transaction.atomic
def decide(user, business_id, decision_id, target, selected_plan='', feedback='', modified_plan=None):
    business = authorized_business(user, business_id, write=True)
    business = Business.objects.select_for_update().get(pk=business.pk)
    decision = get_object_or_404(FinancialDecision.objects.select_for_update(), pk=decision_id, business=business)
    if target == decision.state and target != 'modified':
        return decision  # Retry-safe; no duplicate lifecycle events.
    if target not in TRANSITIONS.get(decision.state, set()) or target == 'evaluated':
        raise ValidationError('This decision transition is not allowed. Outcomes are evaluated by monitoring.')
    before = decision.state
    if target in ('accepted', 'modified'):
        plans = decision.investigation.result['comparison']['plans']
        selected = next((p for p in plans if p['name'] == selected_plan), None)
        if target == 'modified':
            if not modified_plan:
                raise ValidationError('A modified decision requires an explicit validated plan.')
            selected = evaluate_plan(decision.investigation.snapshot, modified_plan)
        elif decision.state == 'modified' and decision.selected_snapshot.get('name') == selected_plan:
            selected = decision.selected_snapshot
        if not selected or not selected['feasible'] or not selected['timeline'].get('available'):
            raise ValidationError('Choose a feasible evaluated plan with sufficient financial data.')
        if decision.investigation.result['focus'].get('analysis', {}).get('intent', {}).get('no_borrowing') and any(a['kind'] == 'finance' for a in selected['actions']):
            raise ValidationError('Borrowing is excluded by this investigation question. Start a new investigation to change that instruction.')
        if decision.investigation.result['focus']['missing_information']:
            raise ValidationError('Resolve the investigation’s missing information and investigate again before accepting.')
        current = build_state(business)
        if current['fingerprint'] != decision.investigation.snapshot['fingerprint']:
            raise ValidationError('Financial data or preferences changed. Run a fresh investigation before committing to a plan.')
        if target == 'modified' and decision.state == 'modified' and decision.selected_snapshot == selected and decision.feedback == feedback[:4000]:
            return decision
        decision.selected_plan = selected['name']
        decision.selected_snapshot = selected
        decision.expected = {'balance_at_review': selected['timeline']['ending_balance'], 'minimum_balance': selected['timeline']['minimum_balance'],
                             'funding_gap': selected['timeline']['funding_gap'], 'as_of': decision.investigation.snapshot['as_of'],
                             'review_date': decision.review_date.isoformat(), 'basis': 'simulated', 'currency': business.currency,
                             'dependencies': selected['dependencies']}
    decision.state, decision.feedback = target, feedback[:4000]
    decision.save()
    DecisionEvent.objects.create(decision=decision, user=user, from_state=before, to_state=target, details={'selected_plan': decision.selected_plan, 'feedback': feedback[:4000]})
    audit(user, business, 'decision.'+target, decision.pk)
    return decision


def monitor_decision(decision, as_of=None):
    """Trusted scheduled service; locks and reloads the business-scoped decision."""
    today = as_of or timezone.localdate()
    with transaction.atomic():
        item = FinancialDecision.objects.select_for_update().select_related('business', 'investigation').get(pk=decision.pk, business_id=decision.business_id)
        if item.state not in ('accepted', 'monitoring'):
            return item
        if item.state == 'accepted':
            item.state = 'monitoring'
            item.save(update_fields=['state', 'updated_at'])
            DecisionEvent.objects.create(decision=item, from_state='accepted', to_state='monitoring', details={'basis': 'internal monitoring only'})
        if today < item.review_date:
            return item
        business = item.business
        # Reconcile only actual records at the fixed review date, not current cash.
        current = build_state(business, as_of=item.review_date)
        if not current['complete'] or current['known_cash'] is None:
            item.outcome = {'status': 'awaiting_data', 'reason': 'Complete verified cash records through the fixed review date are required.'}
            item.save(update_fields=['outcome', 'updated_at'])
            return item
        historical = business.transactions.filter(archived=False, date__gt=date.fromisoformat(item.expected['as_of']), date__lte=item.review_date, status='paid')
        if not historical.exists():
            item.outcome = {'status': 'awaiting_data', 'reason': 'No actual paid activity recorded in the review period; absence is not treated as proof of performance.'}
            item.save(update_fields=['outcome', 'updated_at'])
            return item
        actual = summary(business, end=item.review_date)['cash']
        expected = Decimal(item.expected['balance_at_review'])
        # Actual minimum derives from paid ledger at every recorded day plus endpoints.
        from collections import defaultdict
        by_day = defaultdict(lambda: Decimal('0'))
        for row in historical:
            by_day[row.date] += cash_effect(row)
        running = summary(business, end=date.fromisoformat(item.expected['as_of']))['cash']
        lowest = running
        for day in sorted(by_day):
            running += by_day[day]
            lowest = min(lowest, running)
        item.outcome = {'status': 'observed', 'review_date': item.review_date.isoformat(), 'expected_balance': str(expected),
                        'actual_balance': str(actual), 'difference': str(money(actual-expected)), 'actual_minimum': str(lowest),
                        'basis': 'calculated from actual paid records; causal attribution to the plan is not established',
                        'currency': business.currency, 'data_quality': 'User-confirmed completeness; not independently audited.'}
        item.state = 'evaluated'
        item.evaluated_at = timezone.now()
        item.save()
        DecisionEvent.objects.create(decision=item, from_state='monitoring', to_state='evaluated', details=item.outcome)
        audit(None, business, 'decision.evaluated', item.pk)
        return item


def policy_feedback(business):
    observed = list(business.decisions.filter(state__in=['evaluated', 'closed'], evaluated_at__isnull=False).order_by('-evaluated_at')[:50])
    outcomes = [d for d in observed if d.outcome.get('status') == 'observed']
    if len(outcomes) < 5:
        return {'sample_size': len(outcomes), 'adjustment': None, 'explanation': 'At least five evaluated outcomes are required before suggesting a preference adjustment. Defaults remain unchanged.'}
    errors = [abs(Decimal(d.outcome['difference'])) for d in outcomes]
    mean_error = money(sum(errors)/len(errors))
    return {'sample_size': len(outcomes), 'mean_absolute_balance_difference': str(mean_error),
            'adjustment': 'Review operating reserve by the observed mean absolute balance difference.',
            'suggested_additional_reserve': str(mean_error), 'automatic_change': False,
            'explanation': 'Business-specific measured feedback, not model retraining. Owner review is required; differing decisions and incomplete records limit generalization.'}
