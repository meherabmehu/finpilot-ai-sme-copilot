"""Readable current survival and saved scenario sections for existing export writers."""
from .report_sections import amount


def survival_sections(business):
    from .intelligence.financial_state import build_state
    from .intelligence.survival_insights import survival_overview
    state = build_state(business)
    insight = survival_overview(business, state)
    runway = insight['runway']
    return [
        {'title': 'Current financial survival summary', 'headers': ['Measure', 'Value / basis'], 'rows': [
            ['As of', state['as_of']], ['Scope', 'Current authorized records; date filters do not reconstruct historical as-known evidence.'],
            ['Source fingerprint', state['fingerprint']], ['Business type', insight['domain']['type']],
            ['Business-aware guidance', insight['domain']['guidance']], ['Industry assumptions', insight['domain']['basis']],
            ['Recorded cash', amount(state['known_cash'])], ['Rule-based status', insight['health']['label']],
            ['Status explanation', insight['health']['reason']], ['Qualification', insight['health']['qualification']],
            ['Minimum reserve', amount(state['policy']['reserve'])],
            ['First dated reserve breach', state['projection'].get('reserve_breach') or 'Not identified / unavailable'],
            ['Dated minimum closing cash', amount(state['projection'].get('minimum_balance'))],
            ['Closing reserve gap', amount(state['projection'].get('funding_gap'))],
            ['Average-burn runway, days', runway['days'] or 'No finite defensible estimate'],
            ['Runway basis', runway['reason'] + ' ' + runway['basis']],
            ['History coverage', f"{runway['history_days']} calendar days; {runway['active_days']} active days"],
        ]},
        {'title': 'Payment priorities', 'headers': ['Payment / source', 'Priority', 'Recorded due', 'Amount', 'Dependency'], 'rows': [
            [p['description']+' / '+p['id'], p['priority']+' / suggested '+p['suggested_priority']+' / '+p['urgency'], p['recorded_due'], amount(p['amount']), p['dependency']+' '+p['impact']]
            for p in insight['priorities']] or [['No dated upcoming payments recorded.']]},
        {'title': 'Collection exposure', 'headers': ['Invoice / reference', 'Currency', 'Amount', 'Due', 'Days overdue'], 'rows': [
            [p['reference'] or p['description'], p['currency'], p['amount'], p['due_date'] or 'Unknown',
             p['days_overdue'] if p['days_overdue'] is not None else 'Unknown'] for p in insight['collections']['invoices']]
            or [['No pending receivables recorded.']]},
        {'title': 'Limitations', 'headers': ['Source and uncertainty'], 'rows': [[line] for line in state['limitations']] + [[insight['collections']['basis']]]},
    ]


