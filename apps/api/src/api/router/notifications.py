"""Notifications API — CRUD backed by Notification model."""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Notification
from ...core.database import get_db
from ..dependencies.auth import get_current_user
from ...core.auth import AuthContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/notifications', tags=['Notifications'])


def _notif_to_dict(n: Notification) -> dict:
    return {
        'id': str(n.id),
        'tenant_id': str(n.tenant_id),
        'user_id': str(n.user_id),
        'tender_id': str(n.tender_id) if n.tender_id else None,
        'type': n.type,
        'title': n.title,
        'message': n.message,
        'data': n.data,
        'is_read': n.is_read,
        'read_at': n.read_at.isoformat() if n.read_at else None,
        'created_at': n.created_at.isoformat() if n.created_at else None,
    }


@router.get('/')
async def list_notifications(
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id
    try:
        conditions = [
            Notification.tenant_id == UUID(tenant_id),
            Notification.user_id == UUID(user_id),
            Notification.deleted_at.is_(None),
        ]
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)

        total_q = select(func.count(Notification.id)).where(*conditions)
        total = await db.scalar(total_q) or 0

        q = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return {'success': True, 'data': [_notif_to_dict(r) for r in rows], 'total': total, 'page': page, 'limit': limit}
    except Exception as e:
        logger.exception('Failed to list notifications')
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/{notification_id}/read')
async def mark_as_read(
    notification_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id
    try:
        q = select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == UUID(tenant_id),
            Notification.user_id == UUID(user_id),
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Notification not found')
        row.is_read = True
        row.read_at = datetime.utcnow()
        await db.commit()
        await db.refresh(row)
        return {'success': True, 'data': _notif_to_dict(row)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to mark notification as read')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/read-all')
async def mark_all_as_read(
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id
    try:
        stmt = (
            update(Notification)
            .where(
                Notification.tenant_id == UUID(tenant_id),
                Notification.user_id == UUID(user_id),
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = await db.execute(stmt)
        await db.commit()
        return {'success': True, 'updated': result.rowcount}
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to mark all as read')
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{notification_id}')
async def delete_notification(
    notification_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id
    try:
        q = select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == UUID(tenant_id),
            Notification.user_id == UUID(user_id),
            Notification.deleted_at.is_(None),
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Notification not found')
        row.deleted_at = datetime.utcnow()
        await db.commit()
        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception('Failed to delete notification')
        raise HTTPException(status_code=500, detail=str(e))
