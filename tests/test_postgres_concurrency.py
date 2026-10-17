"""Run against an isolated disposable PostgreSQL test DB, never production."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
import pytest
from django.db import connection, connections, close_old_connections
from django.utils import timezone
from apps.portal.imports import preview_import, confirm_import
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.decision_memory import decide
from apps.portal.intelligence.monitoring import monitor_business
from tests.test_import_integrity import upload

pytestmark = pytest.mark.django_db(transaction=True)


def parallel_twice(function):
    barrier = Barrier(2)
    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return function()
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        return [f.result(timeout=30) for f in futures]


def postgres_only():
    if connection.vendor != 'postgresql':
        pytest.skip('PostgreSQL row-lock behavior requires a disposable PostgreSQL test database.')


def test_concurrent_import_preview_and_confirmation(owner, business):
    postgres_only()
    ids = parallel_twice(lambda: preview_import(business, upload()).pk)
    assert ids[0] == ids[1]
    counts = parallel_twice(lambda: confirm_import(business, owner, ids[0]))
    assert sorted(counts) == [0, 3]
    assert business.transactions.count() == 3
    assert business.auditevent_set.filter(action='import.confirmed').count() == 1


def test_concurrent_accept_and_monitor(owner, business, entry):
    postgres_only()
    entry(kind='payable', status='pending', amount=1200, due_date=timezone.localdate()+timedelta(days=3))
    item = run_investigation(owner, business.pk, 'Review dated liquidity')
    ids = parallel_twice(lambda: decide(owner, business.pk, item.decision.pk, 'accepted', item.result['recommended']).pk)
    assert ids[0] == ids[1]
    assert item.decision.events.filter(to_state='accepted').count() == 1
    statuses = parallel_twice(lambda: monitor_business(business).status)
    assert statuses == ['completed', 'completed']
    assert item.decision.events.filter(to_state='monitoring').count() == 1
    assert business.decisions.count() == 1
    codes = list(business.financial_issues.values_list('code', flat=True))
    assert len(codes) == len(set(codes))
    assert all(not run.details['notification_sent'] for run in business.monitoring_runs.all())
