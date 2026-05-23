"""Platform admin persistence (MySQL). DB helpers below are used by admin_platform routes.

Legacy JSON under .tenderiq/ is deprecated and not written by API handlers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet

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


def _get_fernet() -> Fernet:
    secret = get_settings().JWT_SECRET or 'dev-secret'
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def _encrypt_secret(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt_secret(token: str) -> str:
    return _get_fernet().decrypt(token.encode()).decode()


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


# --- DB-aware variants (used by admin_platform.py with fallback to file above) ---
# These accept a SQLAlchemy async session as the first argument.
# They follow the same patterns as the file-based functions above.

from .models import AIProvider as AIProviderModel, DismissedFailedJob as DismissedFailedJobModel


async def list_ai_providers_db(db, public: bool = True) -> list[dict]:
    from sqlalchemy import select

    result = await db.execute(select(AIProviderModel).order_by(AIProviderModel.created_at.desc()))
    items = result.scalars().all()
    out = []
    for p in items:
        row = {
            'id': p.provider_id,
            'name': p.name,
            'type': p.provider_type,
            'base_url': p.base_url or '',
            'is_active': p.is_active,
            'is_default': p.is_default,
            'models': p.models or [],
            'settings': p.settings or {},
        }
        if public:
            row['api_key_masked'] = mask_secret(
                _decrypt_secret(p.api_key_enc) if p.api_key_enc else ''
            ) or ('configured' if p.api_key_enc else '')
        else:
            row['api_key_enc'] = p.api_key_enc or ''
        out.append(row)
    return out


async def create_ai_provider_db(db, data: dict) -> dict:
    pid = (data.get('id') or data.get('type') or 'provider') + '-' + uuid.uuid4().hex[:6]

    if data.get('is_default'):
        from sqlalchemy import update
        await db.execute(
            update(AIProviderModel).where(AIProviderModel.is_default == True).values(is_default=False)
        )

    api_key_enc = _encrypt_secret(data['api_key']) if data.get('api_key') else None
    entry = AIProviderModel(
        provider_id=pid,
        name=data.get('name') or 'New Provider',
        provider_type=data.get('type') or 'openai',
        base_url=data.get('base_url') or '',
        api_key_enc=api_key_enc,
        is_active=data.get('is_active', True),
        is_default=data.get('is_default', False),
        models=data.get('models') or [],
        settings=data.get('settings')
        or {
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0,
        },
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    rows = await list_ai_providers_db(db, public=True)
    return rows[0] if rows else _provider_to_dict(entry, public=True)


async def update_ai_provider_db(db, provider_id: str, data: dict) -> Optional[dict]:
    from sqlalchemy import select

    result = await db.execute(
        select(AIProviderModel).where(AIProviderModel.provider_id == provider_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None

    if data.get('api_key'):
        entry.api_key_enc = _encrypt_secret(data.pop('api_key'))
    if data.get('is_default'):
        from sqlalchemy import update
        await db.execute(
            update(AIProviderModel).where(AIProviderModel.is_default == True).values(is_default=False)
        )

    for field in ('name', 'provider_type', 'base_url', 'is_active', 'is_default', 'models', 'settings'):
        if field in data:
            setattr(entry, field, data[field])

    await db.commit()
    await db.refresh(entry)
    return _provider_to_dict(entry, public=True)


async def delete_ai_provider_db(db, provider_id: str) -> bool:
    from sqlalchemy import select

    result = await db.execute(
        select(AIProviderModel).where(AIProviderModel.provider_id == provider_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return False

    await db.delete(entry)
    await db.commit()

    remaining = await db.execute(select(AIProviderModel).limit(1))
    if not remaining.scalar_one_or_none():
        return True
    has_default = await db.execute(
        select(AIProviderModel).where(AIProviderModel.is_default == True).limit(1)
    )
    if not has_default.scalar_one_or_none():
        first = (await db.execute(select(AIProviderModel).limit(1))).scalar_one()
        first.is_default = True
        await db.commit()
    return True


async def get_provider_secret_db(db, provider_id: str) -> Optional[str]:
    from sqlalchemy import select

    result = await db.execute(
        select(AIProviderModel).where(AIProviderModel.provider_id == provider_id)
    )
    entry = result.scalar_one_or_none()
    if not entry or not entry.api_key_enc:
        return None
    return _decrypt_secret(entry.api_key_enc)


def _provider_to_dict(p: AIProviderModel, public: bool = True) -> dict:
    row = {
        'id': p.provider_id,
        'name': p.name,
        'type': p.provider_type,
        'base_url': p.base_url or '',
        'is_active': p.is_active,
        'is_default': p.is_default,
        'models': p.models or [],
        'settings': p.settings or {},
    }
    if public:
        row['api_key_masked'] = mask_secret(
            _decrypt_secret(p.api_key_enc) if p.api_key_enc else ''
        ) or ('configured' if p.api_key_enc else '')
    else:
        row['api_key_enc'] = p.api_key_enc or ''
    return row


async def list_dismissed_failed_jobs_db(db) -> set[str]:
    from sqlalchemy import select

    result = await db.execute(select(DismissedFailedJobModel.job_id))
    return {row[0] for row in result.all()}


async def dismiss_failed_job_db(db, job_id: str) -> None:
    from sqlalchemy import select

    existing = await db.execute(
        select(DismissedFailedJobModel).where(DismissedFailedJobModel.job_id == job_id)
    )
    if existing.scalar_one_or_none():
        return
    db.add(DismissedFailedJobModel(job_id=job_id))
    await db.commit()
