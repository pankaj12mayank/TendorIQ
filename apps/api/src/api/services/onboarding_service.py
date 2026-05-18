"""Onboarding Service - Core Onboarding Operations"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import OnboardingState, Tenant, Membership, User
from ...core.logging import get_logger

logger = get_logger('onboarding_service')


class OnboardingService:
    @staticmethod
    async def get_or_create_state(db: AsyncSession, user_id: UUID) -> OnboardingState:
        result = await db.execute(
            select(OnboardingState).where(OnboardingState.user_id == user_id)
        )
        state = result.scalar_one_or_none()

        if not state:
            state = OnboardingState(
                user_id=user_id,
                current_step=1,
                total_steps=5,
                step_1_completed=False,
                step_2_completed=False,
                step_3_completed=False,
                step_4_completed=False,
                step_5_completed=False,
                is_completed=False,
            )
            db.add(state)
            await db.commit()
            await db.refresh(state)
            logger.info(f'Created onboarding state for user {user_id}')

        return state

    @staticmethod
    async def get_state_by_user(db: AsyncSession, user_id: UUID) -> Optional[OnboardingState]:
        result = await db.execute(
            select(OnboardingState).where(OnboardingState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_state_by_tenant(db: AsyncSession, tenant_id: UUID) -> Optional[OnboardingState]:
        result = await db.execute(
            select(OnboardingState).where(OnboardingState.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_step_completion(
        db: AsyncSession,
        user_id: UUID,
        step: int,
        completed: bool,
        step_data: Optional[dict] = None
    ) -> OnboardingState:
        state = await OnboardingService.get_or_create_state(db, user_id)

        step_field = f'step_{step}_completed'
        data_field = f'step_{step}_data'

        if hasattr(state, step_field):
            setattr(state, step_field, completed)
        if step_data and hasattr(state, data_field):
            setattr(state, data_field, step_data)

        if completed:
            state.current_step = step + 1
            state.last_step_completed = step

        if all([
            state.step_1_completed,
            state.step_2_completed,
            state.step_3_completed,
            state.step_4_completed,
            state.step_5_completed
        ]):
            state.is_completed = True
            state.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(state)
        logger.info(f'Updated step {step} completion={completed} for user {user_id}')
        return state

    @staticmethod
    async def set_tenant(db: AsyncSession, user_id: UUID, tenant_id: UUID) -> OnboardingState:
        state = await OnboardingService.get_or_create_state(db, user_id)
        state.tenant_id = tenant_id
        await db.commit()
        await db.refresh(state)
        return state

    @staticmethod
    async def reset_onboarding(db: AsyncSession, user_id: UUID) -> OnboardingState:
        state = await OnboardingService.get_or_create_state(db, user_id)
        state.current_step = 1
        state.step_1_completed = False
        state.step_2_completed = False
        state.step_3_completed = False
        state.step_4_completed = False
        state.step_5_completed = False
        state.step_1_data = {}
        state.step_2_data = {}
        state.step_3_data = {}
        state.step_4_data = {}
        state.step_5_data = {}
        state.is_completed = False
        state.completed_at = None
        state.last_step_completed = None
        await db.commit()
        await db.refresh(state)
        logger.info(f'Reset onboarding state for user {user_id}')
        return state


onboarding_service = OnboardingService()