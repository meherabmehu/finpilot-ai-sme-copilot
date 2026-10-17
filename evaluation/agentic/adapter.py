"""Expected-blind adapter for the existing Django services, not the reference harness.

Imports only the benchmark's response contract. The runner retains oracle access;
this adapter receives a reduced input dictionary without criteria or expected values.
"""
from dataclasses import asdict
from datetime import date
from pathlib import Path
from unittest.mock import patch
import json
import uuid

from adapters.base import AdapterInfo, AdapterStatus, AgentResponse, EvidenceClaim, ResponseStatus
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.http import Http404

from apps.portal import models
from apps.portal.access import authorized_business
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.issue_detection import detect_issues
from apps.portal.intelligence.investigation import run_investigation, question_context
from apps.portal.intelligence.question_analysis import question_comparison
from apps.portal.intelligence.financial_evidence import evidence_graph
from .selectors import resolve
from .normalization import calculations
from .lifecycle import execute_lifecycle


class DjangoAdapter:
    name = 'django'
    description = 'Actual local Django services; disposable test database; per-case rollback; no LLM'
    is_agent_evaluation = True

    def __init__(self, evidence_dir):
        self.evidence_dir = Path(evidence_dir)
        self.executed = 0

    def status(self):
        import os
        safe = (os.environ.get('FINPILOT_EVAL_DJANGO') == '1'
                and settings.SETTINGS_MODULE == 'evaluation.agentic.settings'
                and ((connection.vendor == 'sqlite' and connection.settings_dict['NAME'] == ':memory:')
                     or (connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_finpilot_agentic_')
                         and connection.settings_dict['NAME'] == os.environ.get('FINPILOT_EVAL_DB_NAME'))))
        return (AdapterStatus.CONNECTED, 'Isolated local Django configured; no production connection') if safe else (
            AdapterStatus.BLOCKED, 'Requires explicit opt-in and dedicated in-memory evaluation settings')

    def info(self):
        status, reason = self.status()
        return AdapterInfo(self.name, self.description, status, reason, writes_to_database=True,
                           tested_against_live_application=self.executed > 0)

    def run_case(self, case, prompt):
        # Whitelist only inputs; do not pass criteria/security expected-handling/lifecycle expectations.
        data = case.model_dump(mode='json', include={
            'scenario_id', 'business', 'policy', 'transactions', 'recurring_obligations', 'actor', 'question',
            'candidate_decisions'})
        response = AgentResponse(scenario_id=data['scenario_id'])
        status, reason = self.status()
        evidence = {}
        if status != AdapterStatus.CONNECTED:
            response.status, response.abstained, response.error = ResponseStatus.ERROR, True, reason
            return response
        try:
            with transaction.atomic(), patch('django.utils.timezone.localdate', return_value=date.fromisoformat(data['business']['as_of'])):
                business, user = create_fixture(data)
                try:
                    authorized_business(user, business.pk)
                except (PermissionDenied, Http404) as exc:
                    response.status, response.abstained = ResponseStatus.REFUSED, True
                    response.refusal_reasons = [str(exc)]
                    response.tool_calls = [{'tool': 'authorized_business', 'status': 'denied'}]
                else:
                    before = ledger(business)
                    state = build_state(business, as_of=date.fromisoformat(data['business']['as_of']))
                    plans = resolve(state, data['candidate_decisions']) if data['candidate_decisions'] else None
                    try:
                        inv = run_investigation(user, business.pk, data['question'], custom_plans=plans)
                        result = inv.result
                        response.tool_calls = inv.trace
                    except PermissionDenied as exc:
                        # Viewer read path is allowed, persisted investigation/decision is not.
                        inv = None
                        focus = question_context(data['question'], state)
                        comparison = question_comparison(state, focus['analysis'], plans)
                        result = {'focus': focus, 'analysis': focus['analysis'], 'issues': detect_issues(state),
                                  'comparison': comparison, 'evidence_graph': evidence_graph(state, comparison)}
                        response.refusal_reasons.append(str(exc))
                        response.tool_calls = [{'tool': 'run_investigation', 'status': 'write denied'},
                                               {'tool': 'build_state/detect_issues/question_comparison/evidence_graph', 'status': 'completed'}]
                    comparison = result['comparison']
                    response.calculations = calculations(state, comparison, result)
                    response.issue_codes = [i['code'] for i in result['issues']]
                    response.recommended_plan = comparison['recommended']
                    response.feasible_plans = [p['name'] for p in comparison['plans'] if p['feasible']]
                    response.violations_reported = [v for p in comparison['plans'] for v in p['violations']]
                    response.disclosures = state['limitations'] + [v for p in comparison['plans'] for v in p['dependencies']]
                    # Preserve actual explanatory output; never append benchmark-requested caveats.
                    response.narrative = '\n'.join(line for section in result['analysis']['sections'] for line in section['lines'])
                    response.narrative += '\n' + comparison['objective']
                    response.narrative += '\n' + result.get('explanation', '')
                    response.evidence = EvidenceClaim(
                        references=[e['id'] for e in state['events']],
                        amounts={e['id']: e['amount'] for e in state['events']},
                        dates={e['id']: e['date'] for e in state['events']},
                        formula='cash[d] = cash[d-1] + inflows[d] - outflows[d]',
                        basis='estimated', amount=state['projection'].get('minimum_balance'))
                    response.abstained = not state['projection'].get('available')
                    response.status = ResponseStatus.ABSTAINED if response.abstained else ResponseStatus.ANSWERED
                    if response.abstained:
                        response.refusal_reasons.append(state['projection']['reason'])
                    if ledger(business) != before:
                        response.records_modified.append('Application changed synthetic ledger during investigation')
                    evidence = {'state': state, 'result': result}
                    if prompt['lifecycle_script']:
                        response.lifecycle_actions = execute_lifecycle(business, user, inv, prompt['lifecycle_script'], data)
                self.executed += 1
                transaction.set_rollback(True)
        except Exception as exc:
            import traceback
            evidence['exception_trace'] = traceback.format_exc()
            response.status, response.abstained, response.error = ResponseStatus.ERROR, True, f'{type(exc).__name__}: {exc}'
        # Every case, including blocked/refused, has actual response and rollback evidence.
        if models.Business.objects.exists():
            raise RuntimeError('Evaluation rollback failed: synthetic business leaked')
        evidence.update({'response': asdict(response), 'cleanup': 'rolled back; zero businesses remain'})
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        (self.evidence_dir / f"{data['scenario_id']}.json").write_text(json.dumps(evidence, default=str, sort_keys=True, indent=2) + '\n')
        return response


