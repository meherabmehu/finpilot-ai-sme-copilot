import os
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.portal.models import Business, Membership, FinancialAccount, Transaction, LoanProduct


class Command(BaseCommand):
    help = "Create development-only synthetic workspaces. Set DEMO_PASSWORD explicitly."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo seeding is disabled in production.")
        password = os.getenv("DEMO_PASSWORD")
        if not password or len(password) < 12:
            raise CommandError("Set DEMO_PASSWORD to at least 12 characters.")
        user, created = User.objects.get_or_create(
            username="demo@finpilot.local", defaults={"email": "demo@finpilot.local", "first_name": "Alex Morgan", "is_active": True}
        )
        if created:
            user.set_password(password)
            user.save()
        today = timezone.localdate()
        for name, category, scale in [
            ("ABC Electronics", "Retail", 3),
            ("Tasty Bites", "Restaurant", 2),
            ("The Fashion House", "Retail", 1),
        ]:
            if Business.objects.filter(name=name, is_demo=True, memberships__user=user).exists():
                continue
            business = Business.objects.create(
                name=name,
                category=category,
                country="US",
                currency="USD",
                opening_balance=Decimal(12000 * scale),
                opening_date=today - timedelta(days=180),
                description="Fictional demonstration business. All records are synthetic.",
                is_demo=True,
                low_cash_threshold=2000,
                cash_records_complete=True,
            )
            Membership.objects.create(business=business, user=user)
            account = FinancialAccount.objects.create(business=business, name="Operating account")
            records = []
            for offset in range(180):
                day = today - timedelta(days=179 - offset)
                sales = (150 + (offset * 7 % 110) + offset // 12) * scale
                if category == "Restaurant" and day.weekday() >= 5:
                    sales = sales * 3 // 2
                records.append(
                    Transaction(
                        business=business,
                        account=account,
                        date=day,
                        description="Daily sales",
                        amount=sales,
                        currency="USD",
                        kind="income",
                        category="Sales",
                        status="paid",
                    )
                )
                records.append(
                    Transaction(
                        business=business,
                        account=account,
                        date=day,
                        description="Operating supplies",
                        amount=(65 + offset * 3 % 50) * scale,
                        currency="USD",
                        kind="expense",
                        category="Supplies",
                        status="paid",
                    )
                )
                if day.day == 1:
                    records.append(
                        Transaction(
                            business=business,
                            account=account,
                            date=day,
                            description="Monthly premises rent",
                            amount=900 * scale,
                            currency="USD",
                            kind="expense",
                            category="Rent",
                            status="paid",
                        )
                    )
                if day.day == 25:
                    records.append(
                        Transaction(
                            business=business,
                            account=account,
                            date=day,
                            description="Team payroll",
                            amount=800 * scale,
                            currency="USD",
                            kind="expense",
                            category="Payroll",
                            status="paid",
                        )
                    )
            records.extend(
                [
                    Transaction(
                        business=business,
                        account=account,
                        date=today,
                        due_date=today + timedelta(days=8),
                        description="Supplier invoice",
                        amount=1800 * scale,
                        currency="USD",
                        kind="payable",
                        category="Inventory",
                        status="pending",
                    ),
                    Transaction(
                        business=business,
                        account=account,
                        date=today - timedelta(days=15),
                        due_date=today - timedelta(days=2),
                        description="Wholesale customer invoice",
                        amount=1200 * scale,
                        currency="USD",
                        kind="receivable",
                        category="Sales",
                        status="pending",
                    ),
                ]
            )
            Transaction.objects.bulk_create(records)
        LoanProduct.objects.get_or_create(
            provider="Fictional Example Finance",
            name="Synthetic working capital illustration",
            defaults={
                "country": "US",
                "currency": "USD",
                "minimum": 1000,
                "maximum": 500000,
                "annual_rate": 12,
                "fee": 100,
                "min_months": 6,
                "max_months": 60,
                "illustrative": True,
                "eligibility": "Synthetic product for demonstration only. Not an available offer or approval. No lender underwriting is implemented.",
            },
        )
        self.stdout.write(self.style.SUCCESS("Synthetic demo ready. Sign in as demo@finpilot.local using your DEMO_PASSWORD."))
