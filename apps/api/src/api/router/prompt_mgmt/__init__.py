"""Prompt Management Admin API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ....core.prompt_mgmt import (
    PromptManagementService,
    CreatePromptRequest,
    UpdatePromptRequest,
    CreateVersionRequest,
    RollbackRequest,
    PromptConfig,
)
from ....core.database import AsyncSession, get_db
from ...dependencies.auth import require_super_admin


router = APIRouter(
    prefix='/prompts',
    tags=['prompt_management'],
    dependencies=[Depends(require_super_admin)],
)


class CreatePromptRequestDTO(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_type: str
    category: Optional[str] = None
    content: str
    system_message: Optional[str] = None
    variables: list[str] = []
    output_schema: Optional[dict] = None
    guardrails: Optional[list[str]] = None
    examples: Optional[list[dict]] = None
    model: str = 'gpt-4o-mini'
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    tags: list[str] = []
    is_active: bool = True
    is_system: bool = False


class UpdatePromptRequestDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[list[str]] = None
    output_schema: Optional[dict] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class CreateVersionRequestDTO(BaseModel):
    content: str
    system_message: Optional[str] = None
    variables: Optional[list[str]] = None
    guardrails: Optional[list[str]] = None
    examples: Optional[list[dict]] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    change_summary: Optional[str] = None


class RollbackRequestDTO(BaseModel):
    target_version: str


async def get_service(session: AsyncSession = Depends(get_db)) -> PromptManagementService:
    return PromptManagementService(session)


def get_client_info(request: Request) -> dict:
    return {
        'ip_address': request.client.host if request.client else None,
        'user_agent': request.headers.get('user-agent'),
    }


@router.post('/', status_code=201)
async def create_prompt(
    request_data: CreatePromptRequestDTO,
    request: Request,
    service: PromptManagementService = Depends(get_service),
):
    client_info = get_client_info(request)

    config = PromptConfig(
        model=request_data.model,
        temperature=request_data.temperature,
        max_tokens=request_data.max_tokens,
        top_p=request_data.top_p,
        frequency_penalty=request_data.frequency_penalty,
        presence_penalty=request_data.presence_penalty,
    )

    req = CreatePromptRequest(
        name=request_data.name,
        description=request_data.description,
        prompt_type=request_data.prompt_type,
        category=request_data.category,
        content=request_data.content,
        system_message=request_data.system_message,
        variables=request_data.variables,
        output_schema=request_data.output_schema,
        guardrails=request_data.guardrails,
        examples=request_data.examples,
        config=config,
        tags=request_data.tags,
        is_active=request_data.is_active,
        is_system=request_data.is_system,
    )

    result = await service.create_prompt(
        request=req,
        actor=request.headers.get('x-user-id'),
        ip_address=client_info['ip_address'],
    )

    return result


@router.get('/')
async def list_prompts(
    prompt_type: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    service: PromptManagementService = Depends(get_service),
):
    return await service.list_prompts(
        prompt_type=prompt_type,
        category=category,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get('/{prompt_id}')
async def get_prompt(
    prompt_id: UUID,
    include_analytics: bool = False,
    service: PromptManagementService = Depends(get_service),
):
    result = await service.get_prompt(prompt_id, include_analytics=include_analytics)
    if not result:
        raise HTTPException(status_code=404, detail='Prompt not found')
    return result


@router.get('/name/{name}')
async def get_prompt_by_name(
    name: str,
    service: PromptManagementService = Depends(get_service),
):
    result = await service.get_prompt_by_name(name)
    if not result:
        raise HTTPException(status_code=404, detail='Prompt not found')
    return result


@router.patch('/{prompt_id}')
async def update_prompt(
    prompt_id: UUID,
    request_data: UpdatePromptRequestDTO,
    request: Request,
    service: PromptManagementService = Depends(get_service),
):
    client_info = get_client_info(request)

    req = UpdatePromptRequest(**request_data.model_dump(exclude_unset=True))
    result = await service.update_prompt(
        prompt_id=prompt_id,
        request=req,
        actor=request.headers.get('x-user-id'),
        ip_address=client_info['ip_address'],
    )

    if not result:
        raise HTTPException(status_code=404, detail='Prompt not found')
    return result


@router.delete('/{prompt_id}')
async def delete_prompt(
    prompt_id: UUID,
    service: PromptManagementService = Depends(get_service),
):
    deleted = await service._prompt_repo.delete(prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Prompt not found')
    return {'deleted': True, 'prompt_id': str(prompt_id)}


@router.get('/{prompt_id}/versions')
async def get_versions(prompt_id: UUID, service: PromptManagementService = Depends(get_service)):
    return await service.get_versions(prompt_id)


@router.post('/{prompt_id}/versions')
async def create_version(
    prompt_id: UUID,
    request_data: CreateVersionRequestDTO,
    request: Request,
    service: PromptManagementService = Depends(get_service),
):
    client_info = get_client_info(request)

    config = PromptConfig(
        model=request_data.model or 'gpt-4o-mini',
        temperature=request_data.temperature or 0.7,
        max_tokens=request_data.max_tokens or 2048,
        top_p=request_data.top_p,
        frequency_penalty=request_data.frequency_penalty,
        presence_penalty=request_data.presence_penalty,
    )

    req = CreateVersionRequest(
        content=request_data.content,
        system_message=request_data.system_message,
        variables=request_data.variables,
        guardrails=request_data.guardrails,
        examples=request_data.examples,
        model=request_data.model,
        temperature=request_data.temperature,
        max_tokens=request_data.max_tokens,
        top_p=request_data.top_p,
        frequency_penalty=request_data.frequency_penalty,
        presence_penalty=request_data.presence_penalty,
        change_summary=request_data.change_summary,
    )

    result = await service.create_version(
        prompt_id=prompt_id,
        request=req,
        actor=request.headers.get('x-user-id'),
        ip_address=client_info['ip_address'],
    )

    if not result:
        raise HTTPException(status_code=404, detail='Prompt not found')
    return result


@router.get('/{prompt_id}/versions/{version}')
async def get_version(prompt_id: UUID, version: str, service: PromptManagementService = Depends(get_service)):
    result = await service.get_version(prompt_id, version)
    if not result:
        raise HTTPException(status_code=404, detail='Version not found')
    return result


@router.post('/{prompt_id}/versions/{version}/activate')
async def activate_version(
    prompt_id: UUID,
    version: str,
    request: Request,
    service: PromptManagementService = Depends(get_service),
):
    client_info = get_client_info(request)
    version_obj = await service.get_version(prompt_id, version)
    if not version_obj:
        raise HTTPException(status_code=404, detail='Version not found')

    result = await service.activate_version(
        version_id=UUID(version_obj['id']),
        actor=request.headers.get('x-user-id'),
        ip_address=client_info['ip_address'],
    )

    return result


@router.post('/{prompt_id}/rollback')
async def rollback(
    prompt_id: UUID,
    request_data: RollbackRequestDTO,
    request: Request,
    service: PromptManagementService = Depends(get_service),
):
    client_info = get_client_info(request)

    result = await service.rollback_to_version(
        prompt_id=prompt_id,
        target_version=request_data.target_version,
        actor=request.headers.get('x-user-id'),
        ip_address=client_info['ip_address'],
    )

    if not result:
        raise HTTPException(status_code=404, detail='Version not found')
    return result


@router.post('/{prompt_id}/versions/diff')
async def compare_versions(
    prompt_id: UUID,
    version_id1: UUID,
    version_id2: UUID,
    service: PromptManagementService = Depends(get_service),
):
    return await service.get_version_diff(version_id1, version_id2)


@router.get('/{prompt_id}/analytics')
async def get_analytics(prompt_id: UUID, service: PromptManagementService = Depends(get_service)):
    return await service.get_prompt_analytics(prompt_id)


@router.get('/{prompt_id}/audit')
async def get_audit_history(
    prompt_id: UUID,
    limit: int = Query(default=50, le=200),
    service: PromptManagementService = Depends(get_service),
):
    return await service.get_audit_history(prompt_id=prompt_id, limit=limit)


@router.get('/audit/global')
async def get_global_audit_history(
    limit: int = Query(default=50, le=200),
    hours: int = Query(default=24, ge=1),
    service: PromptManagementService = Depends(get_service),
):
    return await service.get_audit_history(limit=limit)