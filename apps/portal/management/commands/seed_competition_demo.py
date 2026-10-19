"""Repeatable opt-in local synthetic examples; never reset existing records."""
import os
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.portal.models import Business, Membership, FinancialAccount, Transaction, CollectionContext


class Command(BaseCommand):
    help = 'Create two clearly synthetic local competition businesses once; never use production.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG or settings.HOSTED or os.getenv('RENDER') == 'true' or os.getenv('VERCEL') == '1':
            raise CommandError('Competition fixtures are local DEBUG only.')
        password = os.getenv('DEMO_PASSWORD', '')
        if len(password) < 12:
            raise CommandError('Configure a local DEMO_PASSWORD of at least 12 characters.')
        user, created = get_user_model().objects.get_or_create(username='competition@finpilot.local', defaults={'email': 'competition@finpilot.local', 'first_name': 'Synthetic Owner'})
        if created:
            user.set_password(password)
            user.save()
        today = timezone.localdate()
        for kind in ('Retail', 'Restaurant'):
            name = 'Competition Synthetic '+kind
            if Business.objects.filter(name=name, is_demo=True, memberships__user=user).exists():
                self.stdout.write(name+': already exists; preserved.')
                continue
            business = Business.objects.create(name=name, category=kind, country='US', currency='USD', size='Small',
                opening_balance=0, opening_date=today-timedelta(days=500), cash_records_complete=True, is_demo=True,
                low_cash_threshold=70000 if kind == 'Retail' else 15000,
                description='SYNTHETIC competition fixture. '+('Inventory dependence requires supplier confirmation.' if kind == 'Retail' else 'Owner scenario: daily food replenishment and payroll sustain service; food waste is unmeasured.'))
            Membership.objects.create(business=business, user=user)
            account = FinancialAccount.objects.create(business=business, name='Synthetic operating account')
            records = []
            net = Decimal('0')
            for offset in range(500, 0, -1):
                day = today-timedelta(days=offset)
                weekend = day.weekday() >= 5
                income = Decimal(160 if weekend else 260) if kind == 'Retail' else Decimal(900 if weekend else 450)
                expense = Decimal(150 if weekend else 240) if kind == 'Retail' else Decimal(700 if weekend else 580)
                net += income-expense
                for tx_kind, amount, category in [('income', income, 'Sales'), ('expense', expense, 'Inventory' if kind == 'Retail' else 'Food Supplies')]:
                    records.append(Transaction(business=business, account=account, date=day, amount=amount, currency='USD', kind=tx_kind,
                        status='paid', category=category, description='SYNTHETIC historical '+category, reference=f'SYN-{kind}-{offset}-{tx_kind}'))
            Transaction.objects.bulk_create(records)
            business.opening_balance = (Decimal('71010') if kind == 'Retail' else Decimal('30000'))-net
            business.save(update_fields=['opening_balance'])
            def pending(kind_value, amount, offset, category, critical=False):
                return Transaction.objects.create(business=business, account=account, date=today, amount=amount, currency='USD',
                    kind=kind_value, status='pending', due_date=today+timedelta(days=offset), category=category, is_critical=critical,
                    description='SYNTHETIC '+category, reference=f'SYN-{kind}-{amount}-{offset}')
            if kind == 'Retail':
                pending('payable', 5400, 6, 'Inventory', True)
                pending('receivable', 400, 2, 'Sales')
                invoice = pending('receivable', 3600, -7, 'Sales')
                pending('receivable', 500, -3, 'Sales')
                CollectionContext.objects.create(transaction=invoice, customer_alias='Synthetic customer A', follow_up_status='contacted', dispute_status='unknown')
            else:
                pending('payable', 12000, 3, 'Food Supplies', True)
                pending('payable', 8000, 6, 'Payroll', True)
                pending('income', 6000, 2, 'Sales')
                pending('expense', 1000, 9, 'Marketing')
            self.stdout.write(name+': created with synthetic paid history and dated assumptions; no external activity.')
