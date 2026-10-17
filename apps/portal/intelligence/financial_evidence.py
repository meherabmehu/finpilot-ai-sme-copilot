"""Readable provenance graph using authorized snapshot references, never fake citations."""


def evidence_graph(state, comparison):
    nodes = [{'id': 'cash', 'kind': 'calculation', 'label': 'Available recorded cash', 'amount': state['known_cash'],
              'currency': state['currency'], 'date': state['as_of'], 'formula': 'opening balance + paid inflows − paid outflows',
              'source': 'Business opening balance and authorized paid transactions', 'basis': state['cash_basis']}]
    edges = []
    for event in state['events']:
        nodes.append({'id': event['id'], 'kind': 'obligation', 'label': event['description'], 'amount': event['amount'],
                      'currency': state['currency'], 'date': event['date'], 'source': event['source'],
                      'source_id': event['source_id'], 'basis': event['basis']})
        edges.append({'from': event['id'], 'to': 'cash_timeline', 'relationship': event['direction']})
    nodes.append({'id': 'cash_timeline', 'kind': 'projection', 'label': 'Dated cash timeline', 'amount': state['projection'].get('minimum_balance'),
                  'formula': 'cash[d] = cash[d−1] + dated receipts[d] − dated payments[d]', 'basis': 'estimated'})
    edges.append({'from': 'cash', 'to': 'cash_timeline', 'relationship': 'opening point'})
    for index, plan in enumerate(comparison['plans']):
        node_id = f'plan:{index}'
        nodes.append({'id': node_id, 'kind': 'recommendation', 'label': plan['name'], 'amount': plan.get('remaining_gap'),
                      'basis': 'simulated', 'assumptions': plan['dependencies'], 'tradeoffs': plan['tradeoffs'],
                      'formula': comparison['objective']})
        edges.append({'from': 'cash_timeline', 'to': node_id, 'relationship': 'counterfactual comparison'})
        for action in plan['actions']:
            if action.get('event_id'):
                edges.append({'from': action['event_id'], 'to': node_id, 'relationship': action['kind']})
    return {'business_id': state['business_id'], 'fingerprint': state['fingerprint'], 'nodes': nodes, 'edges': edges,
            'limitations': state['limitations'], 'follow_up': 'Confirm external agreements, record actual payments separately, then review the saved decision.'}
