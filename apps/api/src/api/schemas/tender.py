"""Tender Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TenderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    status: str = Field(default='draft')
    budget: Optional[float] = Field(None, ge=0)
    currency: str = Field(default='USD', pattern=r'^[A-Z]{3}$')
    closing_date: Optional[datetime] = None


class TenderCreate(TenderBase):
    """Tenant is taken from JWT; organization_id is optional legacy alias."""

    organization_id: Optional[str] = None


class TenderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    closing_date: Optional[datetime] = None


class TenderResponse(TenderBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_by_id: str
    created_at: datetime
    updated_at: datetime


class TenderListResponse(BaseModel):
    items: list[TenderResponse]
    total: int
    page: int
    limit: int
    pages: int