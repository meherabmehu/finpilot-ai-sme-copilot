"""Retryable monitoring; detection and internal attention are separate from notifications."""

from django.utils import timezone
from ..models import MonitoringRun
from .financial_state import build_state
from .issue_detection import refresh_issues
from .decision_memory import monitor_decision


def monitor_business(business):
    run = MonitoringRun.objects.create(business=business)
    try:
        state = build_state(business)
        detected = refresh_issues(business, state)
        reviewed = 0
        for decision in business.decisions.filter(state__in=['accepted', 'monitoring']).iterator(chunk_size=100):
            monitor_decision(decision)
            reviewed += 1
        run.status = 'completed'
        run.details = {'detected_issues': len(detected), 'reviewed_decisions': reviewed, 'state_fingerprint': state['fingerprint'],
                       'notification_sent': False}
    except Exception as exc:
        run.status = 'failed'
        run.details = {'error_type': type(exc).__name__, 'safe_to_retry': True}
    run.completed_at = timezone.now()
    run.save()
    return run
