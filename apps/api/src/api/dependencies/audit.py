"""Audit-Safe Access - Audit Logging and Safe Operations"""

from typing import Optional, Any, Callable
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import AuditLog, User, Tenant
from ..core.logging import get_logger

logger = get_logger('audit_safe')


class AuditLogger:
    """Audit logging for tenant operations"""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        action: str,
        action_type: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        resource_name: Optional[str] = None,
        changes: Optional[dict] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log an audit action"""
        ip_address = None
        user_agent = None
        request_id = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get('User-Agent')
            request_id = getattr(request.state, 'request_id', None)

        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes or {},
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.info(
            f'Audit: {action} on {resource_type}',
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            resource_id=str(resource_id) if resource_id else None,
        )

        return audit_log


class SafeAccess:
    """Safe access helpers for tenant operations"""

    @staticmethod
    async def check_tenant_resource(
        db: AsyncSession,
        resource: Any,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if resource belongs to tenant"""
        if hasattr(resource, 'tenant_id'):
            return str(resource.tenant_id) == str(tenant_id)
        return False

    @staticmethod
    async def require_tenant_resource(
        db: AsyncSession,
        resource: Any,
        tenant_id: UUID,
        user_id: UUID,
        action: str,
        request: Optional[Request] = None,
    ) -> bool:
        """Require resource belongs to tenant, raise if not"""
        if not await SafeAccess.check_tenant_resource(db, resource, tenant_id, user_id):
            await AuditLogger.log_action(
                db,
                tenant_id,
                user_id,
                action=action,
                resource_type=resource.__class__.__name__,
                changes={'error': 'Access denied - resource not in tenant'},
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Resource does not belong to your organization',
            )
        return True


class TenantAuditMixin:
    """Mixin to add audit logging to services"""

    @staticmethod
    async def log_create(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action_type: str = 'document',
        resource_name: Optional[str] = None,
        values: dict = None,
        request: Optional[Request] = None,
    ):
        await AuditLogger.log_action(
            db,
            tenant_id,
            user_id,
            action='create',
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            new_values=values,
            request=request,
        )

    @staticmethod
    async def log_update(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action_type: str = 'document',
        resource_name: Optional[str] = None,
        old_values: dict = None,
        new_values: dict = None,
        request: Optional[Request] = None,
    ):
        old_values = old_values or {}
        new_values = new_values or {}
        changes = {
            k: {'old': old_values.get(k), 'new': new_values.get(k)}
            for k in set(old_values.keys()) | set(new_values.keys())
            if old_values.get(k) != new_values.get(k)
        }

        await AuditLogger.log_action(
            db,
            tenant_id,
            user_id,
            action='update',
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            old_values=old_values,
            new_values=new_values,
            request=request,
        )

    @staticmethod
    async def log_delete(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action_type: str = 'delete',
        resource_name: Optional[str] = None,
        old_values: dict = None,
        request: Optional[Request] = None,
    ):
        await AuditLogger.log_action(
            db,
            tenant_id,
            user_id,
            action='delete',
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values,
            request=request,
        )

    @staticmethod
    async def log_access(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        action_type: str = 'document',
        request: Optional[Request] = None,
    ):
        await AuditLogger.log_action(
            db,
            tenant_id,
            user_id,
            action='access',
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
        )


audit_logger = AuditLogger()
safe_access = SafeAccess()
tenant_audit = TenantAuditMixin()