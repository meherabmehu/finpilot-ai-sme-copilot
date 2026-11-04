"""Local isolated synthetic owner fixture; public demo requires no seeded account."""
import os
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from django.utils import timezone
from apps.portal.models import Business,PersonalProfile,Membership,FinancialAccount,Transaction


class Command(BaseCommand):
    help='Create a clearly synthetic personal workspace locally; never reset or seed production.'

    @transaction.atomic
    def handle(self,*args,**options):
        if not settings.DEBUG or settings.HOSTED:
            raise CommandError('Only local DEBUG demo seeding is permitted.')
        password=os.environ.get('DEMO_PASSWORD')
        if not password:
            raise CommandError('Set local DEMO_PASSWORD without sharing it in chat.')
        user,created=User.objects.get_or_create(username='personal-demo@finpilot.local',defaults={'email':'personal-demo@finpilot.local','first_name':'Synthetic Freelancer'})
        if created:
            user.set_password(password)
            user.save()
        existing=Business.objects.filter(memberships__user=user,name='Buildathon Synthetic Personal',mode='personal',is_demo=True).first()
        if existing:
            self.stdout.write('Existing synthetic personal workspace preserved; no reset performed.')
            return
        today=timezone.localdate()
        workspace=Business.objects.create(name='Buildathon Synthetic Personal',mode='personal',category='Personal',country='BD',currency='BDT',opening_balance=Decimal('18000'),opening_date=today,
            low_cash_threshold=Decimal('8000'),cash_records_complete=True,is_demo=True)
        Membership.objects.create(business=workspace,user=user)
        account=FinancialAccount.objects.create(business=workspace,name='Synthetic personal cash')
        PersonalProfile.objects.create(workspace=workspace,income_type='freelance',savings_target=Decimal('5000'))
        for kind,amount,offset,essential,category in [('receivable','10000',4,False,'Freelance income'),('payable','12000',7,True,'Essential living costs')]:
            Transaction.objects.create(business=workspace,account=account,date=today,kind=kind,amount=Decimal(amount),currency='BDT',status='pending',due_date=today+timedelta(days=offset),
                is_critical=essential,category=category,description='SYNTHETIC '+category)
        self.stdout.write('Created isolated synthetic personal demo. Login: personal-demo@finpilot.local; use local DEMO_PASSWORD.')
