"""Retryable monitoring; detection and internal attention are separate from notifications."""

from django.db import transaction
from django.utils import timezone
from ..models import MonitoringRun, Business
from .financial_state import build_state
from .issue_detection import refresh_issues
from .decision_memory import monitor_decision


def monitor_business(business):
    run = MonitoringRun.objects.create(business=business)
    try:
        with transaction.atomic():
            business = Business.objects.select_for_update().get(pk=business.pk)
            state = build_state(business)
            detected = refresh_issues(business, state)
        reviewed = 0
        milestones = []
        for decision in business.decisions.filter(state__in=['accepted', 'monitoring']).iterator(chunk_size=100):
            monitor_decision(decision)
            from .roadmap import recovery_roadmap
            roadmap = recovery_roadmap(business, decision)
            milestones.append({'decision': str(decision.pk), 'needs_review': roadmap['freshness']['stale'],
                               'overdue_tasks': sum(bool(a['overdue_task']) for a in roadmap['actions']),
                               'current_reserve_gap': roadmap['freshness']['current_gap'],
                               'next_task_date': min((a['target_date'] or a.get('plan_date') for a in roadmap['actions']
                                                     if a['status'] != 'owner_confirmed' and (a['target_date'] or a.get('plan_date'))), default=None)})
            reviewed += 1
        run.status = 'completed'
        run.details = {'detected_issues': len(detected), 'reviewed_decisions': reviewed, 'state_fingerprint': state['fingerprint'],
                       'deadline_reviews': milestones,
                       'notification_sent': False, 'invocation': 'explicit management command/service; scheduler not established'}
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning('Financial monitoring failed: %s', type(exc).__name__)
        run.status = 'failed'
        run.details = {'error_type': type(exc).__name__, 'safe_to_retry': True}
    run.completed_at = timezone.now()
    run.save()
    return run
