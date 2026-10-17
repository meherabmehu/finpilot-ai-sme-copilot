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
    is_critical = models.BooleanField(default=False)
    recurring_obligation = models.ForeignKey('RecurringObligation', null=True, blank=True, on_delete=models.SET_NULL)
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
    category = models.CharField(max_length=80, default='General')
    is_critical = models.BooleanField(default=False)


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
    valid_until = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def is_current_offer(self, as_of):
        return bool(self.active and not self.illustrative and self.source_url and self.verified_at
                    and self.verified_at <= as_of and (as_of - self.verified_at).days <= 90
                    and self.valid_until and self.valid_until >= as_of)


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


class FinancialPolicy(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='financial_policy')
    horizon_days = models.PositiveSmallIntegerField(default=30)
    protect_payroll = models.BooleanField(default=True)
    protect_critical_suppliers = models.BooleanField(default=True)
    max_delay_days = models.PositiveSmallIntegerField(default=7)
    max_borrowing = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    max_annual_rate = models.DecimalField(max_digits=7, decimal_places=2, default=20)
    expense_increase_percent = models.PositiveSmallIntegerField(default=25)
    concentration_percent = models.PositiveSmallIntegerField(default=60)
    risk_tolerance = models.CharField(max_length=12, choices=[('cautious', 'Cautious'), ('balanced', 'Balanced')], default='cautious')
    restricted_categories = models.JSONField(default=list, blank=True)
    goal = models.CharField(max_length=240, blank=True)
    issue_cooldown_hours = models.PositiveSmallIntegerField(default=24)
    updated_at = models.DateTimeField(auto_now=True)


class FinancialIssue(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='financial_issues')
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=180)
    severity = models.CharField(max_length=12)
    status = models.CharField(max_length=12, choices=[('open', 'Open'), ('resolved', 'Resolved')], default='open')
    evidence = models.JSONField(default=dict)
    detected_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    surfaced_at = models.DateTimeField(null=True, blank=True)
    occurrence_count = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['business', 'code'], name='unique_financial_issue')]
        indexes = [models.Index(fields=['business', 'status', 'severity'])]


class Investigation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name='investigations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    issue = models.ForeignKey(FinancialIssue, null=True, blank=True, on_delete=models.SET_NULL)
    question = models.CharField(max_length=4000)
    mode = models.CharField(max_length=20, default='deterministic')
    status = models.CharField(max_length=16, default='completed')
    request_key = models.UUIDField(default=uuid.uuid4)
    snapshot = models.JSONField(default=dict)
    trace = models.JSONField(default=list)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['business', 'user', 'request_key'], name='unique_investigation_request')]


class FinancialDecision(models.Model):
    STATES = [(s, s.title()) for s in ['proposed', 'accepted', 'rejected', 'modified', 'monitoring', 'evaluated', 'closed']]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name='decisions')
    investigation = models.OneToOneField(Investigation, on_delete=models.PROTECT, related_name='decision')
    state = models.CharField(max_length=16, choices=STATES, default='proposed')
    selected_plan = models.CharField(max_length=80, blank=True)
    selected_snapshot = models.JSONField(default=dict)
    expected = models.JSONField(default=dict)
    review_date = models.DateField()
    feedback = models.TextField(blank=True)
    outcome = models.JSONField(default=dict)
    evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['business', 'state', 'review_date'])]


class DecisionEvent(models.Model):
    decision = models.ForeignKey(FinancialDecision, on_delete=models.PROTECT, related_name='events')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    from_state = models.CharField(max_length=16, blank=True)
    to_state = models.CharField(max_length=16)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class MonitoringRun(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='monitoring_runs')
    status = models.CharField(max_length=16, default='pending')
    details = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
