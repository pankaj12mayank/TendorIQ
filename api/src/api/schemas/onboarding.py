"""Onboarding Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

from ..onboarding_helpers import (
    normalize_onboarding_billing_cycle,
    normalize_onboarding_plan_id,
)


class Step1OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$')
    logo_url: Optional[str] = None


class Step2ProfileSetup(BaseModel):
    description: Optional[str] = Field(None, max_length=2000)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    headquarters: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)


class ExpertiseArea(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    selected: bool = False


class Step3ExpertiseSetup(BaseModel):
    expertise_areas: list[str] = Field(default_factory=list)
    custom_expertise: Optional[str] = Field(None, max_length=500)
    annual_tender_volume: Optional[str] = Field(None, max_length=50)
    average_contract_value: Optional[str] = Field(None, max_length=50)
    target_regions: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class PlanFeature(BaseModel):
    name: str
    included: bool = True
    limit: Optional[str] = None


class PlanOption(BaseModel):
    id: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    currency: str = 'USD'
    features: list[PlanFeature]
    recommended: bool = False
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None


class Step4PlanSelection(BaseModel):
    plan_id: str = Field(..., pattern=r'^(free|starter|professional|enterprise)$')
    billing_cycle: str = Field(default='monthly', pattern=r'^(monthly|yearly)$')
    addons: list[str] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def normalize_plan_and_cycle(cls, value):
        if not isinstance(value, dict):
            return value
        raw = dict(value)
        if 'plan_id' in raw:
            raw['plan_id'] = normalize_onboarding_plan_id(str(raw['plan_id']))
        if 'billing_cycle' in raw:
            raw['billing_cycle'] = normalize_onboarding_billing_cycle(str(raw['billing_cycle']))
        return raw


class DashboardWidget(BaseModel):
    id: str
    type: str
    enabled: bool = True
    position: int = 0


class Step5DashboardSetup(BaseModel):
    widgets: list[DashboardWidget] = Field(default_factory=list)
    notifications_enabled: bool = True
    email_digest: str = 'weekly'
    timezone: str = 'UTC'
    currency: str = 'USD'
    language: str = 'en'


class OnboardingStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    tenant_id: Optional[str] = None
    current_step: int = 1
    total_steps: int = 5
    step_1_completed: bool = False
    step_2_completed: bool = False
    step_3_completed: bool = False
    step_4_completed: bool = False
    step_5_completed: bool = False
    step_1_data: dict = Field(default_factory=dict)
    step_2_data: dict = Field(default_factory=dict)
    step_3_data: dict = Field(default_factory=dict)
    step_4_data: dict = Field(default_factory=dict)
    step_5_data: dict = Field(default_factory=dict)
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OnboardingSessionTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 1800


class Step1Response(BaseModel):
    success: bool = True
    step: int = 1
    completed: bool = True
    tenant_id: str
    tenant_name: str
    onboarding_state: OnboardingStateResponse
    session: Optional[OnboardingSessionTokens] = None


class Step2Response(BaseModel):
    success: bool = True
    step: int = 2
    completed: bool = True
    onboarding_state: OnboardingStateResponse


class Step3Response(BaseModel):
    success: bool = True
    step: int = 3
    completed: bool = True
    onboarding_state: OnboardingStateResponse


class Step4Response(BaseModel):
    success: bool = True
    step: int = 4
    completed: bool = True
    plan_id: str
    billing_cycle: str
    onboarding_state: OnboardingStateResponse


class Step5Response(BaseModel):
    success: bool = True
    step: int = 5
    completed: bool = True
    is_onboarding_complete: bool = True
    onboarding_state: OnboardingStateResponse
    session: Optional[OnboardingSessionTokens] = None


class ExpertiseCategoryResponse(BaseModel):
    categories: list[str]
    industries: list[str]
    company_sizes: list[str]
    tender_volumes: list[str]
    contract_values: list[str]


AVAILABLE_PLANS = [
    {
        'id': 'free',
        'name': 'Free',
        'description': 'Perfect for getting started with tender management',
        'price_monthly': 0,
        'price_yearly': 0,
        'currency': 'USD',
        'features': [
            {'name': 'Up to 3 tenders', 'included': True},
            {'name': 'Up to 5 bids', 'included': True},
            {'name': 'Basic analytics', 'included': True},
            {'name': 'Email support', 'included': True},
            {'name': 'AI-powered summaries', 'included': False},
            {'name': 'Advanced analytics', 'included': False},
            {'name': 'Priority support', 'included': False},
        ],
        'recommended': False,
    },
    {
        'id': 'starter',
        'name': 'Starter',
        'description': 'Ideal for small teams and growing businesses',
        'price_monthly': 49,
        'price_yearly': 470,
        'currency': 'USD',
        'features': [
            {'name': 'Up to 25 tenders', 'included': True, 'limit': '25/month'},
            {'name': 'Up to 50 bids', 'included': True, 'limit': '50/month'},
            {'name': 'Basic analytics', 'included': True},
            {'name': 'Email support', 'included': True},
            {'name': 'AI-powered summaries', 'included': True, 'limit': '20/month'},
            {'name': 'Advanced analytics', 'included': False},
            {'name': 'Priority support', 'included': False},
        ],
        'recommended': False,
    },
    {
        'id': 'professional',
        'name': 'Professional',
        'description': 'For established teams with advanced needs',
        'price_monthly': 149,
        'price_yearly': 1430,
        'currency': 'USD',
        'features': [
            {'name': 'Unlimited tenders', 'included': True},
            {'name': 'Unlimited bids', 'included': True},
            {'name': 'Basic analytics', 'included': True},
            {'name': 'Email support', 'included': True},
            {'name': 'AI-powered summaries', 'included': True, 'limit': '100/month'},
            {'name': 'Advanced analytics', 'included': True},
            {'name': 'Priority support', 'included': True},
        ],
        'recommended': True,
    },
    {
        'id': 'enterprise',
        'name': 'Enterprise',
        'description': 'Custom solutions for large organizations',
        'price_monthly': 499,
        'price_yearly': 4790,
        'currency': 'USD',
        'features': [
            {'name': 'Unlimited tenders', 'included': True},
            {'name': 'Unlimited bids', 'included': True},
            {'name': 'Basic analytics', 'included': True},
            {'name': 'Email support', 'included': True},
            {'name': 'AI-powered summaries', 'included': True},
            {'name': 'Advanced analytics', 'included': True},
            {'name': 'Priority support', 'included': True, 'limit': '24/7'},
            {'name': 'Custom integrations', 'included': True},
            {'name': 'Dedicated account manager', 'included': True},
        ],
        'recommended': False,
    },
]