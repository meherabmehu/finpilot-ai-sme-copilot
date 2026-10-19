"""Manual-review-compatible catalog validation; never automatically changes terms."""
import json
from pathlib import Path
import httpx
from django.core.management.base import BaseCommand, CommandError
from apps.portal.intelligence.loan_catalog import CATALOG, PublicProduct


class Command(BaseCommand):
    help = 'Validate bundled/reviewed JSON loan sources; --live checks official URLs, never marks terms refreshed.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=Path)
        parser.add_argument('--live', action='store_true')

    def handle(self, *args, **options):
        try:
            raw = json.loads(options['file'].read_text(encoding='utf-8')) if options['file'] else CATALOG
            if not isinstance(raw, list) or len(raw) > 100:
                raise ValueError('Catalog bound exceeded.')
            products = [PublicProduct.model_validate(p) for p in raw]
        except (ValueError, OSError) as exc:
            raise CommandError('Catalog validation failed; review schema, official sources and bounds.') from exc
        for product in products:
            status = 'schema valid; source content requires manual review'
            if options['live']:
                try:
                    with httpx.Client(timeout=15, follow_redirects=False) as client:
                        response = client.get(product.source_url)
                    status = f'HTTP {response.status_code}; manually verify page content and any redirect before updating verified_at'
                except httpx.HTTPError:
                    status = 'source unavailable; verification date unchanged'
            self.stdout.write(json.dumps({'id': product.id, 'status': status}))
