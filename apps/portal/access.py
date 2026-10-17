from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Business, Membership, AuditEvent


def authorized_business(user, business_id, write=False):
    business = get_object_or_404(Business, pk=business_id, memberships__user=user)
    if write and not Membership.objects.filter(business=business, user=user, role="owner").exists():
        raise PermissionDenied("This workspace is read-only.")
    return business


def audit(user, business, action, object_id="", details=None):
    AuditEvent.objects.create(user=user, business=business, action=action, object_id=str(object_id), details=details or {})
