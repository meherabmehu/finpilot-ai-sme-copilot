from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.portal.models import Business, Alert, AuditEvent
from apps.portal.engine import summary, forecast


class Command(BaseCommand):
    help = "Idempotently update workspace financial monitoring alerts."

    def add_arguments(self, parser):
        parser.add_argument('--business', help='Restrict trusted monitoring to one business UUID.')

    def handle(self, *args, **options):
        failures = 0
        today = timezone.localdate()
        businesses = Business.objects.all()
        if options.get('business'):
            businesses = businesses.filter(pk=options['business'])
        for business in businesses.iterator():
            from apps.portal.intelligence.monitoring import monitor_business
            run = monitor_business(business)
            if run.status == 'failed':
                self.stderr.write('A business monitoring run failed; inspect MonitoringRun and retry. No sensitive details logged.')
                failures += 1
                continue
            current = summary(business, today - timedelta(days=29))
            previous = summary(business, today - timedelta(days=59), today - timedelta(days=30))
            newest = business.transactions.filter(archived=False).order_by("-date").first()
            projection = forecast(business)
            checks = {
                "missing_records": (not current["count"], "No recent records. Add transactions to keep your financial picture current."),
                "stale_data": (
                    newest is not None and newest.date < today - timedelta(days=14),
                    "Your latest financial entry is more than 14 days old.",
                ),
                "low_cash": (
                    current["cash"] is not None and current["cash"] < business.low_cash_threshold,
                    "Recorded cash is below your configured threshold.",
                ),
                "forecast_shortage": (
                    projection.get("available") and Decimal(projection["minimum_balance"]) < business.low_cash_threshold,
                    "Baseline forecast falls below your cash threshold. This is an assumption-based risk.",
                ),
                "overdue_receivables": (
                    business.transactions.filter(archived=False, kind="receivable", status="pending", due_date__lt=today).exists(),
                    "Outstanding receivables are past their recorded due date.",
                ),
                "upcoming_payments": (
                    business.transactions.filter(
                        archived=False, kind="payable", status="pending", due_date__gte=today, due_date__lte=today + timedelta(days=7)
                    ).exists(),
                    "Supplier payments are due within seven days.",
                ),
                "expense_increase": (
                    previous["expenses"] > 0 and current["expenses"] > previous["expenses"] * Decimal("1.25"),
                    "Recorded operating expenses increased by over 25% against the preceding 30 days.",
                ),
                "revenue_decline": (
                    previous["revenue"] > 0 and current["revenue"] < previous["revenue"] * Decimal(".8"),
                    "Recorded revenue declined by over 20% against the preceding 30 days.",
                ),
            }
            for code, (active, text) in checks.items():
                Alert.objects.update_or_create(business=business, code=code, defaults={"active": bool(active), "message": text})
            AuditEvent.objects.create(business=business, action="monitor.completed")
        if failures:
            raise CommandError(f'{failures} monitoring invocation(s) failed; inspect MonitoringRun and retry.')
        self.stdout.write("Financial monitoring complete.")
