"""Owner-reported action progress, separate from ledger and decision transitions."""
from datetime import date, timedelta
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

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
    rows.append({'key': 'review-records', 'title': 'Recheck cash and reserve after new records',
                 'description': 'Enter actual paid movements in My Business, then request a monitoring review.',
                 'reference': '', 'plan_date': decision.review_date.isoformat(),
                 'dependency': 'Sufficient recorded actual outcomes and the fixed review date are required.'})
    return rows


def recovery_roadmap(business, decision):
    if decision.business_id != business.pk:
        raise ValueError('Roadmap business mismatch.')
    rows = roadmap_actions(decision)
    for row in rows:
        latest = AuditEvent.objects.filter(business=business, action='roadmap.updated', object_id=str(decision.pk),
                                           details__action_key=row['key']).order_by('-created_at', '-pk').first()
        progress = latest.details if latest else {}
        row.update(status=progress.get('status', 'planned'), status_label=dict(STATUSES).get(progress.get('status', 'planned')),
                   responsible=progress.get('responsible', ''), note=progress.get('note', ''),
                   target_date=progress.get('target_date', ''), updated_at=latest.created_at if latest else None)
    return {'decision': decision, 'actions': rows, 'editable': decision.state in ('accepted', 'monitoring'),
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