def scenario_sections(business):
    sections = []
    for scenario in business.scenarios.order_by('-created_at'):
        result = scenario.result
        if result.get('kind') == 'invoice_recovery_v1':
            sections.append({'title': scenario.name+' (hypothetical invoice recovery snapshot)',
                'headers': ['Measure', 'Value'], 'rows': [
                    ['Saved UTC', scenario.created_at.isoformat()], ['Source fingerprint', result['source_fingerprint']],
                    ['Target reserve', amount(result['target_reserve'])], ['Baseline gap', amount(result['baseline'].get('remaining_gap'))],
                    ['Recovery minimum cash', amount(result['plan']['timeline'].get('minimum_balance'))],
                    ['Lowest date', result['plan']['timeline'].get('lowest_date')],
                    ['Recovery ending cash', amount(result['plan']['timeline'].get('ending_balance'))],
                    ['Residual gap', amount(result['plan'].get('remaining_gap'))], ['Basis', result['basis']]]})
            sections.append({'title': 'Explicit invoice assumptions', 'headers': ['Reference', 'Amount', 'Assumed date'],
                'rows': [[r['event_id'], amount(r['amount']), r['date']] for r in result['assumptions']['recoveries']] or [['No new recoveries.']]})
            continue
        if result.get('kind') != 'dated_stress_v1':
            sections.append({'title': scenario.name+' (earlier operating illustration)',
                'headers': ['Revenue', 'Expenses', 'Operating surplus', 'Cash delta', 'Basis'],
                'rows': [[amount(result.get('revenue')), amount(result.get('expenses')), amount(result.get('operating_surplus')),
                          amount(result.get('cash_delta')), result.get('assumption', '')]]})
            sections.append({'title': 'Earlier scenario inputs', 'headers': ['Assumption', 'Entered value'],
                             'rows': [[key.replace('_', ' '), str(value)] for key, value in scenario.assumptions.items()]})
            continue
        sections.append({'title': scenario.name+' (dated stress snapshot)', 'headers': ['Measure', 'Value'], 'rows': [
            ['Saved UTC', scenario.created_at.isoformat()], ['Snapshot as of', result['as_of']], ['Snapshot currency', result['currency']],
            ['Basis', result['basis']], ['Source fingerprint', result['source_fingerprint']],
            ['Original plan', result['plan_name']], ['Illustrative borrowing', amount(result['borrowing'])],
            ['Full financing cost', amount(result['financing_cost'])], ['Repayments beyond horizon', amount(result['deferred_liabilities'])],
        ]})
        sections.append({'title': 'Explicit collection cases',
            'headers': ['Case / receipts / delay', 'Minimum cash', 'Ending cash', 'Reserve gap', 'Priority funding', 'Unrealized receipts'],
            'rows': [[f"{case['label']} / {case['collection_percent']}% / {case['delay_days']} days",
                      amount(case['timeline']['minimum_balance']), amount(case['timeline']['ending_balance']),
                      amount(case['timeline']['funding_gap']), case['protected_funding_status'], amount(case['unrealized_receipts'])]
                     for case in result['cases']]})
        sections.append({'title': 'Assumptions and limitations', 'headers': ['Condition'], 'rows': [
            [f"{key.replace('_', ' ')}: {value}"] for key, value in result['assumptions'].items()]
            + [[line] for line in result['dependencies']+result['limitations']]})
    return sections or [{'title': 'Scenario analysis', 'headers': ['Availability'], 'rows': [['No saved scenarios available.']]}]


def roadmap_sections(business):
    from .intelligence.roadmap import recovery_roadmap, READABLE_STATES
    sections = []
    for decision in business.decisions.filter(state__in=READABLE_STATES).exclude(selected_plan='').select_related('investigation')[:100]:
        roadmap = recovery_roadmap(business, decision)
        sections.append({'title': decision.selected_plan+' / owner-reported progress',
            'headers': ['Task', 'Planned date', 'Payment deadline', 'Owner target', 'Status', 'Responsible', 'Evidence / note'],
            'rows': [[a['title'], a.get('plan_date'), a.get('payment_deadline'), a['target_date'], a['status_label'], a['responsible'], a['reference']+' '+a['note']]
                     for a in roadmap['actions']]})
        sections.append({'title': 'Historical expectations and current financial status', 'headers': ['Measure', 'Value'],
            'rows': [['Original simulated ending cash', amount(decision.expected.get('balance_at_review'))],
                     ['Current recorded cash', amount(roadmap['freshness']['current_cash'])],
                     ['Current reserve gap', amount(roadmap['freshness']['current_gap'])],
                     ['Needs review', roadmap['freshness']['stale']], ['Fixed final review', str(decision.review_date)],
                     ['Outcome status', decision.outcome.get('status', 'Not evaluated')],
                     ['Outcome basis', decision.outcome.get('basis', roadmap['basis'])],
                     ['Automatic alerts', 'Inactive; manual review only'] ]})
    return sections or [{'title': 'Recovery roadmap progress', 'headers': ['Availability'], 'rows': [['No accepted recovery plan recorded.']]}]
