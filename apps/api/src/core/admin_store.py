"""File-backed platform admin data when DB is unavailable or for AI provider secrets."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import get_settings

_ROOT = Path(__file__).resolve().parents[4]
_STORE_DIR = _ROOT / '.tenderiq'
_USERS_FILE = _STORE_DIR / 'platform_users.json'
_PROVIDERS_FILE = _STORE_DIR / 'ai_providers.json'
_DISMISSED_FILE = _STORE_DIR / 'dismissed_failed_jobs.json'


def _ensure_dir() -> None:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> None:
    _ensure_dir()
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def _encrypt_secret(value: str) -> str:
    secret = (get_settings().JWT_SECRET or 'dev-secret').encode()
    raw = value.encode()
    enc = bytes(b ^ secret[i % len(secret)] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(enc).decode()


def _decrypt_secret(token: str) -> str:
    secret = (get_settings().JWT_SECRET or 'dev-secret').encode()
    enc = base64.urlsafe_b64decode(token.encode())
    raw = bytes(b ^ secret[i % len(secret)] for i, b in enumerate(enc))
    return raw.decode()


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return ''
    if len(value) <= 8:
        return '****'
    return f'{value[:3]}****{value[-4:]}'


# --- Users ---

def list_platform_users() -> list[dict]:
    return _read_json(_USERS_FILE, [])


def save_platform_users(users: list[dict]) -> None:
    _write_json(_USERS_FILE, users)


def create_platform_user(data: dict) -> dict:
    users = list_platform_users()
    email = (data.get('email') or '').strip().lower()
    if any(u.get('email', '').lower() == email for u in users):
        raise ValueError('Email already exists')
    user = {
        'id': str(uuid.uuid4()),
        'name': data.get('name') or email.split('@')[0],
        'email': email,
        'role': data.get('role') or 'viewer',
        'status': data.get('status') or 'active',
        'organization': data.get('organization') or '—',
        'permissions': data.get('permissions') or [],
        'lastActive': datetime.now(timezone.utc).isoformat(),
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'deleted': False,
    }
    users.append(user)
    save_platform_users(users)
    return user


def update_platform_user(user_id: str, data: dict) -> Optional[dict]:
    users = list_platform_users()
    for i, u in enumerate(users):
        if u.get('id') == user_id and not u.get('deleted'):
            users[i] = {**u, **data, 'id': user_id}
            save_platform_users(users)
            return users[i]
    return None


def soft_delete_platform_user(user_id: str) -> bool:
    return update_platform_user(user_id, {'status': 'inactive', 'deleted': True}) is not None


# --- AI providers ---

DEFAULT_PROVIDERS = [
    {
        'id': 'ollama',
        'name': 'Ollama',
        'type': 'ollama',
        'base_url': 'http://localhost:11434',
        'api_key_masked': '',
        'is_active': True,
        'is_default': True,
        'models': [
            {
                'id': 'llama3',
                'name': 'Llama 3',
                'provider': 'Ollama',
                'max_tokens': 8192,
                'cost_per_1k_tokens': 0,
                'is_default': True,
            }
        ],
        'settings': {
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0,
        },
    }
]


def list_ai_providers(public: bool = True) -> list[dict]:
    items = _read_json(_PROVIDERS_FILE, None)
    if items is None:
        items = [dict(p) for p in DEFAULT_PROVIDERS]
        _write_json(_PROVIDERS_FILE, items)
    if not public:
        return items
    out = []
    for p in items:
        row = {k: v for k, v in p.items() if k != 'api_key_enc'}
        row['api_key_masked'] = mask_secret(
            _decrypt_secret(p['api_key_enc']) if p.get('api_key_enc') else ''
        ) or ('configured' if p.get('api_key_enc') else '')
        out.append(row)
    return out


def _find_provider(provider_id: str) -> Optional[dict]:
    for p in list_ai_providers(public=False):
        if p.get('id') == provider_id:
            return p
    return None


def create_ai_provider(data: dict) -> dict:
    providers = list_ai_providers(public=False)
    pid = (data.get('id') or data.get('type') or 'provider') + '-' + uuid.uuid4().hex[:6]
    entry: dict[str, Any] = {
        'id': pid,
        'name': data.get('name') or 'New Provider',
        'type': data.get('type') or 'openai',
        'base_url': data.get('base_url') or '',
        'is_active': data.get('is_active', True),
        'is_default': data.get('is_default', False),
        'models': data.get('models') or [],
        'settings': data.get('settings')
        or {
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0,
        },
    }
    if data.get('api_key'):
        entry['api_key_enc'] = _encrypt_secret(data['api_key'])
    if entry.get('is_default'):
        for p in providers:
            p['is_default'] = False
    providers.append(entry)
    _write_json(_PROVIDERS_FILE, providers)
    return list_ai_providers(public=True)[-1]


def update_ai_provider(provider_id: str, data: dict) -> Optional[dict]:
    providers = list_ai_providers(public=False)
    for i, p in enumerate(providers):
        if p.get('id') == provider_id:
            if data.get('api_key'):
                p['api_key_enc'] = _encrypt_secret(data.pop('api_key'))
            p.update({k: v for k, v in data.items() if k != 'api_key'})
            if p.get('is_default'):
                for other in providers:
                    if other.get('id') != provider_id:
                        other['is_default'] = False
            providers[i] = p
            _write_json(_PROVIDERS_FILE, providers)
            return list_ai_providers(public=True)[i]
    return None


def delete_ai_provider(provider_id: str) -> bool:
    providers = [p for p in list_ai_providers(public=False) if p.get('id') != provider_id]
    if len(providers) == len(list_ai_providers(public=False)):
        return False
    if providers and not any(p.get('is_default') for p in providers):
        providers[0]['is_default'] = True
    _write_json(_PROVIDERS_FILE, providers)
    return True


def get_provider_secret(provider_id: str) -> Optional[str]:
    p = _find_provider(provider_id)
    if not p or not p.get('api_key_enc'):
        return None
    return _decrypt_secret(p['api_key_enc'])


# --- Dismissed failed jobs ---

def list_dismissed_failed_jobs() -> set[str]:
    return set(_read_json(_DISMISSED_FILE, []))


def dismiss_failed_job(job_id: str) -> None:
    dismissed = list_dismissed_failed_jobs()
    dismissed.add(job_id)
    _write_json(_DISMISSED_FILE, sorted(dismissed))
