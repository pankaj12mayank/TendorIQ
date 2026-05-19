"""AI Orchestrator API Router"""

from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ....core.orchestrator import (
    Orchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
    WorkflowManager,
    get_orchestrator,
    get_workflow_manager,
    PromptTemplate,
    PromptType,
    ChainDefinition,
    ChainStep,
    StepType,
)
from ....core.ai import ProviderType


router = APIRouter(prefix='/orchestrator', tags=['orchestrator'])


class ExecuteRequest(BaseModel):
    task: Optional[str] = None
    messages: Optional[list[dict[str, str]]] = None
    prompt_template_id: Optional[str] = None
    chain_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    validate_response: bool = True
    detect_hallucinations: bool = True
    context: dict = Field(default_factory=dict)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


class CreatePromptTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_type: PromptType
    content: str
    variables: list[str] = []
    output_schema: Optional[dict] = None
    tags: list[str] = []


class CreateChainRequest(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[dict]
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    timeout: int = 300
    max_retries: int = 3
    tags: list[str] = []


class CreateWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list[dict]


@router.post('/execute', response_model=OrchestratorResponse)
async def execute(request: ExecuteRequest):
    orchestrator = get_orchestrator()
    try:
        orch_request = OrchestratorRequest(
            task=request.task,
            messages=request.messages,
            prompt_template_id=request.prompt_template_id,
            chain_id=request.chain_id,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            validate_response=request.validate_response,
            detect_hallucinations=request.detect_hallucinations,
            context=request.context,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
        )
        return await orchestrator.execute(orch_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/prompts')
async def list_prompts(tag_filter: Optional[str] = None):
    orchestrator = get_orchestrator()
    tags = tag_filter.split(',') if tag_filter else None
    templates = orchestrator._prompt_registry.list_templates(tag_filter=tags)
    return {'prompts': [t.model_dump() for t in templates]}


@router.post('/prompts')
async def create_prompt(request: CreatePromptTemplateRequest):
    orchestrator = get_orchestrator()
    template = PromptTemplate(
        name=request.name,
        description=request.description,
        prompt_type=request.prompt_type,
        content=request.content,
        variables=request.variables,
        output_schema=request.output_schema,
        tags=request.tags,
    )
    template_id = orchestrator.register_prompt(template)
    return {'id': template_id, 'template': template.model_dump()}


@router.get('/prompts/{prompt_id}')
async def get_prompt(prompt_id: str, version: Optional[str] = None):
    orchestrator = get_orchestrator()
    template = orchestrator._prompt_registry.get(prompt_id, version)
    if not template:
        raise HTTPException(status_code=404, detail=f'Prompt {prompt_id} not found')
    return template.model_dump()


@router.get('/prompts/{prompt_id}/versions')
async def get_prompt_versions(prompt_id: str):
    orchestrator = get_orchestrator()
    versions = orchestrator._prompt_registry.get_versions(prompt_id)
    return {'versions': [v.model_dump() for v in versions]}


@router.post('/prompts/{prompt_id}/render')
async def render_prompt(prompt_id: str, variables: dict):
    orchestrator = get_orchestrator()
    template = orchestrator._prompt_registry.get(prompt_id)
    if not template:
        raise HTTPException(status_code=404, detail=f'Prompt {prompt_id} not found')
    rendered = template.render(**variables)
    return {'rendered': rendered}


@router.get('/chains')
async def list_chains():
    return {'chains': []}


@router.post('/chains')
async def create_chain(request: CreateChainRequest):
    steps = [ChainStep(**s) for s in request.steps]
    chain = ChainDefinition(
        name=request.name,
        description=request.description,
        steps=steps,
        input_schema=request.input_schema,
        output_schema=request.output_schema,
        timeout=request.timeout,
        max_retries=request.max_retries,
        tags=request.tags,
    )
    return {'id': chain.id, 'chain': chain.model_dump()}


@router.get('/chains/{chain_id}')
async def get_chain(chain_id: str):
    return {'id': chain_id, 'name': 'Chain'}


@router.post('/workflows')
async def create_workflow(request: CreateWorkflowRequest):
    manager = get_workflow_manager()
    workflow_id = manager.define_workflow(
        name=request.name,
        steps=request.steps,
        description=request.description,
    )
    return {'id': workflow_id}


@router.get('/workflows')
async def list_workflows():
    manager = get_workflow_manager()
    workflows = manager.list_workflows()
    return {'workflows': workflows}


@router.post('/workflows/{workflow_id}/execute')
async def execute_workflow(workflow_id: str, input_data: dict, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
    manager = get_workflow_manager()
    try:
        result = await manager.execute_workflow(workflow_id, input_data, user_id, tenant_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/traces/{trace_id}')
async def get_trace(trace_id: str):
    orchestrator = get_orchestrator()
    trace = await orchestrator.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f'Trace {trace_id} not found')
    return trace


@router.get('/analytics')
async def get_analytics(tenant_id: Optional[str] = None, hours: int = 24):
    orchestrator = get_orchestrator()
    return await orchestrator.get_analytics(tenant_id, hours)


@router.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'orchestrator'}