"""Phase 4 — lite AI catalog and JSON extraction."""

import pytest

from src.core.ai.lite_ai import (
    catalog_to_dict,
    extract_json_object,
    resolve_default_model,
    ProviderInfo,
    _resolve_catalog_defaults,
)


def test_extract_json_object_plain():
    out = extract_json_object('{"a": 1}')
    assert out == {'a': 1}


def test_extract_json_object_fenced():
    text = 'Here is data:\n```json\n{"ok": true}\n```'
    assert extract_json_object(text) == {'ok': True}


def test_catalog_to_dict_picks_configured_default():
    providers = [
        ProviderInfo(id='openai', label='OpenAI', configured=True, models=['gpt-4o-mini']),
        ProviderInfo(id='ollama', label='Ollama', configured=False, models=['llama3.2']),
    ]
    data = catalog_to_dict(providers)
    assert data['any_configured'] is True
    assert data['default_provider'] == 'openai'
    assert data['providers'][0]['id'] == 'openai'


def test_resolve_catalog_defaults_prefers_ollama_when_live():
    providers = [
        ProviderInfo(id='openai', label='OpenAI', configured=True, online=True, models=['gpt-4o-mini']),
        ProviderInfo(
            id='ollama',
            label='Ollama',
            configured=True,
            online=True,
            models=['llama3.2:latest'],
            default_model='llama3.2:latest',
        ),
    ]
    prov, model = _resolve_catalog_defaults(providers)
    assert prov == 'ollama'
    assert model == 'llama3.2:latest'


def test_resolve_default_model_fallback(monkeypatch):
    monkeypatch.setattr(
        'src.core.ai.lite_ai._key',
        lambda _name: '',
    )
    assert resolve_default_model('anthropic').startswith('claude')
