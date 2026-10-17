"""An isolated, repeatable DEBUG-only decision workflow; never seed production."""
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.portal.models import (Business, Membership, FinancialAccount, Transaction, DecisionEvent,
                                FinancialDecision, Investigation)
from apps.portal.intelligence.issue_detection import refresh_issues
from apps.portal.intelligence.decision_memory import monitor_decision

NAME = 'Decision Lab · Synthetic Liquidity Demo'
LOGIN = 'decisions@finpilot.local'


class Command(BaseCommand):
    help = 'Seed/reset one isolated DEBUG-only liquidity demo; optionally record synthetic outcomes.'

    def add_arguments(self, parser):
        parser.add_argument('--extended', action='store_true', help='Include overdue collections, expense growth and discretionary trade-offs.')
        parser.add_argument('--reset', action='store_true', help='Reset only this named synthetic workspace.')
        parser.add_argument('--follow-up', action='store_true', help='Record the accepted plan as synthetic paid activity and evaluate at review date.')

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Synthetic decision seeding is disabled in production.')
        password = os.getenv('DEMO_PASSWORD', '')
        if len(password) < 12:
            raise CommandError('Set DEMO_PASSWORD to at least 12 characters.')
        user, created = User.objects.get_or_create(username=LOGIN, defaults={'email': LOGIN, 'first_name': 'Synthetic Owner'})
        if created:
            user.set_password(password)
            user.save()
        business = Business.objects.filter(name=NAME, is_demo=True, memberships__user=user).first()
        if options['follow_up']:
            if not business:
                raise CommandError('Seed the demo first.')
            decision = business.decisions.filter(state__in=['accepted', 'monitoring']).order_by('-created_at').first()
            if not decision:
                raise CommandError('Accept a plan in the demo Decision Lab before recording follow-up activity.')
            if not decision.selected_snapshot.get('feasible'):
                raise CommandError('The selected synthetic plan must be feasible.')
            for event in decision.selected_snapshot['events']:
                if not event['id'].startswith('tx:') or not event['id'][3:].isdigit():
                    raise CommandError('For this reproducible follow-up, select a timing/collection plan without financing or split payments.')
                Transaction.objects.filter(business=business, pk=int(event['id'][3:])).update(
                    status='paid', date=event['date'], amount=event['amount'])
            result = monitor_decision(decision, as_of=decision.review_date)
            self.stdout.write(f'SYNTHETIC review at {decision.review_date}: {result.state}; actual balance {result.outcome.get("actual_balance", "unknown")}. No external action.')
            return
        if business and not options['reset']:
            self.stdout.write(f'Demo already exists: {business.pk}; use --reset to reset its synthetic history.')
            return
        if not business:
            business = Business.objects.create(name=NAME, category='Retail', country='US', currency='USD',
                                               opening_balance=1000, opening_date=timezone.localdate(),
                                               cash_records_complete=True, is_demo=True,
                                               description='DEBUG-only synthetic liquidity scenario. No real financial records.')
            Membership.objects.create(business=business, user=user)
        else:
            Business.objects.select_for_update().get(pk=business.pk)
            DecisionEvent.objects.filter(decision__business=business).delete()
            FinancialDecision.objects.filter(business=business).delete()
            Investigation.objects.filter(business=business).delete()
            business.transactions.all().delete()
            business.financial_issues.all().delete()
            business.monitoring_runs.all().delete()
            business.recurring_obligations.all().delete()
            business.financial_policy.delete() if hasattr(business, 'financial_policy') else None
            business.opening_balance = 1000
            business.opening_date = timezone.localdate()
            business.low_cash_threshold = 0
            business.cash_records_complete = True
            business.save()
        account = business.accounts.first() or FinancialAccount.objects.create(business=business, name='Synthetic operating cash')
        today = timezone.localdate()
        for description, kind, amount, category, days in [
            ('Synthetic supplier invoice', 'payable', 500, 'Supplies', 2),
            ('Synthetic payroll', 'payable', 800, 'Payroll', 3),
            ('Synthetic customer collection', 'receivable', 700, 'Sales', 5),
            ('Synthetic inventory payment', 'payable', 100, 'Inventory', 7),
        ]:
            Transaction.objects.create(business=business, account=account, date=today, description=description,
                                       kind=kind, amount=amount, currency='USD', category=category, status='pending',
                                       due_date=today+timedelta(days=days))
        if options['extended']:
            from apps.portal.models import FinancialPolicy
            business.opening_date = today-timedelta(days=60)
            business.opening_balance = 1300
            business.low_cash_threshold = 200
            business.save()
            FinancialPolicy.objects.update_or_create(business=business, defaults={'max_borrowing': 0})
            for description, kind, amount, category, day, due in [
                ('Synthetic old marketing expense', 'expense', 100, 'Marketing', today-timedelta(days=40), None),
                ('Synthetic current marketing expense', 'expense', 200, 'Marketing', today-timedelta(days=2), None),
                ('Synthetic overdue customer invoice', 'receivable', 400, 'Sales', today-timedelta(days=20), today-timedelta(days=9)),
                ('Synthetic adjustable campaign proposal', 'payable', 100, 'Discretionary', today, today+timedelta(days=8)),
            ]:
                Transaction.objects.create(business=business, account=account, date=day, description=description,
                                           kind=kind, amount=amount, currency='USD', category=category,
                                           status='pending' if due else 'paid', due_date=due,
                                           reference='synthetic-overdue-invoice' if kind == 'receivable' else '')
        refresh_issues(business)
        if options['extended']:
            self.stdout.write('EXTENDED SYNTHETIC: cash 1000; reserve 200; overdue receipts 400; baseline minimum -300; ending 200; recorded operating expenses 1700 vs prior 100 (includes pending bills); Marketing 200 vs prior 100.')
        self.stdout.write(f'SYNTHETIC demo ready: /b/{business.pk}/ — login {LOGIN}. Known cash USD 1000; baseline minimum -300; ending cash {200 if options["extended"] else 300}.')
