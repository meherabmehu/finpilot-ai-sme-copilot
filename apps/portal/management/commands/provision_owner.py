"""Trusted operator provisioning; never exposed as an HTTP endpoint."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction


class Command(BaseCommand):
    help = "Create an ordinary active owner login from one-time operator environment settings; never grants staff privileges."

    @transaction.atomic
    def handle(self, *args, **options):
        email = os.getenv("FINPILOT_INITIAL_EMAIL", "").strip().lower()
        password = os.getenv("FINPILOT_INITIAL_PASSWORD", "")
        if not email or not password:
            raise CommandError("Both one-time account environment settings are required.")
        try:
            validate_email(email)
            if len(email) > 150:
                raise ValidationError("Email is too long.")
            User = get_user_model()
            candidate = User(username=email, email=email, first_name="Business owner")
            validate_password(password, candidate)
        except ValidationError as exc:
            raise CommandError("Invalid operator-provided account settings.") from exc
        user = User.objects.filter(username=email).first()
        if user:
            # Idempotent deploys never reset an established user's password or role.
            if user.is_active:
                self.stdout.write("Account already active; credentials and privileges were not changed.")
                return
            if user.is_staff or user.is_superuser or user.membership_set.exists():
                raise CommandError("Refusing to replace an existing privileged or business-linked account.")
            # The deployment owner explicitly supplies the identity for an unverified,
            # unused account when external mail delivery has not been configured.
            user.is_active = True
            user.set_password(password)
            user.save(update_fields=["is_active", "password"])
        else:
            candidate.is_active = True
            candidate.is_staff = False
            candidate.is_superuser = False
            candidate.set_password(password)
            candidate.save()
        self.stdout.write(self.style.SUCCESS("Owner login provisioned. No staff access, businesses or financial records were added."))
