import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.decision_memory import decide, monitor_decision, policy_feedback
from apps.portal.models import FinancialDecision


def investigate(owner, business, entry, key=None):
    today = timezone.localdate()
    entry(kind='payable', category='Payroll', amount=800, status='pending', due_date=today+timedelta(days=3))
    entry(kind='payable', amount=500, status='pending', due_date=today+timedelta(days=2))
    entry(kind='receivable', amount=700, status='pending', due_date=today+timedelta(days=5))
    return run_investigation(owner, business.pk, 'Can I afford my supplier and payroll?', request_key=key)


def test_investigation_trace_evidence_and_retry_are_persistent(owner, business, entry):
    key = uuid.uuid4()
    item = investigate(owner, business, entry, key)
    again = run_investigation(owner, business.pk, item.question, request_key=key)
    assert again.pk == item.pk
    assert len(item.trace) == 5
    assert all(t['business_id'] == str(business.pk) for t in item.trace)
    assert any(n['source'] == 'transaction' for n in item.result['evidence_graph']['nodes'] if n.get('kind') == 'obligation')
    assert item.result['mode'].startswith('deterministic')
    assert FinancialDecision.objects.count() == 1


def test_decision_lifecycle_never_changes_transactions(owner, business, entry):
    item = investigate(owner, business, entry)
    decision = item.decision
    selected = item.result['recommended']
    count = business.transactions.count()
    decide(owner, business.pk, decision.pk, 'accepted', selected)
    decide(owner, business.pk, decision.pk, 'accepted', selected)
    decision.refresh_from_db()
    assert decision.events.filter(to_state='accepted').count() == 1
    monitor_decision(decision)
    decision.refresh_from_db()
    assert decision.state == 'monitoring'
    assert business.transactions.count() == count
    with pytest.raises(ValidationError):
        decide(owner, business.pk, decision.pk, 'closed')


def test_outcome_uses_review_date_actuals_not_simulation(owner, business, entry):
    item = investigate(owner, business, entry)
    decision = decide(owner, business.pk, item.decision.pk, 'accepted', item.result['recommended'])
    entry(amount=100, date=decision.review_date)
    evaluated = monitor_decision(decision, as_of=decision.review_date)
    assert evaluated.state == 'evaluated'
    assert evaluated.outcome['actual_balance'] == '1100.00'
    assert Decimal(evaluated.outcome['difference']) == 1100 - Decimal(evaluated.expected['balance_at_review'])
    monitor_decision(evaluated, as_of=decision.review_date)
    assert evaluated.events.filter(to_state='evaluated').count() == 1


def test_no_actuals_and_incomplete_data_do_not_fabricate_outcomes(owner, business, entry):
    item = investigate(owner, business, entry)
    decision = decide(owner, business.pk, item.decision.pk, 'accepted', item.result['recommended'])
    assert monitor_decision(decision, as_of=decision.review_date).outcome['status'] == 'awaiting_data'
    assert policy_feedback(business)['adjustment'] is None


def test_reject_modify_and_stale_evidence(owner, business, entry):
    item = investigate(owner, business, entry)
    selected = item.result['comparison']['plans'][0]
    decision = decide(owner, business.pk, item.decision.pk, 'modified', modified_plan={'name': 'My adjustment', 'actions': selected['actions']})
    assert decision.state == 'modified'
    decision = decide(owner, business.pk, decision.pk, 'rejected', feedback='Supplier did not agree')
    assert decide(owner, business.pk, decision.pk, 'closed').state == 'closed'
    another = run_investigation(owner, business.pk, 'Review cash')
    entry(amount=10)
    with pytest.raises(ValidationError, match='changed'):
        decide(owner, business.pk, another.decision.pk, 'accepted', another.result['recommended'])
