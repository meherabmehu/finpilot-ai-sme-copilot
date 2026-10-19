"""Operator-only safe availability check; no ledger or secret values printed."""
import json
import httpx
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.portal.intelligence.ai_grounding import provider_status


class Command(BaseCommand):
    help = 'Check Grok configuration; --live verifies model availability without financial data.'

    def add_arguments(self, parser):
        parser.add_argument('--live', action='store_true')

    def handle(self, *args, **options):
        result = provider_status() | {'live_verified': False}
        if options['live'] and result['configured']:
            try:
                with httpx.Client(timeout=settings.XAI_TIMEOUT_SECONDS, follow_redirects=False) as client:
                    response = client.get(settings.XAI_BASE_URL.rstrip('/')+'/models', headers={'Authorization': 'Bearer '+settings.XAI_API_KEY})
                response.raise_for_status()
                result['live_verified'] = any(row.get('id') == settings.XAI_MODEL for row in response.json().get('data', []))
                result['reason'] = 'Configured model was listed by provider.' if result['live_verified'] else 'Configured model not returned by provider; verify owner access.'
            except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                result['reason'] = 'Provider check failed; upstream details and credentials withheld.'
        self.stdout.write(json.dumps(result))
