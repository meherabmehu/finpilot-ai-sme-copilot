from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Business, Membership, AuditEvent


def authorized_business(user, business_id, write=False):
    business = get_object_or_404(Business, pk=business_id, memberships__user=user)
    if write and not Membership.objects.filter(business=business, user=user, role="owner").exists():
        raise PermissionDenied("This workspace is read-only.")
    return business


@transaction.atomic
def audit(user, business, action, object_id="", details=None):
    AuditEvent.objects.create(user=user, business=business, action=action, object_id=str(object_id), details=details or {})
    if action in ('business.updated', 'transaction.created', 'transaction.updated', 'transaction.archived',
                  'import.confirmed', 'recurring.created', 'recurring.disabled', 'policy.updated'):
        from .intelligence.issue_detection import refresh_issues
        refresh_issues(business)
