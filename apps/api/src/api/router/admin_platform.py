"""Super Admin platform APIs — users, billing, AI providers, queue, failed jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from ...core import admin_store
from ...core.admin_store import dismiss_failed_job, list_dismissed_failed_jobs
from ...core.platform_metrics import (
    append_email_failed_jobs,
    append_email_queue_jobs,
    load_platform_failed_jobs,
    load_platform_queue_jobs,
    platform_analytics_summary,
    platform_system_health,
)
from ...core.audit_limits import (
    DEFAULT_AUDIT_LIST_LIMIT,
    MAX_AUDIT_LIST_LIMIT,
    clamp_export_limit,
)
from ...core.audit_present import audit_export_payload, audit_log_to_dict, load_users_by_id
from ...core.database import get_db
from ...core.models import (
    AIProvider,
    AuditLog,
    DismissedFailedJob,
    Membership,
    QueueJob,
    Tenant,
    User,
)
from ...core.roles import coerce_membership_role, MEMBERSHIP_ROLES
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


def _map_db_user(
    u: User,
    tenant_name: str = '—',
    membership_role: Optional[str] = None,
) -> dict:
    role = membership_role or (u.role if u.role in MEMBERSHIP_ROLES else 'member')
    return {
        'id': str(u.id),
        'name': u.name or u.email.split('@')[0],
        'email': u.email,
        'role': role,
        'membership_role': role,
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
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(500))
    db_users = result.scalars().all()
    for u in db_users:
        mem_result = await db.execute(
            select(Membership)
            .where(Membership.user_id == u.id, Membership.status == 'active')
            .order_by(Membership.joined_at.desc())
            .limit(1)
        )
        mem = mem_result.scalar_one_or_none()
        tenant_name = '—'
        mem_role: Optional[str] = None
        if mem:
            mem_role = mem.role
            t = await db.get(Tenant, mem.tenant_id)
            if t:
                tenant_name = t.name
        users.append(_map_db_user(u, tenant_name, mem_role))

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
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail='Email already exists')
    user = User(
        email=email,
        name=body.name,
        role=coerce_membership_role(body.role, default='viewer'),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _map_db_user(user, body.organization or '—')


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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid user id') from exc
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


@router.delete('/users/{user_id}', status_code=204)
async def delete_user(user_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    try:
        uid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid user id') from exc
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    await db.delete(user)
    await db.commit()
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
async def get_ai_providers(_admin: SuperAdmin, db=Depends(get_db)):
    providers = await admin_store.list_ai_providers_db(db)
    return {'providers': providers}


@router.post('/ai-providers', status_code=201)
async def add_ai_provider(body: AIProviderBody, _admin: SuperAdmin, db=Depends(get_db)):
    return await admin_store.create_ai_provider_db(db, body.model_dump())


@router.patch('/ai-providers/{provider_id}')
async def patch_ai_provider(provider_id: str, body: AIProviderPatch, _admin: SuperAdmin, db=Depends(get_db)):
    updated = await admin_store.update_ai_provider_db(db, provider_id, body.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail='Provider not found')
    return updated


@router.delete('/ai-providers/{provider_id}', status_code=204)
async def remove_ai_provider(provider_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    if provider_id == 'ollama':
        raise HTTPException(status_code=400, detail='Cannot delete default Ollama provider')
    deleted = await admin_store.delete_ai_provider_db(db, provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Provider not found')
    return None


@router.post('/ai-providers/{provider_id}/test')
async def test_ai_provider(provider_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    providers = await admin_store.list_ai_providers_db(db, public=False)
    provider = next((p for p in providers if p.get('id') == provider_id), None)
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
    jobs = await load_platform_queue_jobs(db)
    await append_email_queue_jobs(db, jobs)
    return {'jobs': jobs}


async def _resolve_queue_target(db, job_id: str):
    try:
        uid = UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid job id') from exc

    job = await db.get(QueueJob, uid)
    if job:
        return 'platform', job

    try:
        from ...core.email.db_models import EmailQueueItem

        item = await db.get(EmailQueueItem, uid)
        if item:
            return 'email', item
    except Exception:
        pass

    raise HTTPException(status_code=404, detail='Job not found')


@router.post('/queue/jobs/{job_id}/cancel')
async def cancel_queue_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    kind, row = await _resolve_queue_target(db, job_id)
    if kind == 'platform':
        if row.status in ('completed', 'cancelled'):
            raise HTTPException(status_code=400, detail='Job cannot be cancelled')
        row.status = 'cancelled'
    else:
        if row.status in ('completed', 'cancelled'):
            raise HTTPException(status_code=400, detail='Job cannot be cancelled')
        row.status = 'cancelled'
    await db.commit()
    return {'success': True, 'status': 'cancelled'}


@router.post('/queue/jobs/{job_id}/pause')
async def pause_queue_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    kind, row = await _resolve_queue_target(db, job_id)
    if kind == 'platform':
        if row.status == 'processing':
            raise HTTPException(status_code=409, detail='Cannot pause a running job')
        if row.status not in ('pending',):
            raise HTTPException(status_code=400, detail='Job is not pausable')
        row.status = 'pending'
    else:
        if row.status == 'processing':
            raise HTTPException(status_code=409, detail='Cannot pause a running job')
        if row.status not in ('pending', 'queued'):
            raise HTTPException(status_code=400, detail='Job is not pausable')
        row.status = 'pending'
    await db.commit()
    return {'success': True, 'status': 'pending'}


@router.post('/queue/jobs/{job_id}/resume')
async def resume_queue_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    kind, row = await _resolve_queue_target(db, job_id)
    if kind == 'platform':
        if row.status not in ('cancelled', 'failed'):
            raise HTTPException(status_code=400, detail='Job cannot be resumed')
        row.status = 'pending'
        row.error = None
    else:
        if row.status not in ('cancelled', 'failed', 'dead_letter'):
            raise HTTPException(status_code=400, detail='Job cannot be resumed')
        row.status = 'pending'
        row.error_message = None
    await db.commit()
    return {'success': True, 'status': 'pending'}


@router.post('/queue/jobs/{job_id}/retry')
async def retry_queue_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    try:
        uid = UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid job id') from exc

    job = await db.get(QueueJob, uid)
    if job and job.status in ('failed', 'cancelled'):
        job.status = 'pending'
        job.error = None
        job.attempts = (job.attempts or 0) + 1
        await db.commit()
        return {'success': True}

    try:
        from ...core.email.db_models import EmailQueueItem
        from ...core.tasks.inline import schedule_job

        item = await db.get(EmailQueueItem, uid)
        if item:
            item.status = 'pending'
            item.retry_count = (item.retry_count or 0) + 1
            item.error_message = None
            await db.commit()
            schedule_job('email_process', _job_id=str(item.id), queue_item_id=str(item.id))
            return {'success': True}
    except Exception:
        pass
    raise HTTPException(status_code=404, detail='Job not found or not retryable')


# --- Failed jobs ---

@router.get('/failed-jobs')
async def list_failed_jobs(_admin: SuperAdmin, db=Depends(get_db)):
    dismissed: set[str] = set()
    try:
        dismissed = await admin_store.list_dismissed_failed_jobs_db(db)
    except Exception as exc:
        logger.warning('DB dismissed jobs unavailable, using file store: %s', exc)
        dismissed = list_dismissed_failed_jobs()
    jobs = await load_platform_failed_jobs(db, dismissed)
    await append_email_failed_jobs(db, jobs, dismissed)
    return {'jobs': jobs}


@router.delete('/failed-jobs/{job_id}', status_code=204)
async def delete_failed_job(job_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    try:
        await admin_store.dismiss_failed_job_db(db, job_id)
    except Exception as exc:
        logger.warning('DB dismiss failed job, using file store: %s', exc)
        dismiss_failed_job(job_id)
    return None


@router.post('/failed-jobs/clear-dismissed')
async def clear_dismissed(_admin: SuperAdmin, db=Depends(get_db)):
    try:
        from sqlalchemy import delete
        await db.execute(delete(DismissedFailedJob))
        await db.commit()
    except Exception:
        pass
    from ...core.admin_store import _DISMISSED_FILE

    if _DISMISSED_FILE.is_file():
        _DISMISSED_FILE.unlink()
    return {'success': True}


# --- Analytics summary ---

@router.get('/analytics/summary')
async def analytics_summary(_admin: SuperAdmin, db=Depends(get_db)):
    return await platform_analytics_summary(db)


@router.get('/health')
async def platform_health(_admin: SuperAdmin, db=Depends(get_db)):
    return await platform_system_health(db)


# --- Platform audit (cross-tenant) ---

class PlatformAuditExportRequest(BaseModel):
    format: str = Field(default='json', pattern='^(json|csv)$')
    tenant_id: Optional[str] = None
    action_type: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1, le=10000)


@router.get('/audit-logs')
async def list_platform_audit_logs(
    _admin: SuperAdmin,
    db=Depends(get_db),
    limit: int = Query(DEFAULT_AUDIT_LIST_LIMIT, le=MAX_AUDIT_LIST_LIMIT),
    offset: int = Query(0, ge=0),
    tenant_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
):
    conditions = []
    if tenant_id:
        conditions.append(AuditLog.tenant_id == UUID(tenant_id))
    if action_type:
        conditions.append(AuditLog.action_type == action_type)

    count_q = select(func.count(AuditLog.id))
    list_q = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    if conditions:
        count_q = count_q.where(*conditions)
        list_q = list_q.where(*conditions)

    total = await db.scalar(count_q) or 0
    rows = (await db.execute(list_q)).scalars().all()
    user_ids = {r.user_id for r in rows if r.user_id}
    users_by_id = await load_users_by_id(db, user_ids)

    logs = [audit_log_to_dict(r, users_by_id.get(r.user_id)) for r in rows]
    return {'logs': logs, 'total': total}


@router.post('/audit-logs/export')
async def export_platform_audit_logs(
    _admin: SuperAdmin,
    body: PlatformAuditExportRequest,
    db=Depends(get_db),
):
    conditions = []
    if body.tenant_id:
        conditions.append(AuditLog.tenant_id == UUID(body.tenant_id))
    if body.action_type:
        conditions.append(AuditLog.action_type == body.action_type)

    export_limit = clamp_export_limit(body.limit)
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(export_limit)
    if conditions:
        q = q.where(*conditions)
    rows = (await db.execute(q)).scalars().all()
    user_ids = {r.user_id for r in rows if r.user_id}
    users_by_id = await load_users_by_id(db, user_ids)
    logs = [audit_log_to_dict(r, users_by_id.get(r.user_id)) for r in rows]
    return audit_export_payload(logs, body.format)
