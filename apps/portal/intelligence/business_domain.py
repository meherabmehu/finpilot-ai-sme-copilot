"""Industry patterns are prompts for review, never asserted company facts."""
from datetime import date
from decimal import Decimal

from ..engine import money

DOMAINS = {
    'Retail': ('inventory', 'stock', 'supplier', 'replenishment'),
    'E-commerce': ('platform', 'settlement', 'refund', 'advertising', 'fulfillment'),
    'Restaurant': ('food', 'ingredients', 'supplies', 'waste', 'payroll'),
    'Manufacturing': ('raw material', 'production', 'equipment', 'maintenance', 'payroll'),
    'Services': ('client', 'contract', 'project', 'payroll'),
    'Wholesale': ('inventory', 'supplier', 'customer credit', 'receivable'),
    'Other': (),
}
QUESTIONS = {
    'Retail': 'Would delaying inventory replenishment cause a stockout, and is another supplier available?',
    'E-commerce': 'What are the actual platform settlement delay, return obligations and fulfillment deadlines?',
    'Restaurant': 'Which food replenishment and staffing costs are necessary to keep trading each day?',
    'Manufacturing': 'Which raw material or maintenance payment blocks a dated production commitment?',
    'Services': 'Which client or project milestones control collections and essential staffing commitments?',
    'Wholesale': 'Which customer credit and supplier terms govern the next inventory cycle?',
    'Other': 'Which payments interrupt operations if delayed, and what evidence supports that dependency?',
}


def domain_context(business, state):
    kind = business.category if business.category in DOMAINS else 'Other'
    matches = [e['id'] for e in state['events'] if any(w in e.get('category', '').casefold() for w in DOMAINS[kind])]
    return {'type': kind, 'size': business.size, 'country': business.country, 'currency': business.currency,
            'owner_context': business.description[:2000], 'matched_references': matches[:20],
            'question': QUESTIONS[kind],
            'guidance': (f'Review recorded {kind.lower()} commitments before changing spending. ' + QUESTIONS[kind]) if matches else
                        f'No category-linked {kind.lower()} operational dependency is established. ' + QUESTIONS[kind],
            'basis': 'Business type is owner-recorded; category matches suggest questions, not contractual facts.'}


def assess_payment(event, state):
    today = date.fromisoformat(state['as_of'])
    prior = next((r for r in state['overdue'] if f"tx:{r['id']}" == event['id']), None)
    due = prior['date'] if prior else event['date']
    days = (date.fromisoformat(due)-today).days
    restricted = event['category'].casefold() in {s.casefold() for s in state['policy']['restricted_categories']}
    protected = (event.get('payroll') and state['policy']['protect_payroll']) or (event.get('critical') and state['policy']['protect_critical_suppliers']) or restricted
    domain = state.get('business_context', {}).get('category', 'Other')
    pattern = any(s in event['category'].casefold() for s in DOMAINS.get(domain, ()))
    if protected:
        priority, impact, sufficiency = 'Critical', 'Protected by the recorded owner policy; confirm actual operational consequences.', 'Explicit recorded protection'
    elif event.get('critical') or event.get('payroll'):
        priority, impact, sufficiency = 'High', 'Recorded criticality exists, but policy protection is disabled.', 'Owner classification; review policy'
    elif pattern:
        priority, impact, sufficiency = 'High', f'May affect {domain.lower()} operations; interruption and alternative supply are unverified.', 'Preliminary category/type inference'
    else:
        priority, impact, sufficiency = 'Review Needed', 'Operational impact is unknown. Lack of evidence does not make this bill unimportant.', 'Insufficient operational evidence'
    return {'suggested_priority': priority, 'urgency': 'Overdue' if days < 0 else 'Due today' if not days else 'Within 7 days' if days <= 7 else 'Later in horizon',
            'days_to_due': days, 'impact': impact, 'evidence_sufficiency': sufficiency, 'owner_confirmation_needed': not protected,
            'supporting_evidence': [event['id'], f"Recorded category: {event['category']}", f'Recorded due: {due}'],
            'missing_information': ['Contract terms, penalty evidence, operational dependency and availability of alternatives'], 'protected': bool(protected)}


def obligation_summary(state, priorities):
    total = sum((Decimal(e['amount']) for e in priorities), Decimal('0'))
    protected = sum((Decimal(e['amount']) for e in priorities if e['protected']), Decimal('0'))
    overdue = sum((Decimal(r['amount']) for r in state['overdue'] if r['direction'] == 'outflow' and r['date'] < state['as_of']), Decimal('0'))
    return {k: str(money(v)) for k, v in {'total': total, 'protected': protected, 'other': total-protected, 'overdue': overdue}.items()}


def category_review(business):
    """Suggestions only: source descriptions/categories remain untouched."""
    aliases = {'operating expen.': 'Operating Expenses', 'operating expenses': 'Operating Expenses',
               'salary': 'Payroll', 'salaries': 'Payroll', 'wages': 'Payroll', 'stock': 'Inventory'}
    rows = []
    for category in business.transactions.filter(archived=False).values_list('category', flat=True).distinct()[:100]:
        key = category.strip().casefold()
        if key in ('general', 'o', '') or key in aliases:
            rows.append({'recorded': category, 'suggested': aliases.get(key),
                         'reason': 'Ambiguous category needs owner review.' if key in ('general', 'o', '') else 'Consider consistent naming; no evidence was overwritten.'})
    return rows
