"""Platform owner operational dashboard (Layer 4) — real backend state only."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from ...core.dashboard.pipeline_stages import derive_pipeline_stages
from ...core.database import get_db
from ...core.models import (
    AnalysisResult,
    Document,
    Membership,
    PaymentTransaction,
    Proposal,
    Tenant,
    Tender,
    User,
)
from ...core.user_preferences import normalize_preferences
from ..dependencies.auth import SuperAdmin

router = APIRouter(prefix='/admin/platform/dashboard', tags=['Admin Dashboard'])


def _is_platform_owner(user: User) -> bool:
    return bool(normalize_preferences(user.preferences).get('platform_super_admin'))


def _is_platform_owner_preferences(preferences: Any) -> bool:
    return bool(normalize_preferences(preferences).get('platform_super_admin'))


def _start_of_utc_day() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def _document_pipeline_row(db, doc: Document) -> dict[str, Any]:
    meta = doc.metadata_json if isinstance(doc.metadata_json, dict) else {}
    analysis_meta = meta.get('analysis') if isinstance(meta.get('analysis'), dict) else None

    has_analysis = (
        await db.scalar(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.document_id == doc.id)
        )
        or 0
    ) > 0

    has_proposal = False
    if doc.tender_id:
        has_proposal = (
            await db.scalar(
                select(func.count(Proposal.id)).where(Proposal.tender_id == doc.tender_id)
            )
            or 0
        ) > 0

    pipeline = derive_pipeline_stages(
        doc.processing_status or 'uploaded',
        analysis_meta=analysis_meta,
        has_analysis_result=has_analysis,
        has_proposal=has_proposal,
        retry_count=int(doc.retry_count or 0),
        processing_error=doc.processing_error,
    )

    owner_email = '—'
    owner_name = '—'
    if doc.owner_id:
        owner = await db.get(User, doc.owner_id)
        if owner:
            owner_email = owner.email
            owner_name = owner.name or owner.email.split('@')[0]

    tender_title = None
    if doc.tender_id:
        tender = await db.get(Tender, doc.tender_id)
        if tender and tender.deleted_at is None:
            tender_title = tender.title

    return {
        'document_id': str(doc.id),
        'document_name': doc.name or doc.file_name,
        'tender_id': str(doc.tender_id) if doc.tender_id else None,
        'tender_title': tender_title,
        'owner_email': owner_email,
        'owner_name': owner_name,
        'processing_status': doc.processing_status,
        'updated_at': (doc.updated_at or doc.created_at or datetime.now(timezone.utc)).isoformat(),
        'pipeline': pipeline,
    }


async def _build_pipeline_rows(db, docs: list[Document]) -> list[dict[str, Any]]:
    if not docs:
        return []
    doc_ids = [d.id for d in docs]
    owner_ids = list({d.owner_id for d in docs if d.owner_id})
    tender_ids = list({d.tender_id for d in docs if d.tender_id})

    analysis_doc_ids = set(
        (
            await db.execute(
                select(AnalysisResult.document_id)
                .where(AnalysisResult.document_id.in_(doc_ids))
                .group_by(AnalysisResult.document_id)
            )
        )
        .scalars()
        .all()
    )
    proposal_tender_ids = set()
    if tender_ids:
        proposal_tender_ids = set(
            (
                await db.execute(
                    select(Proposal.tender_id)
                    .where(Proposal.tender_id.in_(tender_ids))
                    .group_by(Proposal.tender_id)
                )
            )
            .scalars()
            .all()
        )

    owner_map: dict[Any, User] = {}
    if owner_ids:
        owner_rows = (await db.execute(select(User).where(User.id.in_(owner_ids)))).scalars().all()
        owner_map = {u.id: u for u in owner_rows}

    tender_map: dict[Any, Tender] = {}
    if tender_ids:
        tender_rows = (
            await db.execute(
                select(Tender).where(
                    Tender.id.in_(tender_ids),
                    Tender.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        tender_map = {t.id: t for t in tender_rows}

    rows: list[dict[str, Any]] = []
    for doc in docs:
        meta = doc.metadata_json if isinstance(doc.metadata_json, dict) else {}
        analysis_meta = meta.get('analysis') if isinstance(meta.get('analysis'), dict) else None
        has_analysis = doc.id in analysis_doc_ids
        has_proposal = bool(doc.tender_id and doc.tender_id in proposal_tender_ids)
        pipeline = derive_pipeline_stages(
            doc.processing_status or 'uploaded',
            analysis_meta=analysis_meta,
            has_analysis_result=has_analysis,
            has_proposal=has_proposal,
            retry_count=int(doc.retry_count or 0),
            processing_error=doc.processing_error,
        )
        owner = owner_map.get(doc.owner_id) if doc.owner_id else None
        tender = tender_map.get(doc.tender_id) if doc.tender_id else None
        rows.append(
            {
                'document_id': str(doc.id),
                'document_name': doc.name or doc.file_name,
                'tender_id': str(doc.tender_id) if doc.tender_id else None,
                'tender_title': tender.title if tender else None,
                'owner_email': owner.email if owner else '—',
                'owner_name': (owner.name or owner.email.split('@')[0]) if owner else '—',
                'processing_status': doc.processing_status,
                'updated_at': (doc.updated_at or doc.created_at or datetime.now(timezone.utc)).isoformat(),
                'pipeline': pipeline,
            }
        )
    return rows


@router.get('/overview')
async def dashboard_overview(_admin: SuperAdmin, db=Depends(get_db)):
    """Uploads today, active users, revenue, failed jobs, recent payments."""
    day_start = _start_of_utc_day()

    uploads_today = await db.scalar(
        select(func.count(Document.id)).where(
            Document.deleted_at.is_(None),
            Document.created_at >= day_start,
        )
    ) or 0

    failed_ai_jobs = await db.scalar(
        select(func.count(Document.id)).where(
            Document.deleted_at.is_(None),
            Document.processing_status == 'failed',
        )
    ) or 0

    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.status == 'paid'
        )
    ) or 0

    all_users = (await db.execute(select(User.id, User.last_login_at, User.preferences))).all()
    active_users = 0
    inactive_users = 0
    for _, last_login_at, preferences in all_users:
        if _is_platform_owner_preferences(preferences):
            continue
        if last_login_at:
            active_users += 1
        else:
            inactive_users += 1

    recent_payments_rows = (
        (
            await db.execute(
                select(PaymentTransaction)
                .order_by(PaymentTransaction.created_at.desc())
                .limit(8)
            )
        )
        .scalars()
        .all()
    )
    payment_user_ids = list({p.user_id for p in recent_payments_rows if p.user_id})
    payment_users: dict[Any, str] = {}
    if payment_user_ids:
        payment_users = {
            uid: email
            for uid, email in (
                await db.execute(select(User.id, User.email).where(User.id.in_(payment_user_ids)))
            ).all()
        }
    recent_payments = []
    for p in recent_payments_rows:
        user_email = payment_users.get(p.user_id, '—')
        recent_payments.append(
            {
                'id': str(p.id),
                'provider': p.provider,
                'amount': float(p.amount or 0),
                'currency': p.currency or 'INR',
                'plan': p.plan,
                'status': p.status,
                'user_email': user_email,
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }
        )

    return {
        'success': True,
        'data': {
            'uploads_today': int(uploads_today),
            'active_users': active_users,
            'inactive_users': inactive_users,
            'revenue': float(total_revenue),
            'failed_ai_jobs': int(failed_ai_jobs),
            'recent_payments': recent_payments,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get('/pipeline')
async def dashboard_pipeline(
    _admin: SuperAdmin,
    limit: int = Query(12, ge=1, le=50),
    page: int = Query(1, ge=1),
    db=Depends(get_db),
):
    """Live AI jobs from document processing_status and metadata (no synthetic progress)."""
    active_statuses = ('uploaded', 'processing', 'retrying', 'needs_review')
    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

    active_docs = (
        (
            await db.execute(
                select(Document)
                .where(
                    Document.deleted_at.is_(None),
                    Document.processing_status.in_(active_statuses),
                )
                .order_by(Document.updated_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    terminal_docs = (
        (
            await db.execute(
                select(Document)
                .where(
                    Document.deleted_at.is_(None),
                    Document.processing_status.in_(('completed', 'failed')),
                    Document.updated_at >= recent_cutoff,
                )
                .order_by(Document.updated_at.desc())
                .limit(max(5, limit // 2))
            )
        )
        .scalars()
        .all()
    )

    seen: set[str] = set()
    merged_docs: list[Document] = []
    for doc in list(active_docs) + list(terminal_docs):
        did = str(doc.id)
        if did in seen:
            continue
        seen.add(did)
        merged_docs.append(doc)

    jobs = await _build_pipeline_rows(db, merged_docs)
    jobs.sort(key=lambda j: j.get('updated_at') or '', reverse=True)
    total = len(jobs)
    start = (page - 1) * limit
    page_jobs = jobs[start : start + limit]

    has_active = any(
        j.get('pipeline', {}).get('is_terminal') is False
        for j in jobs
    )

    return {
        'success': True,
        'data': {
            'jobs': page_jobs,
            'has_active': has_active,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        },
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit if total else 0,
        },
    }


@router.get('/tenders')
async def dashboard_tenders(
    _admin: SuperAdmin,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db=Depends(get_db),
):
    q = select(Tender).where(Tender.deleted_at.is_(None))
    if status:
        q = q.where(Tender.status == status.lower())
    if user_id:
        q = q.where(Tender.owner_id == user_id)
    if search:
        term = f'%{search.strip().lower()}%'
        q = q.where(func.lower(Tender.title).like(term))

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = (
        (
            await db.execute(
                q.order_by(Tender.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    owner_ids = list({t.owner_id for t in rows if t.owner_id})
    owner_emails: dict[Any, str] = {}
    if owner_ids:
        owner_emails = {
            uid: email
            for uid, email in (
                await db.execute(select(User.id, User.email).where(User.id.in_(owner_ids)))
            ).all()
        }

    items: list[dict[str, Any]] = []
    for t in rows:
        owner_email = owner_emails.get(t.owner_id, '—')
        items.append(
            {
                'id': str(t.id),
                'title': t.title,
                'status': t.status,
                'owner_id': str(t.owner_id) if t.owner_id else None,
                'owner_email': owner_email,
                'budget': t.budget,
                'currency': t.currency,
                'created_at': (t.created_at or datetime.now(timezone.utc)).isoformat(),
            }
        )

    return {
        'success': True,
        'data': items,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': int(total),
            'pages': (int(total) + limit - 1) // limit if total else 0,
        },
    }


@router.delete('/tenders/{tender_id}')
async def dashboard_delete_tender(
    tender_id: str,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    tender = await db.get(Tender, tender_id)
    if not tender or tender.deleted_at is not None:
        raise HTTPException(status_code=404, detail='Tender not found')
    tender.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {'success': True, 'data': {'tender_id': tender_id, 'deleted': True}}


@router.get('/users')
async def dashboard_registered_users(
    _admin: SuperAdmin,
    status: Optional[str] = Query(None, pattern=r'^(active|inactive)$'),
    plan: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
):
    """Registered users with plans and usage; platform owner accounts excluded."""
    subq = (
        select(
            Membership.user_id.label('user_id'),
            func.max(Membership.joined_at).label('joined_at'),
        )
        .where(Membership.status == 'active')
        .group_by(Membership.user_id)
        .subquery()
    )
    q = (
        select(User, Membership, Tenant)
        .outerjoin(subq, subq.c.user_id == User.id)
        .outerjoin(
            Membership,
            (Membership.user_id == User.id)
            & (Membership.joined_at == subq.c.joined_at),
        )
        .outerjoin(Tenant, Tenant.id == Membership.tenant_id)
    )
    if search:
        term = f'%{search.strip().lower()}%'
        q = q.where(
            func.lower(User.email).like(term)
            | func.lower(func.coalesce(User.name, '')).like(term)
        )
    if status == 'inactive':
        q = q.where(User.last_login_at.is_(None))
    elif status == 'active':
        q = q.where(User.last_login_at.is_not(None))
    if plan:
        q = q.where(Tenant.plan == plan.lower())

    rows = (
        (
            await db.execute(
                q.order_by(User.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .all()
    )

    filtered: list[tuple[User, Optional[Membership], Optional[Tenant]]] = []
    by_plan: dict[str, int] = {}
    active_count = 0
    inactive_count = 0

    for u, mem, tenant in rows:
        if _is_platform_owner(u):
            continue
        user_status = 'active' if u.last_login_at else 'inactive'
        if user_status == 'active':
            active_count += 1
        else:
            inactive_count += 1
        plan_name = (tenant.plan if tenant else 'free') or 'free'
        by_plan[plan_name] = by_plan.get(plan_name, 0) + 1
        filtered.append((u, mem, tenant))

    owner_all_rows = (
        (
            await db.execute(
                q.order_by(User.created_at.desc())
            )
        )
        .all()
    )
    total = sum(1 for u, _, _ in owner_all_rows if not _is_platform_owner(u))
    page_rows = filtered

    page_user_ids = [u.id for u, _, _ in page_rows]
    uploads_by_user = {}
    analysis_by_user = {}
    proposals_by_user = {}
    if page_user_ids:
        uploads_by_user = {
            uid: int(count)
            for uid, count in (
                await db.execute(
                    select(Document.owner_id, func.count(Document.id))
                    .where(
                        Document.owner_id.in_(page_user_ids),
                        Document.deleted_at.is_(None),
                    )
                    .group_by(Document.owner_id)
                )
            ).all()
        }
        analysis_by_user = {
            uid: int(count)
            for uid, count in (
                await db.execute(
                    select(AnalysisResult.owner_id, func.count(AnalysisResult.id))
                    .where(AnalysisResult.owner_id.in_(page_user_ids))
                    .group_by(AnalysisResult.owner_id)
                )
            ).all()
        }
        proposals_by_user = {
            uid: int(count)
            for uid, count in (
                await db.execute(
                    select(Proposal.owner_id, func.count(Proposal.id))
                    .where(Proposal.owner_id.in_(page_user_ids))
                    .group_by(Proposal.owner_id)
                )
            ).all()
        }

    users_out: list[dict[str, Any]] = []
    for u, mem, tenant in page_rows:
        upload_count = uploads_by_user.get(u.id, 0)
        analysis_count = analysis_by_user.get(u.id, 0)
        proposal_count = proposals_by_user.get(u.id, 0)
        users_out.append(
            {
                'id': str(u.id),
                'name': u.name or u.email.split('@')[0],
                'email': u.email,
                'status': 'active' if u.last_login_at else 'inactive',
                'plan': (tenant.plan if tenant else 'free') or 'free',
                'role': mem.role if mem else 'member',
                'organization': tenant.name if tenant else '—',
                'last_active': (u.last_login_at or u.updated_at).isoformat()
                if (u.last_login_at or u.updated_at)
                else None,
                'usage': {
                    'uploads': int(upload_count),
                    'analysis': int(analysis_count),
                    'proposals': int(proposal_count),
                },
            }
        )

    return {
        'success': True,
        'data': {
            'summary': {
                'active_users': active_count,
                'inactive_users': inactive_count,
                'by_plan': by_plan,
            },
            'users': users_out,
        },
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit if total else 0,
        },
    }


@router.get('/user-options')
async def dashboard_user_filter_options(
    _admin: SuperAdmin,
    q: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
):
    """Searchable owner emails for tender filter (excludes platform owner)."""
    stmt = select(User).order_by(User.email.asc()).limit(limit)
    if q:
        term = f'%{q.strip().lower()}%'
        stmt = stmt.where(
            func.lower(User.email).like(term)
            | func.lower(func.coalesce(User.name, '')).like(term)
        )
    rows = (await db.execute(stmt)).scalars().all()
    options = [
        {'id': str(u.id), 'email': u.email, 'name': u.name or u.email.split('@')[0]}
        for u in rows
        if not _is_platform_owner(u)
    ]
    return {'success': True, 'data': options}
