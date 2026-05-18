"""Base Pydantic Schemas"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')


class ResponseBase(BaseModel):
    success: bool = True
    error: Optional[dict[str, Any]] = None


class DataResponse(ResponseBase, Generic[T]):
    data: Optional[T] = None


class PaginatedResponse(ResponseBase):
    data: list[Any] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class PaginationMeta(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)


class TimestampMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IDMixin(BaseModel):
    id: str = Field(validation_alias='id')


def create_response(data: Any, meta: Optional[PaginationMeta] = None) -> dict[str, Any]:
    response = {'success': True, 'data': data}

    if meta:
        response['meta'] = {
            'page': meta.page,
            'limit': meta.limit,
            'total': meta.total,
            'total_pages': meta.total_pages,
        }

    return response


def create_error_response(code: str, message: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details,
        },
    }