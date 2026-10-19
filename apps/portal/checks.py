"""Configuration validation without network calls or secret-bearing diagnostics."""
from django.conf import settings
from django.core.checks import Warning, register


@register()
def ai_configuration(app_configs, **kwargs):
    from .intelligence.ai_grounding import provider_status
    from .intelligence.ai_provider import selected_provider
    provider = selected_provider()
    # Groq has a default model; that alone does not mean setup was attempted.
    attempted = bool(provider.key or (provider.name == 'xai' and provider.model) or settings.FINPILOT_AI_PROVIDER == 'groq')
    if settings.FINPILOT_AI_ENABLED and attempted and not provider_status()['configured']:
        prefix = 'GROQ' if provider.name == 'groq' else 'XAI'
        return [Warning(provider.label+' configuration is incomplete or invalid; use the documented server-side configuration.',
                        hint=f'Set {prefix}_API_KEY and an accessible {prefix}_MODEL; official HTTPS endpoint only. Financial calculations remain available.', id='portal.W001')]
    return []
