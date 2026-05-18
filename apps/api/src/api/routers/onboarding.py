"""Onboarding API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .dependencies.auth import CurrentUser
from .services.onboarding_service import onboarding_service
from .services.tenant_service import tenant_service
from .schemas.onboarding import (
    Step1OrganizationCreate,
    Step2ProfileSetup,
    Step3ExpertiseSetup,
    Step4PlanSelection,
    Step5DashboardSetup,
    OnboardingStateResponse,
    Step1Response,
    Step2Response,
    Step3Response,
    Step4Response,
    Step5Response,
    ExpertiseCategoryResponse,
    AVAILABLE_PLANS,
)
from ..core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/onboarding', tags=['onboarding'])


def _state_to_response(state) -> OnboardingStateResponse:
    return OnboardingStateResponse(
        id=str(state.id),
        user_id=str(state.user_id),
        tenant_id=str(state.tenant_id) if state.tenant_id else None,
        current_step=state.current_step,
        total_steps=state.total_steps,
        step_1_completed=state.step_1_completed,
        step_2_completed=state.step_2_completed,
        step_3_completed=state.step_3_completed,
        step_4_completed=state.step_4_completed,
        step_5_completed=state.step_5_completed,
        step_1_data=state.step_1_data or {},
        step_2_data=state.step_2_data or {},
        step_3_data=state.step_3_data or {},
        step_4_data=state.step_4_data or {},
        step_5_data=state.step_5_data or {},
        is_completed=state.is_completed,
        completed_at=state.completed_at,
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


class PlansResponse(BaseModel):
    plans: list


class ExpertiseCategoriesResponse(BaseModel):
    expertise_areas: list[str]
    industries: list[str]
    company_sizes: list[str]
    annual_tender_volumes: list[str]
    average_contract_values: list[str]
    target_regions: list[dict]
    certifications: list[str]


EXPERTISE_AREAS = [
    'Construction & Infrastructure',
    'Information Technology',
    'Healthcare & Medical',
    'Education & Training',
    'Transportation & Logistics',
    'Energy & Utilities',
    'Manufacturing & Industrial',
    'Professional Services',
    'Security & Defense',
    'Environmental Services',
    'Agriculture & Food',
    'Finance & Banking',
    'Communications',
    'Real Estate',
    'Other',
]

INDUSTRIES = [
    'Government',
    'Private',
    'Non-Profit',
    'Healthcare',
    'Education',
    'Technology',
    'Manufacturing',
    'Construction',
    'Finance',
    'Retail',
    'Transportation',
    'Energy',
    'Media',
    'Telecommunications',
    'Other',
]

COMPANY_SIZES = [
    '1-10 employees',
    '11-50 employees',
    '51-200 employees',
    '201-500 employees',
    '501-1000 employees',
    '1001-5000 employees',
    '5000+ employees',
]

TENDER_VOLUMES = [
    '1-10 per year',
    '11-25 per year',
    '26-50 per year',
    '51-100 per year',
    '100+ per year',
]

CONTRACT_VALUES = [
    'Under $10,000',
    '$10,000 - $50,000',
    '$50,000 - $100,000',
    '$100,000 - $500,000',
    '$500,000 - $1,000,000',
    'Over $1,000,000',
]

TARGET_REGIONS = [
    {'id': 'north_america', 'name': 'North America'},
    {'id': 'europe', 'name': 'Europe'},
    {'id': 'asia_pacific', 'name': 'Asia Pacific'},
    {'id': 'middle_east', 'name': 'Middle East'},
    {'id': 'africa', 'name': 'Africa'},
    {'id': 'south_america', 'name': 'South America'},
    {'id': 'global', 'name': 'Global'},
]

CERTIFICATIONS = [
    'ISO 9001 (Quality Management)',
    'ISO 14001 (Environmental)',
    'ISO 27001 (Information Security)',
    'ISO 45001 (Occupational Health)',
    'SOC 2',
    'CMMI',
    'PMP',
    'Six Sigma',
    'ITIL',
    'Other',
]


@router.get('/status', response_model=OnboardingStateResponse)
async def get_onboarding_status(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's onboarding status"""
    state = await onboarding_service.get_state_by_user(db, UUID(current_user.user_id))
    if not state:
        return OnboardingStateResponse(
            id='',
            user_id=current_user.user_id,
            current_step=1,
            total_steps=5,
        )
    return _state_to_response(state)


