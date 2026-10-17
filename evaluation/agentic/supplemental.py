"""Independent host-side checks for gaps in the upstream report, never input to the adapter.

Keep literal expectation mismatches visible. Do not alter the benchmark's verdicts or score.
"""
from collections import defaultdict
import json


def build(source, report, actual_dir):
    cases = {}
    for path in (source / 'scenarios').rglob('*.json'):
        if path.name != 'index.json':
            case = json.loads(path.read_text())
            cases[case['scenario_id']] = case
    actual = {entry['scenario_id']: json.loads((actual_dir / f"{entry['scenario_id']}.json").read_text())
              for entry in report['cases']}
    groups = defaultdict(list)
    lifecycle = []
    for scenario_id, evidence in actual.items():
        case = cases[scenario_id]
        if case['pair_id']:
            groups[case['pair_id']].append(case)
        script = case.get('lifecycle', {}).get('steps', [])
        if not script:
            continue
        actions = evidence['response']['lifecycle_actions']
        checks = []
        for i, step in enumerate(script):
            got = actions[i] if i < len(actions) else {}
            for key, wanted in step['expected'].items():
                if key == 'note':
                    continue
                exact = got.get(key) == wanted
                # Rejection wording is not normalized away: preserve the exact mismatch,
                # and separately record that rejection actually occurred without a state change.
                checks.append({'step_index': i, 'step': step['step'], 'field': key, 'expected': wanted,
                               'actual': got.get(key), 'exact_match': exact,
                               'rejection_observed': bool(got.get('rejected_with')) if key == 'rejected_with' else None})
        lifecycle.append({'scenario_id': scenario_id, 'expected_steps': len(script), 'actual_steps': len(actions),
                          'checks': checks, 'actual_actions': actions})
    pairs = []
    for name, members in sorted(groups.items()):
        members.sort(key=lambda c: c['scenario_id'])
        dimension = members[0]['differentiation']['dimension']
        values = []
        for case in members:
            response = actual[case['scenario_id']]['response']
            value = len(response['violations_reported']) if dimension == 'violation_count' else response.get(
                dimension, response['calculations'].get(dimension))
            if isinstance(value, list):
                value = sorted(value)
            values.append({'scenario_id': case['scenario_id'], 'actual': value})
        unique = {json.dumps(v['actual'], sort_keys=True) for v in values}
        relation = members[0]['differentiation']['expect']
        complete = len(members) == (3 if name == 'LIQ-005' else 2) and all(v['actual'] is not None for v in values)
        pairs.append({'group': name, 'dimension': dimension, 'expected_relation': relation,
                      'constraint': members[0]['differentiation']['distinguishing_constraint'], 'values': values,
                      'holds': complete and (len(unique) == 1 if relation == 'equal' else len(unique) > 1)})
    # Sidecar has no influence on the unchanged ten-dimension rubric.
    checks = [c for item in lifecycle for c in item['checks']]
    output = {'kind': 'actual-application-supplemental-v1', 'suite': report['suite'],
              'upstream_score_unchanged': True, 'pairs': pairs, 'lifecycle': lifecycle,
              'summary': {'pair_groups_checked': len(pairs), 'pair_groups_hold': sum(p['holds'] for p in pairs),
                          'lifecycle_cases': len(lifecycle), 'lifecycle_assertions': len(checks),
                          'literal_matches': sum(c['exact_match'] for c in checks),
                          'literal_mismatches': sum(not c['exact_match'] for c in checks),
                          'nonwording_mismatches': sum(not c['exact_match'] and c['field'] != 'rejected_with' for c in checks),
                          'cleanup_confirmed_cases': sum(e.get('cleanup') == 'rolled back; zero businesses remain' for e in actual.values()),
                          'ledger_mutation_findings': sum(bool(e['response']['records_modified']) for e in actual.values())}}
    # Compact actual output, not input ledgers/oracles/priors. Full local state/graph remains
    # in the private working evidence directory for deeper reproducibility.
    responses = {key: value['response'] for key, value in actual.items()}
    return output, responses
