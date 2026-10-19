"""Configuration validation without network calls or secret-bearing diagnostics."""
from django.conf import settings
from django.core.checks import Warning, register


@register()
def ai_configuration(app_configs, **kwargs):
    from .intelligence.ai_grounding import provider_status
    if settings.FINPILOT_AI_ENABLED and (settings.XAI_API_KEY or settings.XAI_MODEL) and not provider_status()['configured']:
        return [Warning('Grok configuration is incomplete or invalid; use the documented server-side configuration.',
                        hint='Set both XAI_API_KEY and an accessible XAI_MODEL; official HTTPS endpoint only. Financial calculations remain available.', id='portal.W001')]
    return []
