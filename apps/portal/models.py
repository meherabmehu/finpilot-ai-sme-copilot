import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Business(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=40)
    country = models.CharField(max_length=2)
    currency = models.CharField(max_length=3)
    size = models.CharField(max_length=40, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    registration_number = models.CharField(max_length=80, blank=True)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    opening_date = models.DateField()
    low_cash_threshold = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    cash_records_complete = models.BooleanField(
        default=False, help_text="Confirm paid cash records are complete since the opening balance date before generating forecasts."
    )
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[("owner", "Owner"), ("viewer", "Read-only Viewer")], default="owner")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "user"], name="unique_membership")]


class FinancialAccount(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=80)


class Transaction(models.Model):
    TYPES = [
        (x, x.replace("_", " ").title())
        for x in ["income", "expense", "transfer", "receivable", "payable", "refund", "loan_disbursement", "loan_repayment"]
    ]
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="transactions")
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=240)
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3)
    kind = models.CharField(max_length=24, choices=TYPES)
    category = models.CharField(max_length=80, default="General")
    account = models.ForeignKey(FinancialAccount, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=[("paid", "Paid"), ("pending", "Pending")], default="paid")
    due_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    fingerprint = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="positive_transaction"),
            models.UniqueConstraint(fields=["business", "fingerprint"], name="unique_import_transaction"),
        ]
        indexes = [models.Index(fields=["business", "date"])]


class AuditEvent(models.Model):
    business = models.ForeignKey(Business, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class DataImport(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64)
    rows = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "digest"], name="unique_import")]


class Scenario(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="scenarios")
    name = models.CharField(max_length=80)
    assumptions = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecurringObligation(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="recurring_obligations")
    description = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    direction = models.CharField(max_length=8, choices=[("outflow", "Outflow"), ("inflow", "Inflow")], default="outflow")
    next_due = models.DateField()
    frequency = models.CharField(
        max_length=10, choices=[("weekly", "Weekly"), ("monthly", "Monthly"), ("yearly", "Yearly")], default="monthly"
    )
    active = models.BooleanField(default=True)


class LoanComparison(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="loan_comparisons")
    assumptions = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class LoanProduct(models.Model):
    provider = models.CharField(max_length=120)
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=2)
    currency = models.CharField(max_length=3)
    minimum = models.DecimalField(max_digits=18, decimal_places=2)
    maximum = models.DecimalField(max_digits=18, decimal_places=2)
    annual_rate = models.DecimalField(max_digits=7, decimal_places=3)
    fee = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    min_months = models.PositiveIntegerField(default=1)
    max_months = models.PositiveIntegerField(default=60)
    source_url = models.URLField(blank=True)
    verified_at = models.DateField(null=True)
    illustrative = models.BooleanField(default=True)
    eligibility = models.TextField(blank=True)


class Conversation(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="conversations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="alerts")
    code = models.CharField(max_length=40)
    message = models.CharField(max_length=300)
    active = models.BooleanField(default=True)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "code"], name="unique_alert")]
