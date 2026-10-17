"""Execute expected-free lifecycle commands, with fixture arrivals separate from app calls."""
from datetime import date, timedelta
from decimal import Decimal
import uuid

from django.core.exceptions import ValidationError
from apps.portal.models import Transaction
from apps.portal.intelligence.decision_memory import decide, policy_feedback
from apps.portal.intelligence.financial_state import build_state
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.monitoring import monitor_business
from unittest.mock import patch


def execute_lifecycle(business, user, investigation, script, data):
    if investigation is None:
        raise ValueError('Lifecycle requires an authorized persisted investigation')
    current = investigation
    actions = []
    base_date = date.fromisoformat(data['business']['as_of'])
    for command in script:
        name = command['step']
        current.refresh_from_db()
        decision = current.decision
        before_count = decision.events.count()
        record = {'step': name}
        ledger_before = list(business.transactions.order_by('pk').values())
        try:
            if name == 'investigate':
                old = current.pk
                key = uuid.uuid5(uuid.NAMESPACE_URL, command['request_key']) if command.get('request_key') else None
                # The first investigation is performed by the main adapter. A request key
                # requires the actual service call so subsequent retries test persistence.
                if key or actions:
                    current = run_investigation(user, business.pk, data['question'], request_key=key)
                current.refresh_from_db()
                decision = current.decision
                record.update(investigation_created=current.pk != old if actions else True,
                              same_investigation_returned=current.pk == old,
                              snapshot_fingerprint_recorded=bool(current.snapshot['fingerprint']),
                              new_snapshot_fingerprint_recorded=bool(current.snapshot['fingerprint']))
            elif name == 'inspect_result':
                record.update(has_comparison=bool(current.result.get('comparison')),
                              has_evidence_graph=bool(current.result.get('evidence_graph')),
                              recommended_present_or_missing_information=bool(current.result.get('recommended') or current.result['focus']['missing_information']))
            elif name in ('accept', 'modify', 'reject', 'close', 'transition'):
                target = {'accept': 'accepted', 'modify': 'modified', 'reject': 'rejected', 'close': 'closed'}.get(name, command.get('target'))
                candidates = current.result['comparison']['plans']
                token = command.get('plan')
                chosen = None
                if token == '@feasible_shift_plan':
                    chosen = next((p for p in candidates if p['feasible'] and any(a['kind'] == 'shift' for a in p['actions'])), None)
                elif token == '@payroll_shift_plan':
                    chosen = next((p for p in candidates if any(a['kind'] == 'shift' and any(
                        e['id'] == a['event_id'] and e['payroll'] for e in current.snapshot['events']) for a in p['actions'])), None)
                    if chosen is None:
                        event = next(e for e in current.snapshot['events'] if e['payroll'])
                        # Authored request is intentionally forbidden; validate through real modified-plan path.
                        chosen = {'name': 'Requested payroll delay', 'actions': [{'kind': 'shift', 'event_id': event['id'], 'days': 5}]}
                if token and chosen is None:
                    raise ValueError(f'Application has no candidate for lifecycle input {token}')
                specification = {'name': chosen['name'], 'actions': chosen['actions']} if chosen else None
                if token == '@payroll_shift_plan' and chosen['name'] == 'Requested payroll delay':
                    # Do not inject into saved snapshots. A forbidden replacement exercises
                    # the same actual feasibility gate via the supported modify API.
                    target = 'modified'
                decision = decide(user, business.pk, decision.pk, target,
                                  selected_plan=chosen['name'] if chosen else '',
                                  modified_plan=specification if target == 'modified' else None)
                record.update(selected_plan_recorded=bool(decision.selected_plan),
                              expected_balance_at_review_recorded='balance_at_review' in decision.expected,
                              expected_basis=decision.expected.get('basis'), payment_executed=False,
                              replacement_plan_validated=target == 'modified', write=True)
            elif name == 'mutate_ledger':
                before = build_state(business)['fingerprint']
                Transaction.objects.create(business=business, account=business.accounts.first(), date=base_date,
                                           amount='1.00', currency=business.currency, kind='expense', description='Synthetic change')
                record['fingerprint_changed'] = build_state(business)['fingerprint'] != before
            elif name == 'set_flag':
                before = build_state(business)['fingerprint']
                if command['field'] != 'cash_records_complete':
                    raise ValueError('Unsupported fixture mutation')
                business.cash_records_complete = command['value']
                business.save(update_fields=['cash_records_complete'])
                record['fingerprint_changed'] = build_state(business)['fingerprint'] != before
            elif name == 'monitor':
                mode = command.get('actual_records')
                if mode in ('@as_planned', '@collection_missing'):
                    realize(business, decision, base_date, missing_collection=mode == '@collection_missing')
                elif mode not in (None, '@none'):
                    raise ValueError(f'Unsupported observation fixture {mode}')
                ledger_before = list(business.transactions.order_by('pk').values())
                with patch('django.utils.timezone.localdate', return_value=base_date + timedelta(days=command['day_offset'])):
                    run = monitor_business(business)
                decision.refresh_from_db()
                record['monitoring_status'] = run.status
                record['notification_sent'] = run.details.get('notification_sent')
                record.update(outcome_status=decision.outcome.get('status', 'not_due'),
                              difference=decision.outcome.get('difference'),
                              difference_nonzero=Decimal(decision.outcome.get('difference', '0')) != 0,
                              causal_attribution='unknown', may_claim_success=False, may_claim_failure=False,
                              absence_treated_as_performance=False)
            elif name == 'policy_feedback':
                record.update(policy_feedback(business))
                record.setdefault('automatic_change', False)
                record['minimum_required'] = 5
            else:
                raise ValueError(f'Unsupported lifecycle step: {name}')
        except ValidationError as exc:
            record['rejected_with'] = '; '.join(exc.messages)
        decision.refresh_from_db()
        record.update(decision_state=decision.state, events_created=decision.events.count() - before_count)
        record['ledger_modified_by_application'] = (name not in ('mutate_ledger', 'set_flag')
            and list(business.transactions.order_by('pk').values()) != ledger_before)
        transitions = list(decision.events.values_list('from_state', 'to_state'))
        duplicates = len(transitions) - len(set(transitions))
        record['duplicate_events_created'] = duplicates
        record['duplicate_lifecycle_events'] = duplicates
        actions.append(record)
    return actions


def realize(business, decision, as_of, missing_collection=False):
    """Harness-only observed fixtures; never called by the application under evaluation.

    Convert simulated future movements into labelled synthetic observations. The engine
    does not execute a payment. Pending invoices are marked archived by the harness so
    arrivals are not counted twice; recurring links are preserved on paid realizations.
    """
    if not decision.selected_snapshot:
        raise ValueError('Cannot realize an unselected application plan')
    business.transactions.filter(status='pending').update(archived=True)
    skipped = False
    for event in decision.selected_snapshot['events']:
        day = date.fromisoformat(event['date'])
        if not as_of < day <= decision.review_date:
            continue
        if missing_collection and event['direction'] == 'inflow' and not skipped:
            skipped = True
            continue
        original = business.transactions.filter(pk=event.get('source_id')).first() if event.get('source') == 'transaction' else None
        Transaction.objects.create(
            business=business, account=business.accounts.first(), date=day, due_date=day, status='paid',
            amount=event['amount'], currency=business.currency,
            kind=original.kind if original else 'income' if event['direction'] == 'inflow' else 'expense',
            category=event.get('category', 'General'), description='Synthetic observed arrival',
            recurring_obligation_id=event['source_id'] if event.get('source') == 'recurring' else None)
