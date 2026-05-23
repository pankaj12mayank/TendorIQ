"""Base Repository Pattern"""

from typing import Any, Generic, TypeVar, Optional
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.logging import get_logger
from .soft_delete import apply_active_only, mark_soft_deleted, model_has_soft_delete

logger = get_logger(__name__)

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        query = apply_active_only(select(self.model).where(self.model.id == id), self.model)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ModelType]:
        query = apply_active_only(select(self.model), self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: Any, obj_in: dict[str, Any]) -> Optional[ModelType]:
        db_obj = await self.get(id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            await self.db.flush()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> bool:
        query = select(self.model).where(self.model.id == id)
        if model_has_soft_delete(self.model):
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(query)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        if model_has_soft_delete(self.model):
            mark_soft_deleted(db_obj)
        else:
            await self.db.delete(db_obj)
        await self.db.flush()
        return True

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        query = apply_active_only(select(func.count()).select_from(self.model), self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists(self, id: Any) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return result.scalar_one() > 0

    async def get_all_in_tenant(
        self,
        tenant_id: Any,
        skip: int = 0,
        limit: int = 100,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> list[ModelType]:
        """Get all records filtered by tenant_id, with optional extra filters"""
        query = apply_active_only(
            select(self.model).where(self.model.tenant_id == tenant_id),
            self.model,
        )

        if extra_filters:
            for key, value in extra_filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_in_tenant(
        self,
        tenant_id: Any,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> int:
        """Count records filtered by tenant_id"""
        query = apply_active_only(
            select(func.count()).select_from(self.model).where(self.model.tenant_id == tenant_id),
            self.model,
        )

        if extra_filters:
            for key, value in extra_filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()