def ledger(business):
    return list(business.transactions.order_by('pk').values())


def create_fixture(data):
    source = data['business']
    user = get_user_model().objects.create_user(username='evaluation-' + data['scenario_id'])
    business = models.Business.objects.create(
        id=uuid.uuid5(uuid.NAMESPACE_URL, 'finpilot-evaluation:' + data['scenario_id']),
        name=source['name'], category=source['sector'], country=source['country'], currency=source['currency'],
        opening_balance=source['opening_balance'], opening_date=source['opening_date'],
        low_cash_threshold=source['low_cash_threshold'], cash_records_complete=source['cash_records_complete'], is_demo=True)
    account = models.FinancialAccount.objects.create(business=business, name='Synthetic evaluation account')
    actor = data.get('actor')
    # Actor identifiers in this package are portable aliases, not database UUIDs.
    allowed = not actor or (actor['role'] != 'stranger' and actor['requested_business_id'] in actor['member_of'])
    if allowed:
        models.Membership.objects.create(user=user, business=business, role=actor['role'] if actor else 'owner')
    models.FinancialPolicy.objects.create(business=business, **data['policy'])
    for row in data['recurring_obligations']:
        fields = {k: v for k, v in row.items() if k != 'obligation_id'}
        models.RecurringObligation.objects.create(pk=row['obligation_id'], business=business, **fields)
    accounts = {'main': account}
    for row in data['transactions']:
        if row['account'] not in accounts:
            accounts[row['account']] = models.FinancialAccount.objects.create(business=business, name=row['account'])
        fields = {k: v for k, v in row.items() if k not in {'txn_id', 'account'}}
        models.Transaction.objects.create(pk=row['txn_id'], business=business, account=accounts[row['account']], **fields)
    # Explicit portable IDs must not leave PostgreSQL sequences behind fixture rows.
    from django.core.management.color import no_style
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [models.Transaction, models.RecurringObligation]):
            cursor.execute(sql)
    business.refresh_from_db()
    return business, user
