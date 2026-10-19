"""Compare immutable evidence with current read-through state, never rewrite history."""
from ..models import AuditEvent


def snapshot_comparison(business, snapshot, current):
    changed = snapshot.get('fingerprint') != current['fingerprint']
    latest = AuditEvent.objects.filter(business=business, action__in=[
        'business.updated', 'transaction.created', 'transaction.updated', 'transaction.archived',
        'import.confirmed', 'recurring.created', 'recurring.disabled', 'policy.updated']).order_by('-created_at').first()
    return {'stale': changed, 'status': 'Needs Review' if changed else 'Matches current financial snapshot',
            'original_as_of': snapshot.get('as_of'), 'original_gap': snapshot.get('projection', {}).get('funding_gap'),
            'current_as_of': current['as_of'], 'current_gap': current['projection'].get('funding_gap'),
            'current_cash': current['known_cash'], 'changed_at': latest.created_at if latest else None,
            'basis': 'Original evidence is historical. Current amounts use current records, policies, business context and analysis date; any of these can change the fingerprint.'}
