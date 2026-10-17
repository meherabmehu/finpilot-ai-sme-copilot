import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.portal.intelligence.investigation import run_investigation
from apps.portal.models import Membership, FinancialPolicy


@pytest.fixture
def investigation(owner, business, entry):
    entry(kind='payable', status='pending', amount=500, due_date=timezone.localdate()+timedelta(days=2))
    entry(kind='payable', category='Payroll', status='pending', amount=800, due_date=timezone.localdate()+timedelta(days=3))
    entry(kind='receivable', status='pending', amount=700, due_date=timezone.localdate()+timedelta(days=5))
    return run_investigation(owner, business.pk, 'Can I cover payroll and my supplier?')


def test_saved_workflow_and_retry(client, owner, business, investigation):
    client.force_login(owner)
    url = reverse('investigation_start', args=[business.pk])
    payload = {'question': 'Review my obligations', 'request_key': str(uuid.uuid4())}
    first = client.post(url, payload)
    assert first.status_code == 302
    assert client.post(url, payload).url == first.url
    page = client.get(first.url)
    assert page.status_code == 200
    assert b'Compare simulated alternatives' in page.content
    decision = investigation.decision
    url = reverse('decision_update', args=[business.pk, decision.pk])
    payload = {'target': 'accepted', 'selected_plan': investigation.result['recommended']}
    assert client.post(url, payload).status_code == 302
    client.post(url, payload)
    decision.refresh_from_db()
    assert decision.state == 'accepted'
    assert decision.events.filter(to_state='accepted').count() == 1
    assert client.post(reverse('decision_review', args=[business.pk, decision.pk])).status_code == 302
    decision.refresh_from_db()
    assert decision.state == 'monitoring'
    assert client.get(reverse('planning', args=[business.pk])+'?tab=decisions').status_code == 200


@pytest.mark.parametrize('route', ['financial_policy', 'investigation_start', 'decision_update', 'decision_review'])
def test_mutations_require_post_owner_and_csrf(client, owner, business, investigation, route):
    args = [business.pk] + ([investigation.decision.pk] if route.startswith('decision_') else [])
    url = reverse(route, args=args)
    client.force_login(owner)
    assert client.get(url).status_code == 405
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(owner)
    assert secure.post(url, {}).status_code == 403
    viewer = User.objects.create_user('reader')
    Membership.objects.create(user=viewer, business=business, role='viewer')
    client.force_login(viewer)
    assert client.post(url, {}).status_code == 403
    outsider = User.objects.create_user('outsider')
    client.force_login(outsider)
    assert client.post(url, {}).status_code == 404


def test_detail_is_business_scoped(client, business, investigation):
    outsider = User.objects.create_user('outsider')
    client.force_login(outsider)
    assert client.get(reverse('investigation_detail', args=[business.pk, investigation.pk])).status_code == 404


def test_policy_validation_and_historical_snapshot(client, owner, business, investigation):
    client.force_login(owner)
    original = investigation.snapshot
    payload = {**original['policy'], 'minimum_reserve': '200', 'horizon_days': 14,
               'restricted_categories': 'Marketing, Travel', 'goal': 'Protect wages'}
    payload.pop('reserve')
    payload.pop('source')
    url = reverse('financial_policy', args=[business.pk])
    assert client.post(url, payload).status_code == 302
    assert FinancialPolicy.objects.get(business=business).restricted_categories == ['Marketing', 'Travel']
    business.refresh_from_db()
    assert business.low_cash_threshold == 200
    investigation.refresh_from_db()
    assert investigation.snapshot == original
    assert b'Historical evidence' in client.get(reverse('investigation_detail', args=[business.pk, investigation.pk])).content
    payload['horizon_days'] = 200
    assert client.post(url, payload).status_code == 400
    assert FinancialPolicy.objects.get(business=business).horizon_days == 14


def test_bad_input_is_safe(client, owner, business, investigation):
    client.force_login(owner)
    assert client.post(reverse('investigation_start', args=[business.pk]), {'question': 'test', 'request_key': 'bad'}).status_code == 400
    response = client.post(reverse('decision_update', args=[business.pk, investigation.decision.pk]),
                           {'target': 'modified', 'modified_plan': '{"name":"Unsafe","actions":[{"kind":"execute_sql"}]}'})
    assert response.status_code == 302
    investigation.decision.refresh_from_db()
    assert investigation.decision.state == 'proposed'
