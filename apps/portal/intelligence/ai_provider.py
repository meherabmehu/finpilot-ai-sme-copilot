"""Server-only provider selection; credentials never enter public status output."""
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.conf import settings


@dataclass(frozen=True, repr=False)
class Provider:
    name: str
    label: str
    key: str
    base_url: str
    model: str
    timeout: float
    max_tokens: int
    temperature: float

    @property
    def namespace(self):
        return 'groq' if self.name == 'groq' else 'grok'

    @property
    def configured(self):
        host, path = ('api.groq.com', '/openai/v1') if self.name == 'groq' else ('api.x.ai', '/v1')
        try:
            url = urlsplit(self.base_url)
            safe = (url.scheme == 'https' and url.hostname == host and not url.username and not url.password
                    and url.path.rstrip('/') == path and not url.query and not url.fragment and url.port in (None, 443))
        except ValueError:
            safe = False
        return bool(settings.FINPILOT_AI_ENABLED and settings.FINPILOT_AI_PROVIDER in ('auto', self.name)
                    and self.key and self.model and safe)


def selected_provider():
    name = settings.FINPILOT_AI_PROVIDER
    groq = name == 'groq' or (name == 'auto' and not settings.XAI_API_KEY and bool(settings.GROQ_API_KEY))
    prefix = 'GROQ' if groq else 'XAI'
    return Provider('groq' if groq else 'xai', 'Groq' if groq else 'Grok',
                    getattr(settings, prefix+'_API_KEY'), getattr(settings, prefix+'_BASE_URL'),
                    getattr(settings, prefix+'_MODEL'), getattr(settings, prefix+'_TIMEOUT_SECONDS'),
                    getattr(settings, prefix+'_MAX_OUTPUT_TOKENS'), getattr(settings, prefix+'_TEMPERATURE'))
