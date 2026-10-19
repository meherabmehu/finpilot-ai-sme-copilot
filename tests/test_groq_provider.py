"""Groq routing, isolation, and fail-closed evidence validation."""
from unittest.mock import patch

import pytest
from django.core.cache import cache

from apps.portal.advisor import answer
from apps.portal.intelligence.ai_grounding import provider_status, classify_ambiguous
from apps.portal.intelligence.ai_provider import selected_provider
from tests.test_competition_upgrade import reply


@pytest.fixture
def groq(settings):
    cache.clear()
    settings.FINPILOT_AI_ENABLED = True
    settings.FINPILOT_AI_PROVIDER = 'groq'
    settings.GROQ_API_KEY = 'synthetic-groq-key'
    settings.GROQ_MODEL = 'openai/gpt-oss-20b'
    settings.GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
    yield settings
    cache.clear()


@pytest.mark.parametrize('url', ['http://api.groq.com/openai/v1', 'https://api.groq.com.evil.test/openai/v1',
    'https://api.groq.com/openai/v1?token=secret', 'https://user@api.groq.com/openai/v1',
    'https://api.groq.com:444/openai/v1', 'https://api.x.ai/v1'])
def test_groq_rejects_other_endpoints(groq, url):
    groq.GROQ_BASE_URL = url
    assert not provider_status()['configured']


def test_groq_routing_credentials_and_circuit_isolation(groq, owner, business):
    cache.set('grok:circuit', True, 30)
    output = {'evidence_ids': ['F1'], 'action_ids': ['review'], 'question_ids': []}
    trace = []
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post', return_value=reply(output)) as post:
        text = answer(owner, business, 'What is my cash?', trace)
    assert 'Groq-assisted' in text and trace[0]['provider'] == 'groq'
    assert post.call_args.args[0] == 'https://api.groq.com/openai/v1/chat/completions'
    assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer synthetic-groq-key'
    assert post.call_args.kwargs['json']['model'] == groq.GROQ_MODEL
    assert 'synthetic-groq-key' not in text


def test_groq_scope_and_bad_evidence_fallback(groq, owner, business):
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post', return_value=reply({'scope': 'financial'})):
        assert classify_ambiguous('Can we handle it?', []) == 'financial'
    with patch('apps.portal.intelligence.ai_grounding.httpx.Client.post', return_value=reply(
            {'evidence_ids': ['invented'], 'action_ids': [], 'question_ids': []})) as post:
        text = answer(owner, business, 'What is my cash?')
        assert 'Groq unavailable or output rejected' in text
        assert 'temporarily unavailable' in answer(owner, business, 'What is my reserve?')
        assert post.call_count == 1


def test_auto_prefers_explicit_xai_credentials(groq):
    groq.FINPILOT_AI_PROVIDER = 'auto'
    groq.XAI_API_KEY = ''
    assert selected_provider().name == 'groq'
    groq.XAI_API_KEY = 'synthetic-xai'
    assert selected_provider().name == 'xai'
