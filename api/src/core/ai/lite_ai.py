"""Lite AI — any configured provider/key, dynamic model catalog."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Static fallbacks when live list APIs are unavailable
OPENAI_MODELS = [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-3.5-turbo',
]
ANTHROPIC_MODELS = [
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022',
    'claude-3-opus-20240229',
]
GEMINI_MODELS = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-2.0-flash',
]
OLLAMA_DEFAULT_MODELS = ['llama3.2', 'llama3.1', 'mistral', 'phi3', 'qwen2.5']


@dataclass
class ProviderInfo:
    id: str
    label: str
    configured: bool
    models: list[str]
    default_model: Optional[str] = None
    hint: Optional[str] = None
    online: bool = False


def _key(name: str) -> str:
    return (getattr(settings, name, None) or os.environ.get(name) or '').strip()


def _has_key(value: str) -> bool:
    return bool(value) and 'placeholder' not in value.lower() and len(value) > 8


def resolve_default_provider() -> str:
    explicit = (_key('AI_DEFAULT_PROVIDER') or settings.AI_PROVIDER or 'openai').lower()
    if explicit in ('openai', 'anthropic', 'gemini', 'ollama', 'azure'):
        if explicit == 'azure':
            return 'openai'
        if explicit == 'ollama' or _key('OLLAMA_BASE_URL'):
            if explicit == 'ollama' or not _has_key(_key('OPENAI_API_KEY')):
                return 'ollama' if _key('OLLAMA_BASE_URL') or explicit == 'ollama' else explicit
        return explicit
    if _has_key(_key('OPENAI_API_KEY')):
        return 'openai'
    if _has_key(_key('ANTHROPIC_API_KEY')):
        return 'anthropic'
    if _has_key(_key('GEMINI_API_KEY')):
        return 'gemini'
    return 'ollama'


def resolve_default_model(provider: str) -> str:
    custom = (_key('AI_DEFAULT_MODEL') or '').strip()
    if not custom and settings.AI_MODEL and settings.AI_MODEL != 'gpt-4':
        custom = settings.AI_MODEL.strip()
    if custom:
        return custom
    defaults = {
        'openai': 'gpt-4o-mini',
        'anthropic': 'claude-3-5-haiku-20241022',
        'gemini': 'gemini-1.5-flash',
        'ollama': 'llama3.2',
    }
    return defaults.get(provider, 'gpt-4o-mini')


async def _fetch_openai_models(api_key: str) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            if r.status_code != 200:
                return OPENAI_MODELS
            data = r.json()
            ids = [
                m['id']
                for m in data.get('data', [])
                if isinstance(m, dict)
                and (
                    m['id'].startswith('gpt-')
                    or m['id'].startswith('o1')
                    or m['id'].startswith('o3')
                )
            ]
            return sorted(set(ids), reverse=True)[:30] or OPENAI_MODELS
    except Exception as exc:
        logger.debug('OpenAI model list failed: %s', exc)
        return OPENAI_MODELS


async def _probe_ollama(base_url: str) -> tuple[list[str], bool]:
    """Return (model names from Ollama, server reachable). No fake list when offline."""
    try:
        async with httpx.AsyncClient(base_url=base_url.rstrip('/'), timeout=5) as client:
            r = await client.get('/api/tags')
            if r.status_code != 200:
                return [], False
            data = r.json()
            names = sorted(
                {m.get('name', '').strip() for m in data.get('models', []) if m.get('name', '').strip()}
            )
            return names, True
    except Exception as exc:
        logger.debug('Ollama model list failed: %s', exc)
        return [], False


async def build_provider_catalog() -> list[ProviderInfo]:
    openai_key = _key('OPENAI_API_KEY') or _key('AI_API_KEY')
    anthropic_key = _key('ANTHROPIC_API_KEY')
    gemini_key = _key('GEMINI_API_KEY') or _key('GOOGLE_API_KEY')
    ollama_url = _key('OLLAMA_BASE_URL') or 'http://localhost:11434'

    providers: list[ProviderInfo] = []

    if _has_key(openai_key):
        models = await _fetch_openai_models(openai_key)
        providers.append(
            ProviderInfo(
                id='openai',
                label='OpenAI',
                configured=True,
                online=True,
                models=models,
                default_model=_pick_default_model(models, 'openai'),
            )
        )

    if _has_key(anthropic_key):
        providers.append(
            ProviderInfo(
                id='anthropic',
                label='Anthropic',
                configured=True,
                online=True,
                models=ANTHROPIC_MODELS,
                default_model=_pick_default_model(ANTHROPIC_MODELS, 'anthropic'),
            )
        )

    if _has_key(gemini_key):
        providers.append(
            ProviderInfo(
                id='gemini',
                label='Google Gemini',
                configured=True,
                online=True,
                models=GEMINI_MODELS,
                default_model=_pick_default_model(GEMINI_MODELS, 'gemini'),
            )
        )

    ollama_models, ollama_online = await _probe_ollama(ollama_url)
    providers.append(
        ProviderInfo(
            id='ollama',
            label='Ollama (local)',
            configured=ollama_online and bool(ollama_models),
            online=ollama_online,
            models=ollama_models,
            default_model=ollama_models[0] if ollama_models else None,
            hint=None
            if ollama_online and ollama_models
            else (
                'Ollama is running but no models found. Run: ollama pull llama3.2'
                if ollama_online
                else f'Start Ollama at {ollama_url} (ollama serve)'
            ),
        )
    )

    return [p for p in providers if p.configured or p.id == 'ollama']


def _pick_default_model(models: list[str], provider: str) -> str:
    preferred = resolve_default_model(provider)
    if preferred in models:
        return preferred
    return models[0] if models else preferred


def _resolve_catalog_defaults(providers: list[ProviderInfo]) -> tuple[str, str]:
    """Pick default provider/model from live configured providers only."""
    configured = [p for p in providers if p.configured and p.models]
    if not configured:
        return resolve_default_provider(), resolve_default_model(resolve_default_provider())

    priority = ['ollama', 'openai', 'anthropic', 'gemini']
    explicit = resolve_default_provider().lower()
    chosen: Optional[ProviderInfo] = None

    if any(p.id == explicit for p in configured):
        chosen = next(p for p in configured if p.id == explicit)
    else:
        for pid in priority:
            match = next((p for p in configured if p.id == pid), None)
            if match:
                chosen = match
                break
        if not chosen:
            chosen = configured[0]

    model = chosen.default_model if chosen.default_model in chosen.models else chosen.models[0]
    return chosen.id, model


def catalog_to_dict(providers: list[ProviderInfo]) -> dict[str, Any]:
    default_provider, default_model = _resolve_catalog_defaults(providers)
    return {
        'default_provider': default_provider,
        'default_model': default_model,
        'providers': [
            {
                'id': p.id,
                'label': p.label,
                'configured': p.configured,
                'online': p.online,
                'models': p.models,
                'default_model': p.default_model,
                'hint': p.hint,
            }
            for p in providers
        ],
        'any_configured': any(p.configured for p in providers),
    }


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    json_mode: bool = True,
) -> dict[str, Any]:
    """Run chat completion; returns {content, provider, model, usage}."""
    prov = (provider or resolve_default_provider()).lower()
    catalog = await build_provider_catalog()
    configured_ids = {p.id for p in catalog if p.configured}
    if prov not in configured_ids:
        raise ValueError(
            f'Provider "{prov}" is not configured. Add API keys to .env — see /api/v1/ai/catalog'
        )

    mdl = model or resolve_default_model(prov)
    timeout = float(settings.AI_MAX_TOKENS and 120 or 120)

    if prov == 'openai':
        return await _openai_chat(messages, mdl, temperature, max_tokens, json_mode)
    if prov == 'anthropic':
        return await _anthropic_chat(messages, mdl, temperature, max_tokens, json_mode)
    if prov == 'gemini':
        return await _gemini_chat(messages, mdl, temperature, max_tokens, json_mode)
    if prov == 'ollama':
        return await _ollama_chat(messages, mdl, temperature, max_tokens, json_mode)
    raise ValueError(f'Unknown provider: {prov}')


async def _openai_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    key = _key('OPENAI_API_KEY') or _key('AI_API_KEY')
    payload: dict[str, Any] = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json=payload,
        )
        if r.status_code != 200:
            raise ValueError(f'OpenAI error {r.status_code}: {r.text[:500]}')
        data = r.json()
        content = data['choices'][0]['message']['content'] or ''
        usage = data.get('usage', {})
        return {
            'content': content,
            'provider': 'openai',
            'model': model,
            'usage': {
                'input_tokens': usage.get('prompt_tokens', 0),
                'output_tokens': usage.get('completion_tokens', 0),
            },
        }


async def _anthropic_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    key = _key('ANTHROPIC_API_KEY')
    system = ''
    user_messages = []
    for msg in messages:
        if msg.get('role') == 'system':
            system += msg.get('content', '') + '\n'
        else:
            user_messages.append(msg)
    if json_mode and system:
        system += '\nRespond with valid JSON only, no markdown fences.'
    elif json_mode:
        system = 'Respond with valid JSON only, no markdown fences.'

    payload: dict[str, Any] = {
        'model': model,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'messages': user_messages or messages,
    }
    if system.strip():
        payload['system'] = system.strip()

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            },
            json=payload,
        )
        if r.status_code != 200:
            raise ValueError(f'Anthropic error {r.status_code}: {r.text[:500]}')
        data = r.json()
        blocks = data.get('content', [])
        content = ''.join(b.get('text', '') for b in blocks if b.get('type') == 'text')
        usage = data.get('usage', {})
        return {
            'content': content,
            'provider': 'anthropic',
            'model': model,
            'usage': {
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
            },
        }


async def _gemini_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    key = _key('GEMINI_API_KEY') or _key('GOOGLE_API_KEY')
    parts = []
    for msg in messages:
        role = 'user' if msg.get('role') != 'model' else 'model'
        if msg.get('role') == 'system':
            parts.append({'role': 'user', 'parts': [{'text': f"System: {msg.get('content', '')}"}]})
        else:
            parts.append({'role': role, 'parts': [{'text': msg.get('content', '')}]})

    payload = {
        'contents': parts,
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': max_tokens,
        },
    }
    if json_mode:
        payload['generationConfig']['responseMimeType'] = 'application/json'

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, json=payload)
        if r.status_code != 200:
            raise ValueError(f'Gemini error {r.status_code}: {r.text[:500]}')
        data = r.json()
        candidates = data.get('candidates', [])
        text = ''
        if candidates:
            parts_out = candidates[0].get('content', {}).get('parts', [])
            text = ''.join(p.get('text', '') for p in parts_out)
        return {
            'content': text,
            'provider': 'gemini',
            'model': model,
            'usage': {'input_tokens': 0, 'output_tokens': 0},
        }


async def _ollama_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    base = _key('OLLAMA_BASE_URL') or 'http://localhost:11434'
    ollama_messages = [{'role': m.get('role', 'user'), 'content': m.get('content', '')} for m in messages]
    if json_mode:
        ollama_messages.insert(0, {
            'role': 'system',
            'content': 'You must respond with valid JSON only.',
        })
    payload = {
        'model': model,
        'messages': ollama_messages,
        'stream': False,
        'options': {'temperature': temperature, 'num_predict': max_tokens},
    }
    async with httpx.AsyncClient(base_url=base.rstrip('/'), timeout=180) as client:
        r = await client.post('/api/chat', json=payload)
        if r.status_code != 200:
            raise ValueError(f'Ollama error {r.status_code}: {r.text[:500]}')
        data = r.json()
        content = data.get('message', {}).get('content', '')
        return {
            'content': content,
            'provider': 'ollama',
            'model': model,
            'usage': {
                'input_tokens': data.get('prompt_eval_count', 0),
                'output_tokens': data.get('eval_count', 0),
            },
        }


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse JSON from model output (handles markdown fences)."""
    text = (text or '').strip()
    if not text:
        raise ValueError('Empty AI response')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        return json.loads(match.group(1).strip())
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError('AI response was not valid JSON')
