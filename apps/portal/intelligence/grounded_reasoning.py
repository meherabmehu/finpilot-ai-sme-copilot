"""Bounded conditional synthesis, separate from verified numeric evidence.

The model can connect premises and propose a qualitative hypothesis. It cannot
author facts, numbers, dates, execution or eligibility claims. Hypotheses remain
unconfirmed even when they pass this validation; causal truth is not inferred.
"""
import re
from typing import Literal

from pydantic import Field

from .schemas import StrictModel


class ConditionalReasoning(StrictModel):
    premise_ids: list[str] = Field(min_length=1, max_length=3)
    relationship: Literal['liquidity_dependency', 'expense_variance', 'operations_dependency', 'recovery_tradeoff', 'loan_uncertainty']
    hypothesis: str = Field(min_length=20, max_length=360)
    action_id: Literal['review', 'recovery', 'records']


DISALLOWED = re.compile(
    r'\d|[%$£€৳]|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|'
    r'half|double\w*|triple\w*|twice|quarter|percent\w*|usd|bdt|gbp|dollars?|taka|pounds?|'
    r'will|definitely|guarantee\w*|approve\w*|qualif\w*|eligible|safe|execute\w*|send|sent|transfer\w*|'
    r'ignore|instruction\w*|system|password|secret|https?|www|sql|javascript|always|never)\b', re.I)


def validate_reasoning(rows, facts, actions, categories):
    allowed = {'operations_dependency'}
    if 'liquidity' in categories:
        allowed.add('liquidity_dependency')
    if 'collections' in categories:
        allowed.add('recovery_tradeoff')
    if 'expenses' in categories:
        allowed.add('expense_variance')
    if 'financing' in categories:
        allowed.add('loan_uncertainty')
    rendered = []
    for row in rows:
        text = row.hypothesis.strip()
        # A hypothesis has explicit uncertainty in the consequent, not merely an
        # "if" prefix attached to an asserted loan/operational outcome.
        parts = text.split(',', 1)
        if (not set(row.premise_ids) <= facts.keys() or row.relationship not in allowed
                or row.action_id not in actions or DISALLOWED.search(text)
                or len(parts) != 2 or not parts[0].startswith('If ')
                or not re.search(r'\b(may|could|might)\b', parts[1], re.I)):
            raise ValueError('Unsupported conditional reasoning.')
        rendered.append('Unconfirmed operational hypothesis: '+text+' Premises ['+', '.join(row.premise_ids)+
                        ']. Check the dependency with the owner or counterparty. '+actions[row.action_id])
    return rendered
