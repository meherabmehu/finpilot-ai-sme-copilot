from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.urls import reverse
from apps.portal.imports import preview_import, confirm_import
from apps.portal.engine import summary
from apps.portal.models import Business, FinancialAccount, Membership


def upload(reference='sale-1', amount=250):
    today = timezone.localdate()
    return SimpleUploadedFile('records.csv', (
        'date,description,amount,kind,currency,status,category,reference,due_date\n'
        f'{today},Sale,{amount},income,USD,paid,Sales,{reference},\n'
        f'{today},Supplies,100,expense,USD,paid,Supplies,bill-1,\n'
        f'{today},Invoice,400,receivable,USD,pending,Sales,invoice-1,{today+timedelta(days=5)}\n'
    ).encode())


def test_identical_retry_is_non_mutating_and_preview_is_clear(owner, business, client):
    item = preview_import(business, upload())
    assert confirm_import(business, owner, item.pk) == 3
    assert preview_import(business, upload()).pk == item.pk
    assert confirm_import(business, owner, item.pk) == 0
    assert business.transactions.count() == 3
    stats = summary(business)
    assert (stats['revenue'], stats['expenses'], stats['operating_surplus'], stats['cash'], stats['receivables']) == (
        Decimal('650'), Decimal('100'), Decimal('550'), Decimal('1150'), Decimal('400'))
    client.force_login(owner)
    response = client.post(reverse('upload', args=[business.pk]), {'file': upload()})
    assert b'Already imported' in response.content
    assert b'Confirm 3 rows' not in response.content


def test_correction_is_not_silent_append(owner, business):
    item = preview_import(business, upload())
    confirm_import(business, owner, item.pk)
    corrected = preview_import(business, upload(amount=300))
    assert corrected.errors
    with pytest.raises(ValidationError):
        confirm_import(business, owner, corrected.pk)
    assert summary(business)['cash'] == 1150


def test_equal_distinct_events_need_unique_references(owner, business):
    day = timezone.localdate()
    content = 'date,description,amount,kind,currency,status,reference\n'
    content += f'{day},Sale,50,income,USD,paid,event-a\n{day},Sale,50,income,USD,paid,event-b\n'
    item = preview_import(business, SimpleUploadedFile('sales.csv', content.encode()))
    assert not item.errors
    assert confirm_import(business, owner, item.pk) == 2


def test_business_scoped_import_and_service_reauthorization(owner, business, django_user_model):
    item = preview_import(business, upload())
    viewer = django_user_model.objects.create_user('viewer')
    Membership.objects.create(business=business, user=viewer, role='viewer')
    with pytest.raises(PermissionDenied):
        confirm_import(business, viewer, item.pk)
    other = Business.objects.create(name='Other', opening_balance=1000, opening_date=business.opening_date, currency='USD')
    Membership.objects.create(business=other, user=owner)
    FinancialAccount.objects.create(business=other, name='Cash')
    second = preview_import(other, upload())
    assert second.pk != item.pk
    assert confirm_import(other, owner, second.pk) == 3
    assert business.transactions.count() == 0
