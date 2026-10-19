"""Operator-only safe availability check; no ledger or secret values printed."""
import json
import time
import httpx
from django.core.management.base import BaseCommand
from apps.portal.intelligence.ai_grounding import provider_status
from apps.portal.intelligence.ai_provider import selected_provider
from apps.portal.intelligence.ai_grounding import GroundedSelection, selection_schema
from apps.portal.intelligence.grounded_reasoning import validate_reasoning


class Command(BaseCommand):
    help = 'Check selected AI provider configuration; --live verifies model availability without financial data.'

    def add_arguments(self, parser):
        parser.add_argument('--live', action='store_true')
        parser.add_argument('--inference', action='store_true', help='One bounded synthetic structured-output request; no ledger data is sent.')

    def handle(self, *args, **options):
        provider = selected_provider()
        result = provider_status() | {'live_verified': False}
        if options['live'] and result['configured']:
            try:
                with httpx.Client(timeout=provider.timeout, follow_redirects=False) as client:
                    response = client.get(provider.base_url.rstrip('/')+'/models', headers={'Authorization': 'Bearer '+provider.key})
                response.raise_for_status()
                result['live_verified'] = any(row.get('id') == provider.model for row in response.json().get('data', []))
                result['reason'] = 'Configured model was listed by provider.' if result['live_verified'] else 'Configured model not returned by provider; verify owner access.'
            except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError):
                result['reason'] = 'Provider check failed; upstream details and credentials withheld.'
        if options['inference'] and result['configured']:
            started = time.monotonic()
            result['live_inference_verified'] = False
            facts = {'F1': 'Synthetic overdue receivable total: USD 300.00.',
                     'F2': 'Synthetic dated-only reserve gap: USD 100.00; collection date is unknown.'}
            actions = {'review': 'Review the synthetic invoice and confirm receipt timing.'}
            try:
                with httpx.Client(timeout=provider.timeout, follow_redirects=False) as client:
                    response = client.post(provider.base_url.rstrip('/')+'/chat/completions',
                        headers={'Authorization': 'Bearer '+provider.key},
                        json={'model': provider.model, 'max_tokens': provider.max_tokens, 'temperature': provider.temperature,
                              **({'reasoning_effort': 'low'} if provider.name == 'groq' and provider.model.startswith('openai/gpt-oss-') else {}),
                              'messages': [{'role': 'system', 'content': 'Select only supplied evidence IDs. Synthetic data only. Return action review, question_ids empty and reasoning empty. Do not create numbers.'},
                                           {'role': 'user', 'content': json.dumps({'question': 'How much is overdue and what should I check?', 'facts':facts, 'actions':actions})}],
                              'response_format': {'type':'json_schema','json_schema':{'name':'synthetic_financial_check','strict':True,'schema':selection_schema()}}})
                result['inference_http_status'] = response.status_code
                response.raise_for_status()
                if len(response.content) > 100000:
                    raise ValueError('Response limit exceeded.')
                body=response.json()
                output=GroundedSelection.model_validate_json(body['choices'][0]['message']['content'])
                if not set(output.evidence_ids) <= facts.keys() or not set(output.action_ids) <= actions.keys() or output.question_ids:
                    raise ValueError('Unsupported synthetic evidence.')
                validate_reasoning(output.reasoning, facts, actions, ['collections','liquidity'])
                result['live_inference_verified'] = True
                result['inference_basis'] = 'Real inference with strict JSON schema and synthetic evidence; no ledger data sent.'
                result['rate_limit_headers_present'] = any(k.startswith('x-ratelimit-') for k in response.headers)
                result['token_usage'] = {k:body.get('usage',{}).get(k) for k in ('prompt_tokens','completion_tokens','total_tokens')}
            except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
                result['inference_reason'] = 'Request failed or unsupported output rejected; upstream content and credentials withheld.'
            result['inference_elapsed_ms'] = int((time.monotonic()-started)*1000)
        self.stdout.write(json.dumps(result))
