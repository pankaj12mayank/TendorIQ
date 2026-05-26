"""API Router and Endpoints"""

from fastapi import APIRouter

from .base import router as base_router
from .routers.tenders import router as tenders_router

router = APIRouter()
router.include_router(base_router)
router.include_router(tenders_router)


__all__ = ['router']