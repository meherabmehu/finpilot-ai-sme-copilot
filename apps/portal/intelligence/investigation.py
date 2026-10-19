"""Bounded deterministic investigation with persisted evidence and tool traces."""

import uuid
from datetime import date, timedelta, datetime
import calendar
import re
import time

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from ..access import authorized_business, audit
from ..models import Business, FinancialIssue, Investigation, FinancialDecision, DecisionEvent
from .financial_state import build_state
from .issue_detection import detect_issues, health_dimensions, refresh_issues
from .question_analysis import analyze_question, question_comparison
from .financial_evidence import evidence_graph


def question_context(question, state):
    from .question_language import normalize_question
    text = normalize_question(question)
    missing = []
    if any(word in text for word in ('payroll', 'salary', 'wages')) and not any(e['payroll'] for e in state['events']):
        missing.append('No dated payroll obligation is recorded in this horizon. Add its amount and due date before deciding affordability.')
    if any(word in text for word in ('supplier', 'inventory')) and not any(e['direction'] == 'outflow' and not e['payroll'] for e in state['events']):
        missing.append('No dated supplier/inventory outflow is recorded in this horizon.')
    today = date.fromisoformat(state['as_of'])
    target = analyze_question(state, question)['intent'].get('reserve_target')
    if target is not None and str(target) != str(state['policy']['reserve']):
        from decimal import Decimal
        if Decimal(target) != Decimal(state['policy']['reserve']):
            missing.append('The hypothetical reserve target differs from saved Financial Preferences. Review it in Scenario Simulation or explicitly update preferences before accepting this decision.')
    requested = None
    match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
    if match:
        try:
            requested = date.fromisoformat(match.group())
        except ValueError:
            missing.append('The requested date is invalid.')
    else:
        for month in list(calendar.month_name)[1:]+list(calendar.month_abbr)[1:]:
            match = re.search(r'\b'+month.casefold()+r'\s+(?P<day>\d{1,2})(?:,?\s+(?P<year>20\d{2}))?\b', text)
            if not match:
                match = re.search(r'\b(?P<day>\d{1,2})\s+'+month.casefold()+r'(?:,?\s+(?P<year>20\d{2}))?\b', text)
            if match:
                try:
                    requested = datetime.strptime(f"{month} {match.group('day')} {match.group('year') or today.year}", '%B %d %Y' if len(month) > 3 else '%b %d %Y').date()
                except ValueError:
                    missing.append('The requested calendar date is invalid.')
                break
        for index, weekday in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
            if requested is None and weekday in text:
                requested = today + timedelta(days=(index-today.weekday()) % 7 or 7)
                break
    if requested and not today < requested <= date.fromisoformat(state['end_date']):
        missing.append('The requested date is outside the saved planning horizon. Adjust preferences and investigate again.')
    analysis = analyze_question(state, question)
    if requested and state['projection'].get('available'):
        point = next((p for p in state['projection']['points'] if p['date'] == requested.isoformat()), None)
        if point:
            analysis['sections'].insert(0, {'title': 'Requested-date cash evidence', 'lines': [
                f"On {point['date']}: closing cash {point['balance']} {state['currency']}; inflow assumptions {point['inflow']}; dated payments {point['outflow']}; source references {', '.join(point['refs']) or 'none that day'}. Prior dates also determine this balance."]})
    return {'analysis': analysis, 'requested_date': requested.isoformat() if requested else None, 'missing_information': missing,
            'interpretation': 'Guided deterministic matching of recorded payroll, supplier obligations and optional weekday/ISO date. Ambiguous supplier identities require owner review.'}


def run_investigation(user, business_id, question, issue_id=None, request_key=None, custom_plans=None):
    business = authorized_business(user, business_id, write=True)
    from .ai_grounding import scope
    if scope(question) == 'outside':
        raise ValidationError('This question is outside FinPilot financial advisory scope. Ask about business finances.')
    if not question.strip() or len(question) > 4000:
        raise ValidationError('Enter a question of 1–4,000 characters.')
    request_key = uuid.UUID(str(request_key)) if request_key else uuid.uuid4()
    existing = Investigation.objects.filter(business=business, user=user, request_key=request_key).first()
    if existing:
        return existing
    issue = get_object_or_404(FinancialIssue, pk=issue_id, business=business) if issue_id else None
    started = time.monotonic()
    trace = []

    def step(name, function):
        if len(trace) >= 6 or time.monotonic()-started > 15:
            raise ValidationError('Investigation budget reached; narrow the planning horizon and retry.')
        before = time.monotonic()
        output = function()
        trace.append({'tool': name, 'status': 'completed', 'elapsed_ms': int((time.monotonic()-before)*1000),
                      'business_id': str(business.pk)})
        return output

    state = step('get_financial_state', lambda: build_state(business))
    issues = step('diagnose_rules', lambda: detect_issues(state))
    focus = step('inspect_payment_timing', lambda: question_context(question, state))
    comparison = step('compare_counterfactual_plans', lambda: question_comparison(state, focus['analysis'], custom_plans))
    if focus['missing_information']:
        comparison['recommended'] = None
    graph = step('assemble_evidence', lambda: evidence_graph(state, comparison))
    result = {'mode': 'deterministic investigation; not a generative AI answer', 'focus': focus,
              'issues': issues, 'comparison': comparison, 'evidence_graph': graph,
              'analysis': focus['analysis'], 'health': health_dimensions(state), 'recommended': comparison['recommended'],
              'explanation': f"Planning horizon: {state['as_of']} to {state['end_date']}; dated commitments only, not guaranteed trading. Payment-date changes require counterparty agreement. "
                             'Alternatives use your dated records and explicit assumptions. Acceptance records an internal intention only; it never executes payments or contacts counterparties.',
              'next_action': 'Review dependencies and choose, modify or reject a plan.' if comparison['recommended'] else 'Complete the missing financial information before choosing a plan.'}
    with transaction.atomic():
        # Lock only while persisting; computations and any future provider calls stay outside.
        Business.objects.select_for_update().get(pk=business.pk)
        existing = Investigation.objects.filter(business=business, user=user, request_key=request_key).first()
        if existing:
            return existing
        item = Investigation.objects.create(business=business, user=user, issue=issue, question=question.strip(), request_key=request_key,
                                            snapshot=state, trace=trace, result=result)
        decision = FinancialDecision.objects.create(business=business, investigation=item, review_date=date.fromisoformat(state['end_date']))
        DecisionEvent.objects.create(decision=decision, user=user, to_state='proposed', details={'source': 'completed deterministic investigation'})
        audit(user, business, 'investigation.completed', item.pk, {'tools': len(trace), 'snapshot': state['fingerprint']})
    refresh_issues(business)
    return item
