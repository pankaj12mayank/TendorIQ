"""Base Service Layer"""

from typing import Any, Generic, TypeVar, Optional
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class BaseService(Generic[ModelType]):
    """Base service with common business logic"""

    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, id: str) -> Optional[ModelType]:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.get(id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ModelType]:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.get_all(skip=skip, limit=limit, filters=filters)

    async def create(self, data: dict[str, Any]) -> ModelType:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.create(data)

    async def update(self, id: str, data: dict[str, Any]) -> Optional[ModelType]:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.update(id, data)

    async def delete(self, id: str) -> bool:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.delete(id)

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        from ..repositories.base import BaseRepository
        repo = BaseRepository(self.model, self.db)
        return await repo.count(filters)