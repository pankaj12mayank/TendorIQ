"""Super Admin platform APIs — users, billing, AI providers, queue, failed jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...core.admin_store import (
    create_ai_provider,
    create_platform_user,
    delete_ai_provider,
    dismiss_failed_job,
    list_ai_providers,
    list_dismissed_failed_jobs,
    list_platform_users,
    soft_delete_platform_user,
    update_ai_provider,
    update_platform_user,
)
from ...core.database import get_db
from ...core.models import Tenant, User
from ..dependencies.auth import SuperAdmin

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin/platform', tags=['Admin Platform'])


# --- Users ---

class PlatformUserBody(BaseModel):
    name: str
    email: str
    role: str = 'viewer'
    status: str = 'active'
    organization: Optional[str] = None


class PlatformUserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    organization: Optional[str] = None


def _map_db_user(u: User, tenant_name: str = '—') -> dict:
    return {
        'id': str(u.id),
        'name': u.name or u.email.split('@')[0],
        'email': u.email,
        'role': u.role if u.role != 'member' else 'viewer',
        'status': 'active',
        'organization': tenant_name,
        'permissions': [],
        'lastActive': (u.last_login_at or u.updated_at or datetime.now(timezone.utc)).isoformat(),
        'createdAt': (u.created_at or datetime.now(timezone.utc)).isoformat(),
    }


@router.get('/users')
async def list_users(
    _admin: SuperAdmin,
    search: Optional[str] = Query(None),
    db=Depends(get_db),
):
    users: list[dict] = []
    try:
        result = await db.execute(select(User).order_by(User.created_at.desc()).limit(500))
        db_users = result.scalars().all()
        for u in db_users:
            users.append(_map_db_user(u))
    except Exception as exc:
        logger.warning('DB users unavailable, using file store: %s', exc)
        users = [u for u in list_platform_users() if not u.get('deleted')]

    if search:
        q = search.lower()
        users = [
            u
            for u in users
            if q in u.get('name', '').lower() or q in u.get('email', '').lower()
        ]
    return {'users': users, 'total': len(users)}


@router.post('/users', status_code=201)
async def create_user(body: PlatformUserBody, _admin: SuperAdmin, db=Depends(get_db)):
    email = body.email.strip().lower()
    try:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail='Email already exists')
        user = User(
            email=email,
            name=body.name,
            role=body.role if body.role in ('owner', 'admin', 'member', 'viewer') else 'viewer',
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return _map_db_user(user, body.organization or '—')
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning('DB create user failed, file store: %s', exc)
        try:
            return create_platform_user(body.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch('/users/{user_id}')
async def patch_user(
    user_id: str,
    body: PlatformUserPatch,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    try:
        uid = UUID(user_id)
        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        for k, v in data.items():
            if k == 'role' and v in ('owner', 'admin', 'member', 'viewer', 'manager', 'analyst'):
                user.role = 'member' if v in ('manager', 'analyst') else v
            elif hasattr(user, k):
                setattr(user, k, v)
        await db.commit()
        await db.refresh(user)
        return _map_db_user(user, data.get('organization', '—'))
    except HTTPException:
        raise
    except Exception:
        updated = update_platform_user(user_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail='User not found')
        return updated


@router.delete('/users/{user_id}', status_code=204)
async def delete_user(user_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    try:
        uid = UUID(user_id)
        user = await db.get(User, uid)
        if user:
            await db.delete(user)
            await db.commit()
            return None
    except Exception:
        pass
    if not soft_delete_platform_user(user_id):
        raise HTTPException(status_code=404, detail='User not found')
    return None


# --- Billing ---

@router.get('/billing')
async def billing_overview(_admin: SuperAdmin, db=Depends(get_db)):
    plans = [
        {
            'id': 'starter',
            'name': 'Starter',
            'price': 29,
            'interval': 'monthly',
            'features': ['5 Users', '100 Documents/mo', 'Basic Analytics'],
            'limits': {'users': 5, 'documents': 100, 'apiCalls': 1000, 'storage': 1},
        },
        {
            'id': 'professional',
            'name': 'Professional',
            'price': 99,
            'interval': 'monthly',
            'features': ['20 Users', '500 Documents/mo', 'Advanced Analytics', 'Priority Support'],
            'limits': {'users': 20, 'documents': 500, 'apiCalls': 10000, 'storage': 10},
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price': 299,
            'interval': 'monthly',
            'features': ['Unlimited Users', 'Unlimited Documents', 'Custom Analytics', '24/7 Support'],
            'limits': {'users': -1, 'documents': -1, 'apiCalls': -1, 'storage': 100},
        },
    ]
    subscriptions: list[dict] = []
    invoices: list[dict] = []
    try:
        tenants = (await db.execute(select(Tenant).limit(200))).scalars().all()
        for t in tenants:
            subscriptions.append(
                {
                    'id': f'sub-{t.id}',
                    'userId': str(t.id),
                    'planId': t.plan or 'starter',
                    'status': t.subscription_status or t.status or 'active',
                    'currentPeriodStart': (t.created_at or datetime.now(timezone.utc)).isoformat(),
                    'currentPeriodEnd': datetime.now(timezone.utc).isoformat(),
                    'cancelAtPeriodEnd': False,
                    'tenantName': t.name,
                }
            )
    except Exception as exc:
        logger.warning('Billing tenant load failed: %s', exc)

    return {
        'plans': plans,
        'subscriptions': subscriptions,
        'invoices': invoices,
        'stats': {
            'active_subscriptions': len([s for s in subscriptions if s['status'] == 'active']),
            'mrr_estimate': sum(
                next((p['price'] for p in plans if p['id'] == s['planId']), 0)
                for s in subscriptions
                if s['status'] == 'active'
            ),
        },
    }


# --- AI providers ---

class AIProviderBody(BaseModel):
    name: str
    type: str = 'ollama'
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    models: list[dict] = Field(default_factory=list)
    settings: Optional[dict] = None


class AIProviderPatch(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    models: Optional[list[dict]] = None
    settings: Optional[dict] = None


@router.get('/ai-providers')
async def get_ai_providers(_admin: SuperAdmin):
    return {'providers': list_ai_providers()}


@router.post('/ai-providers', status_code=201)
async def add_ai_provider(body: AIProviderBody, _admin: SuperAdmin):
    return create_ai_provider(body.model_dump())


@router.patch('/ai-providers/{provider_id}')
async def patch_ai_provider(provider_id: str, body: AIProviderPatch, _admin: SuperAdmin):
    updated = update_ai_provider(provider_id, body.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail='Provider not found')
    return updated


@router.delete('/ai-providers/{provider_id}', status_code=204)
async def remove_ai_provider(provider_id: str, _admin: SuperAdmin):
    if provider_id == 'ollama':
        raise HTTPException(status_code=400, detail='Cannot delete default Ollama provider')
    if not delete_ai_provider(provider_id):
        raise HTTPException(status_code=404, detail='Provider not found')
    return None


@router.post('/ai-providers/{provider_id}/test')
async def test_ai_provider(provider_id: str, _admin: SuperAdmin):
    from ...core.admin_store import _find_provider

    provider = _find_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail='Provider not found')

    ptype = provider.get('type', 'ollama')
    try:
        if ptype == 'ollama':
            base = provider.get('base_url') or 'http://localhost:11434'
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f'{base.rstrip("/")}/api/tags')
                r.raise_for_status()
            return {'success': True, 'message': 'Ollama is reachable'}
        return {'success': True, 'message': f'{provider.get("name")} configuration saved'}
    except Exception as exc:
        return {'success': False, 'message': str(exc)}


# --- Queue (observability + email) ---

@router.get('/queue/jobs')
async def list_queue_jobs(_admin: SuperAdmin, db=Depends(get_db)):
    from .observability import MOCK_QUEUE_METRICS

    jobs: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for m in MOCK_QUEUE_METRICS:
        for i in range(min(m['pending'], 5)):
            jobs.append(
                {
                    'id': f'{m["queue_name"]}-pending-{i}',
                    'name': f'{m["queue_name"].title()} job',
                    'status': 'pending',
                    'progress': 0,
                    'priority': 'normal',
                    'queue': m['queue_name'],
                    'attempts': 0,
                    'maxAttempts': 3,
                    'createdAt': now,
                    'payload': {},
                }
            )
        if m['active']:
            jobs.append(
                {
                    'id': f'{m["queue_name"]}-active-0',
                    'name': f'{m["queue_name"].title()} processing',
                    'status': 'processing',
                    'progress': 50,
                    'priority': 'high',
                    'queue': m['queue_name'],
                    'worker': 'worker-1',
                    'attempts': 1,
                    'maxAttempts': 3,
                    'createdAt': now,
                    'startedAt': now,
                    'payload': {},
                }
            )

    try:
        from ...core.email.db_models import EmailQueueItem

        result = await db.execute(
            select(EmailQueueItem).order_by(EmailQueueItem.created_at.desc()).limit(50)
        )
        for item in result.scalars().all():
            jobs.append(
                {
                    'id': str(item.id),
                    'name': f'Email: {item.event_key or "notification"}',
                    'status': item.status,
                    'progress': 100 if item.status == 'completed' else 0,
                    'priority': 'normal',
                    'queue': 'email',
                    'attempts': item.retry_count or 0,
                    'maxAttempts': item.max_retries or 5,
                    'createdAt': (item.created_at or datetime.now(timezone.utc)).isoformat(),
                    'error': item.last_error,
                    'payload': {'recipient': item.recipient_email},
                }
            )
    except Exception as exc:
        logger.debug('Email queue load skipped: %s', exc)

    return {'jobs': jobs}


@router.post('/queue/jobs/{job_id}/retry')
async def retry_queue_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    try:
        from ...core.email.db_models import EmailQueueItem
        from ...core.tasks.inline import schedule_job

        item = await db.get(EmailQueueItem, UUID(job_id))
        if item:
            item.status = 'pending'
            item.retry_count = (item.retry_count or 0) + 1
            await db.commit()
            schedule_job('email_process', _job_id=str(item.id), queue_item_id=str(item.id))
            return {'success': True}
    except Exception:
        pass
    return {'success': True, 'message': 'Retry scheduled (synthetic job)'}


# --- Failed jobs ---

@router.get('/failed-jobs')
async def list_failed_jobs(_admin: SuperAdmin, db=Depends(get_db)):
    from .observability import MOCK_FAILURES

    dismissed = list_dismissed_failed_jobs()
    jobs = [
        {
            'id': f['id'],
            'jobName': f.get('type', 'Job').replace('_', ' ').title(),
            'queue': f.get('queue', 'unknown'),
            'failedAt': f.get('occurred_at'),
            'error': f.get('message'),
            'attemptCount': f.get('retry_count', 0),
            'lastAttemptAt': f.get('occurred_at'),
            'retryable': True,
            'payload': {},
        }
        for f in MOCK_FAILURES
        if f['id'] not in dismissed
    ]

    try:
        from ...core.email.db_models import EmailQueueItem

        result = await db.execute(
            select(EmailQueueItem).where(EmailQueueItem.status.in_(('failed', 'dead_letter'))).limit(100)
        )
        for item in result.scalars().all():
            jid = str(item.id)
            if jid in dismissed:
                continue
            jobs.append(
                {
                    'id': jid,
                    'jobName': f'Email: {item.event_key}',
                    'queue': 'email',
                    'failedAt': (item.updated_at or item.created_at).isoformat(),
                    'error': item.last_error or 'Delivery failed',
                    'attemptCount': item.retry_count or 0,
                    'lastAttemptAt': (item.updated_at or item.created_at).isoformat(),
                    'retryable': item.status != 'dead_letter',
                    'payload': {'recipient': item.recipient_email},
                }
            )
    except Exception as exc:
        logger.debug('Email failed jobs skipped: %s', exc)

    return {'jobs': jobs}


@router.delete('/failed-jobs/{job_id}', status_code=204)
async def delete_failed_job(job_id: str, _admin: SuperAdmin):
    dismiss_failed_job(job_id)
    return None


@router.post('/failed-jobs/clear-dismissed')
async def clear_dismissed(_admin: SuperAdmin):
    from ...core.admin_store import _DISMISSED_FILE

    if _DISMISSED_FILE.is_file():
        _DISMISSED_FILE.unlink()
    return {'success': True}


# --- Analytics summary ---

@router.get('/analytics/summary')
async def analytics_summary(_admin: SuperAdmin, db=Depends(get_db)):
    from .observability import MOCK_AI_METRICS, MOCK_API_METRICS, MOCK_QUEUE_METRICS

    user_count = 0
    try:
        user_count = await db.scalar(select(func.count()).select_from(User)) or 0
    except Exception:
        user_count = len([u for u in list_platform_users() if not u.get('deleted')])

    total_api = sum(m['requests'] for m in MOCK_API_METRICS.values())
    total_cost = sum(m['cost'] for m in MOCK_AI_METRICS)
    active_jobs = sum(m['active'] for m in MOCK_QUEUE_METRICS)
    failed = sum(m['failed'] for m in MOCK_QUEUE_METRICS)
    completed = sum(m['completed'] for m in MOCK_QUEUE_METRICS)
    failure_rate = failed / max(completed + failed, 1)

    return {
        'totalUsers': user_count,
        'apiCallsToday': total_api,
        'activeJobs': active_jobs,
        'errorRate': round(failure_rate * 100, 1),
        'monthlyCost': round(total_cost, 2),
        'usage': [],
    }
