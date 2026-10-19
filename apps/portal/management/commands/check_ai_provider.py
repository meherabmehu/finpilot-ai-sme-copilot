"""Operator-only safe availability check; no ledger or secret values printed."""
import json
import httpx
from django.core.management.base import BaseCommand
from apps.portal.intelligence.ai_grounding import provider_status
from apps.portal.intelligence.ai_provider import selected_provider


class Command(BaseCommand):
    help = 'Check selected AI provider configuration; --live verifies model availability without financial data.'

    def add_arguments(self, parser):
        parser.add_argument('--live', action='store_true')

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
        self.stdout.write(json.dumps(result))