@router.post('/step/1', response_model=Step1Response)
async def step1_create_organization(
    data: Step1OrganizationCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Step 1: Create organization"""
    existing = await tenant_service.get_tenant_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Organization slug already exists',
        )

    tenant = await tenant_service.create_tenant(
        db,
        name=data.name,
        slug=data.slug,
        owner_id=UUID(current_user.user_id),
        logo_url=data.logo_url,
    )

    await onboarding_service.set_tenant(db, UUID(current_user.user_id), tenant.id)
    state = await onboarding_service.update_step_completion(
        db,
        UUID(current_user.user_id),
        step=1,
        completed=True,
        step_data={'name': data.name, 'slug': data.slug, 'logo_url': data.logo_url},
    )

    return Step1Response(
        success=True,
        step=1,
        completed=True,
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        onboarding_state=_state_to_response(state),
    )


@router.post('/step/2', response_model=Step2Response)
async def step2_company_profile(
    data: Step2ProfileSetup,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Step 2: Company profile setup"""
    state = await onboarding_service.get_state_by_user(db, UUID(current_user.user_id))
    if not state or not state.step_1_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Step 1 must be completed first',
        )

    if state.tenant_id:
        await tenant_service.update_tenant(
            db,
            state.tenant_id,
            description=data.description,
            website=data.website,
        )

    state = await onboarding_service.update_step_completion(
        db,
        UUID(current_user.user_id),
        step=2,
        completed=True,
        step_data=data.model_dump(exclude_none=True),
    )

    return Step2Response(
        success=True,
        step=2,
        completed=True,
        onboarding_state=_state_to_response(state),
    )


@router.post('/step/3', response_model=Step3Response)
async def step3_expertise_setup(
    data: Step3ExpertiseSetup,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Step 3: Tender expertise setup"""
    state = await onboarding_service.get_state_by_user(db, UUID(current_user.user_id))
    if not state or not state.step_2_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Step 2 must be completed first',
        )

    state = await onboarding_service.update_step_completion(
        db,
        UUID(current_user.user_id),
        step=3,
        completed=True,
        step_data=data.model_dump(exclude_none=True),
    )

    return Step3Response(
        success=True,
        step=3,
        completed=True,
        onboarding_state=_state_to_response(state),
    )


@router.post('/step/4', response_model=Step4Response)
async def step4_plan_selection(
    data: Step4PlanSelection,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Step 4: Plan selection"""
    state = await onboarding_service.get_state_by_user(db, UUID(current_user.user_id))
    if not state or not state.step_3_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Step 3 must be completed first',
        )

    if state.tenant_id:
        await tenant_service.update_tenant(
            db,
            state.tenant_id,
            plan=data.plan_id,
        )

    state = await onboarding_service.update_step_completion(
        db,
        UUID(current_user.user_id),
        step=4,
        completed=True,
        step_data=data.model_dump(exclude_none=True),
    )

    return Step4Response(
        success=True,
        step=4,
        completed=True,
        plan_id=data.plan_id,
        billing_cycle=data.billing_cycle,
        onboarding_state=_state_to_response(state),
    )


@router.post('/step/5', response_model=Step5Response)
async def step5_dashboard_setup(
    data: Step5DashboardSetup,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Step 5: Initial dashboard setup"""
    state = await onboarding_service.get_state_by_user(db, UUID(current_user.user_id))
    if not state or not state.step_4_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Step 4 must be completed first',
        )

    if state.tenant_id:
        from ..core.models import User
        result = await db.execute(
            select(User).where(User.id == UUID(current_user.user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            user.preferences = {
                'timezone': data.timezone,
                'currency': data.currency,
                'language': data.language,
                'email_digest': data.email_digest,
                'notifications_enabled': data.notifications_enabled,
            }
            await db.commit()

    state = await onboarding_service.update_step_completion(
        db,
        UUID(current_user.user_id),
        step=5,
        completed=True,
        step_data=data.model_dump(exclude_none=True),
    )

    return Step5Response(
        success=True,
        step=5,
        completed=True,
        is_onboarding_complete=True,
        onboarding_state=_state_to_response(state),
    )


@router.get('/plans', response_model=PlansResponse)
async def get_available_plans(
    current_user: CurrentUser,
):
    """Get available subscription plans"""
    return PlansResponse(plans=AVAILABLE_PLANS)


@router.get('/expertise-categories', response_model=ExpertiseCategoriesResponse)
async def get_expertise_categories(
    current_user: CurrentUser,
):
    """Get available expertise categories and options"""
    return ExpertiseCategoriesResponse(
        expertise_areas=EXPERTISE_AREAS,
        industries=INDUSTRIES,
        company_sizes=COMPANY_SIZES,
        annual_tender_volumes=TENDER_VOLUMES,
        average_contract_values=CONTRACT_VALUES,
        target_regions=TARGET_REGIONS,
        certifications=CERTIFICATIONS,
    )


@router.post('/reset', response_model=OnboardingStateResponse)
async def reset_onboarding(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Reset onboarding state"""
    state = await onboarding_service.reset_onboarding(db, UUID(current_user.user_id))
    return _state_to_response(state)