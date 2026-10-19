"""Owner-reported action progress, separate from ledger and decision transitions."""
from datetime import date, timedelta
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..access import authorized_business
from ..models import AuditEvent, Business, FinancialDecision

STATUSES = [('planned', 'Planned'), ('in_progress', 'In progress'), ('owner_confirmed', 'Owner confirmed task')]
READABLE_STATES = ('accepted', 'monitoring', 'evaluated', 'closed')


def roadmap_actions(decision):
    snapshot = decision.investigation.snapshot
    by_id = {event['id']: event for event in snapshot['events']}
    by_id.update({f"tx:{row['id']}": row for row in snapshot['overdue']})
    rows = []
    verbs = {'shift': 'Discuss payment or collection timing', 'split': 'Discuss a split payment',
             'collect': 'Follow up the recorded receivable', 'reduce': 'Review and confirm spending reduction',
             'finance': 'Review the entered financing assumption'}
    for index, action in enumerate(decision.selected_snapshot.get('actions', [])):
        source = by_id.get(action.get('event_id'), {})
        key = hashlib.sha256(json.dumps([index, action], sort_keys=True).encode()).hexdigest()[:24]
        day = action.get('date') or source.get('date')
        if action['kind'] == 'shift' and day:
            day = (date.fromisoformat(day)+timedelta(days=action['days'])).isoformat()
        rows.append({'key': key, 'title': verbs[action['kind']], 'description': source.get('description', 'Entered financing terms; not an available lender offer.'),
                     'reference': action.get('event_id', ''), 'plan_date': day,
                     'dependency': 'Counterparty confirmation, actual receipt and record review are required.' if action['kind'] in ('shift', 'split', 'collect') else
                                   'A lender must agree and disburse; no approval is inferred.' if action['kind'] == 'finance' else
                                   'Owner must confirm feasibility and any contractual impact before changing spending.'})
    obligations = sorted((e for e in snapshot['events'] if e['direction'] == 'outflow'), key=lambda e: e['date'])[:4]
    for event in obligations:
        recorded = next((r['date'] for r in snapshot['overdue'] if f"tx:{r['id']}" == event['id']), event['date'])
        due = date.fromisoformat(recorded)
        key = hashlib.sha256(event['id'].encode()).hexdigest()[:12]
        for suffix, title, day in [('prepare', 'Confirm funding and agreements before payment deadline', max(date.fromisoformat(snapshot['as_of']), due-timedelta(days=1))),
                                   ('deadline', 'Recorded payment deadline; verify actual settlement separately', due)]:
            rows.append({'key': key+'-'+suffix, 'title': title, 'description': event['description'],
                         'reference': event['id'], 'plan_date': day.isoformat(), 'payment_deadline': due.isoformat(),
                         'dependency': 'Use actual cash and confirmed receipts; this reminder does not execute or confirm a payment.'})
    rows.insert(0, {'key': 'immediate-review', 'title': 'Start required counterparty discussions and confirm dependencies',
                   'description': 'Review accepted assumptions now; a later outcome review does not postpone payment deadlines.',
                   'reference': '', 'plan_date': snapshot['as_of'], 'dependency': 'Owner action and external confirmation are required.'})
    rows.append({'key': 'review-records', 'title': 'Final outcome review after recorded actuals',
                 'description': 'Enter actual paid movements in My Business, then request a monitoring review.',
                 'reference': '', 'plan_date': decision.review_date.isoformat(),
                 'dependency': 'Sufficient recorded actual outcomes and the fixed review date are required.'})
    return rows


def recovery_roadmap(business, decision):
    if decision.business_id != business.pk:
        raise ValueError('Roadmap business mismatch.')
    rows = roadmap_actions(decision)
    latest_by_key = {}
    for event in AuditEvent.objects.filter(business=business, action='roadmap.updated', object_id=str(decision.pk)).order_by('-created_at', '-pk'):
        latest_by_key.setdefault(event.details.get('action_key'), event)
    for row in rows:
        latest = latest_by_key.get(row['key'])
        progress = latest.details if latest else {}
        row.update(status=progress.get('status', 'planned'), status_label=dict(STATUSES).get(progress.get('status', 'planned')),
                   responsible=progress.get('responsible', ''), note=progress.get('note', ''),
                   target_date=progress.get('target_date', ''), updated_at=latest.created_at if latest else None)
        target = row['target_date'] or row.get('plan_date')
        row['overdue_task'] = bool(target and target < timezone.localdate().isoformat() and row['status'] != 'owner_confirmed')
        row['deadline_warning'] = bool(row.get('payment_deadline') and target and target > row['payment_deadline'])
    from .financial_state import build_state
    from .freshness import snapshot_comparison
    current = build_state(business)
    return {'decision': decision, 'actions': rows, 'editable': decision.state in ('accepted', 'monitoring'),
            'freshness': snapshot_comparison(business, decision.investigation.snapshot, current),
            'current_projection': current['projection'], 'manual_monitoring': 'Automatic alerts are inactive. Recheck before deadlines and after source records change.',
            'basis': 'Owner-reported task progress. It is not proof of payment, settlement, lender approval or causal improvement.'}


@transaction.atomic
def update_roadmap(user, business_id, decision_id, action_key, status, responsible='', target_date=None, note=''):
    business = authorized_business(user, business_id, write=True)
    Business.objects.select_for_update().get(pk=business.pk)
    decision = get_object_or_404(FinancialDecision.objects.select_for_update().select_related('investigation'), pk=decision_id, business=business)
    if decision.state not in ('accepted', 'monitoring'):
        raise ValidationError('Only accepted or monitored plans can receive task confirmations.')
    if action_key not in {row['key'] for row in roadmap_actions(decision)} or status not in dict(STATUSES):
        raise ValidationError('Choose an action and status belonging to this saved plan.')
    if len(responsible) > 120 or len(note) > 1000:
        raise ValidationError('Responsible person and note exceed their field limits.')
    if target_date is not None and not isinstance(target_date, date):
        raise ValidationError('Use a valid explicit target date.')
    details = {'action_key': action_key, 'status': status, 'responsible': responsible,
               'target_date': target_date.isoformat() if target_date else '', 'note': note,
               'basis': 'Owner-reported task progress; not actual financial execution.'}
    prior = AuditEvent.objects.filter(business=business, action='roadmap.updated', object_id=str(decision.pk),
                                     details__action_key=action_key).order_by('-created_at', '-pk').first()
    if prior and prior.details == details:
        return prior
    return AuditEvent.objects.create(user=user, business=business, action='roadmap.updated', object_id=str(decision.pk), details=details)
