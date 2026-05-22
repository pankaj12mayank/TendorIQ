"""AI Provider API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ....core.ai.config import ProviderType
from ....core.ai.service import AIService, get_ai_service
from ....core.auth import AuthContext
from ...dependencies.rbac_deps import RequireAiAnalysis, RequireApiAccess, require_tenant_member


router = APIRouter(
    prefix='/ai',
    tags=['ai'],
    dependencies=[Depends(require_tenant_member)],
)


class CompletionRequest(BaseModel):
    messages: list[dict[str, str]]
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


class CompletionResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: dict
    cost: dict
    latency_ms: int
    request_id: str
    finish_reason: str


class TokenEstimateRequest(BaseModel):
    text: str
    model: Optional[str] = None
    provider: Optional[str] = None


class UsageStatsResponse(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    currency: str = 'USD'


class ProviderStatusResponse(BaseModel):
    provider: str
    available: bool
    model: Optional[str] = None
    stats: Optional[dict] = None
    error: Optional[str] = None


@router.post('/complete', response_model=CompletionResponse)
async def complete(
    request: CompletionRequest,
    current_user: RequireAiAnalysis,
    service: AIService = Depends(get_ai_service),
):
    try:
        provider_type = ProviderType(request.provider) if request.provider else None

        response = await service.complete(
            messages=request.messages,
            provider=provider_type,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return CompletionResponse(
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=response.usage.to_dict(),
            cost=response.cost.to_dict(),
            latency_ms=response.latency_ms,
            request_id=response.request_id,
            finish_reason=response.finish_reason,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/providers')
async def list_providers(service: AIService = Depends(get_ai_service)):
    providers = await service.get_available_providers()
    return {'providers': providers}


@router.get('/providers/{provider}', response_model=ProviderStatusResponse)
async def get_provider_status(
    provider: str,
    service: AIService = Depends(get_ai_service),
):
    try:
        provider_type = ProviderType(provider)
        status = await service.validate_provider(provider_type)
        return status
    except ValueError:
        raise HTTPException(status_code=400, detail=f'Unknown provider: {provider}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/estimate-cost')
async def estimate_cost(
    request: TokenEstimateRequest,
    service: AIService = Depends(get_ai_service),
):
    try:
        provider_type = ProviderType(request.provider) if request.provider else None
        cost = await service.estimate_cost(
            text=request.text,
            model=request.model,
            provider=provider_type,
        )
        return cost.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/usage/{tenant_id}')
async def get_tenant_usage(
    tenant_id: str,
    service: AIService = Depends(get_ai_service),
):
    try:
        usage = await service.get_usage_stats(tenant_id=UUID(tenant_id))
        return usage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/usage/user/{user_id}')
async def get_user_usage(
    user_id: str,
    tenant_id: str,
    service: AIService = Depends(get_ai_service),
):
    try:
        usage = await service.get_usage_stats(
            user_id=UUID(user_id),
            tenant_id=UUID(tenant_id),
        )
        return usage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/limits/{tenant_id}')
async def set_spending_limit(
    tenant_id: str,
    monthly_limit: float,
    service: AIService = Depends(get_ai_service),
):
    try:
        await service.set_spending_limit(UUID(tenant_id), monthly_limit)
        return {'success': True, 'monthly_limit': monthly_limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/limits/{tenant_id}/check')
async def check_spending_limit(
    tenant_id: str,
    user_id: Optional[str] = None,
    service: AIService = Depends(get_ai_service),
):
    try:
        result = await service.check_spending_limit(
            tenant_id=UUID(tenant_id),
            user_id=UUID(user_id) if user_id else None,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/models')
async def list_models():
    from ....core.ai.config import ProviderDefaults
    models = {
        'openai': list(ProviderDefaults.OPENAI_MODELS.keys()),
        'gemini': list(ProviderDefaults.GEMINI_MODELS.keys()),
        'ollama': list(ProviderDefaults.OLLAMA_MODELS.keys()),
    }
    return {'models': models}


@router.get('/cost-comparison')
async def compare_costs(
    models: str,
    input_tokens: int,
    output_tokens: int,
):
    from ....core.ai.accounting import CostCalculator

    model_list = [m.strip() for m in models.split(',')]
    comparison = CostCalculator.compare_models(model_list, input_tokens, output_tokens)
    return {'comparison': comparison}