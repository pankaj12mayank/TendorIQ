"""AI Orchestrator Service - Main Entry Point"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..ai import AIService, AIResponse, ProviderType, get_ai_service
from .prompts import PromptTemplate, PromptRegistry, PromptBuilder, PromptType
from .chains import ChainExecutor, ChainDefinition, ChainStep, StepType, ChainExecution, ChainStatus
from .validation import ResponseValidator, HallucinationDetector, OutputSchemaValidator, ValidationResult
from .logging import AILogger, TraceContext, MetricsCollector, AIObservation


logger = logging.getLogger(__name__)


class OrchestrationConfig(BaseModel):
    default_provider: ProviderType = ProviderType.OPENAI
    default_model: str = 'gpt-4o-mini'
    max_retries: int = 3
    timeout: int = 60
    enable_validation: bool = True
    enable_hallucination_detection: bool = True
    enable_logging: bool = True
    log_to_redis: bool = True
    validation_strict: bool = False


class OrchestratorRequest(BaseModel):
    task: str
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


class OrchestratorResponse(BaseModel):
    request_id: str
    content: str
    provider: str
    model: str
    success: bool
    validation: Optional[dict] = None
    hallucination: Optional[dict] = None
    chain_execution: Optional[dict] = None
    metadata: dict = Field(default_factory=dict)
    trace_id: str
    latency_ms: int
    cost: float


class Orchestrator:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        config: Optional[OrchestrationConfig] = None,
        redis_pool=None,
    ):
        self._ai_service = ai_service or get_ai_service()
        self._config = config or OrchestrationConfig()
        self._prompt_registry = PromptRegistry(redis_pool)
        self._chain_executor = ChainExecutor(self._ai_service, self._prompt_registry)
        self._validator = ResponseValidator(redis_pool)
        self._hallucination_detector = HallucinationDetector(self._ai_service)
        self._logger = AILogger(redis_pool)
        self._redis = redis_pool

    async def execute(
        self,
        request: OrchestratorRequest,
    ) -> OrchestratorResponse:
        start_time = datetime.now(timezone.utc)
        trace_id = str(uuid4())

        try:
            if request.chain_id:
                return await self._execute_chain(request, trace_id)
            elif request.prompt_template_id:
                return await self._execute_with_template(request, trace_id)
            elif request.messages:
                return await self._execute_direct(request, trace_id)
            elif request.task:
                return await self._execute_task(request, trace_id)
            else:
                raise ValueError('No execution method specified')

        except Exception as e:
            logger.error(f'Orchestrator execution failed: {e}', extra={'trace_id': trace_id})
            await self._logger.log_error(e, request.provider or 'unknown', {'request': request.model_dump()}, trace_id)
            raise

    async def _execute_chain(
        self,
        request: OrchestratorRequest,
        trace_id: str,
    ) -> OrchestratorResponse:
        chain_def = self._get_chain_definition(request.chain_id)

        input_data = {
            'task': request.task,
            'context': request.context,
            'messages': request.messages or [],
        }

        execution = await self._chain_executor.execute(chain_def, input_data, request.context)

        response_text = ''
        if execution.steps:
            last_step = execution.steps[-1]
            if last_step.output_data and isinstance(last_step.output_data, dict):
                response_text = last_step.output_data.get('content', str(last_step.output_data))
            else:
                response_text = str(last_step.output_data)

        return OrchestratorResponse(
            request_id=str(uuid4()),
            content=response_text,
            provider='chain',
            model=chain_def.id,
            success=execution.status == ChainStatus.COMPLETED,
            chain_execution={
                'chain_id': execution.chain_id,
                'status': execution.status.value,
                'steps': len(execution.steps),
                'total_latency_ms': execution.total_latency_ms,
            },
            metadata={'chain': chain_def.model_dump()},
            trace_id=trace_id,
            latency_ms=int((datetime.now(timezone.utc) - datetime.fromisoformat(execution.start_time.isoformat())).total_seconds() * 1000) if execution.start_time else 0,
            cost=0.0,
        )

    async def _execute_with_template(
        self,
        request: OrchestratorRequest,
        trace_id: str,
    ) -> OrchestratorResponse:
        template = self._prompt_registry.get(request.prompt_template_id)
        if not template:
            raise ValueError(f'Prompt template {request.prompt_template_id} not found')

        rendered_prompt = template.render(**request.context, task=request.task)
        messages = [{'role': 'user', 'content': rendered_prompt}]

        response = await self._execute_ai_call(messages, request, trace_id)

        return response

    async def _execute_direct(
        self,
        request: OrchestratorRequest,
        trace_id: str,
    ) -> OrchestratorResponse:
        return await self._execute_ai_call(request.messages, request, trace_id)

    async def _execute_task(
        self,
        request: OrchestratorRequest,
        trace_id: str,
    ) -> OrchestratorResponse:
        messages = [{'role': 'user', 'content': request.task}]
        return await self._execute_ai_call(messages, request, trace_id)

    async def _execute_ai_call(
        self,
        messages: list[dict],
        request: OrchestratorRequest,
        trace_id: str,
    ) -> OrchestratorResponse:
        from ..ai import AIResponse, TokenUsage, CostInfo

        provider_type = ProviderType(request.provider) if request.provider else self._config.default_provider
        model = request.model or self._config.default_model

        await self._logger.log_request(
            messages=messages,
            provider=provider_type.value,
            model=model,
            trace_id=trace_id,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
        )

        response = await self._ai_service.complete(
            messages=messages,
            provider=provider_type,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            user_id=UUID(request.user_id) if request.user_id else None,
            tenant_id=UUID(request.tenant_id) if request.tenant_id else None,
        )

        validation_result = None
        hallucination_result = None

        if request.validate_response and self._config.enable_validation:
            validation_result = self._validate_response(response)

        if request.detect_hallucinations and self._config.enable_hallucination_detection:
            hallucination_result = await self._detect_hallucinations(response, request.context)

        await self._logger.log_response(
            request_id=str(uuid4()),
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=response.usage.to_dict(),
            cost=response.cost.total_cost,
            latency_ms=response.latency_ms,
            trace_id=trace_id,
            validation=validation_result.model_dump() if validation_result else None,
            hallucination=hallucination_result.model_dump() if hallucination_result else None,
        )

        return OrchestratorResponse(
            request_id=str(uuid4()),
            content=response.content,
            provider=response.provider,
            model=response.model,
            success=True,
            validation=validation_result.model_dump() if validation_result else None,
            hallucination=hallucination_result.model_dump() if hallucination_result else None,
            metadata={
                'usage': response.usage.to_dict(),
                'finish_reason': response.finish_reason,
            },
            trace_id=trace_id,
            latency_ms=response.latency_ms,
            cost=response.cost.total_cost,
        )

    def _validate_response(self, response: AIResponse) -> ValidationResult:
        return self._validator.validate(response, strict=self._config.validation_strict)

    async def _detect_hallucinations(
        self,
        response: AIResponse,
        context: dict,
    ) -> Optional[Any]:
        return await self._hallucination_detector.detect(
            content=response.content,
            context=context,
        )

    def _get_chain_definition(self, chain_id: str) -> ChainDefinition:
        return ChainDefinition(
            id=chain_id,
            name='Default Chain',
            steps=[
                ChainStep(
                    name='Analyze Task',
                    step_type=StepType.PROMPT,
                    config={'messages': [{'role': 'user', 'content': 'Analyze: {task}'}]},
                ),
            ],
        )

    def register_prompt(self, template: PromptTemplate) -> str:
        return self._prompt_registry.register(template)

    def create_chain(self, definition: ChainDefinition) -> str:
        return definition.id

    async def get_trace(self, trace_id: str) -> Optional[dict]:
        return await self._logger.get_trace(trace_id)

    async def get_analytics(
        self,
        tenant_id: Optional[str] = None,
        hours: int = 24,
    ) -> dict:
        return await self._logger.get_analytics(tenant_id, hours)


class WorkflowManager:
    def __init__(self, orchestrator: Orchestrator):
        self._orchestrator = orchestrator
        self._workflows: dict[str, dict] = {}

    def define_workflow(
        self,
        name: str,
        steps: list[dict],
        description: Optional[str] = None,
    ) -> str:
        workflow_id = str(uuid4())

        workflow = {
            'id': workflow_id,
            'name': name,
            'description': description,
            'steps': steps,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }

        self._workflows[workflow_id] = workflow
        return workflow_id

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> dict:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f'Workflow {workflow_id} not found')

        results = []
        context = input_data.copy()

        for step in workflow['steps']:
            step_type = step.get('type', 'prompt')

            if step_type == 'prompt':
                request = OrchestratorRequest(
                    task=step.get('task', ''),
                    prompt_template_id=step.get('template_id'),
                    provider=step.get('provider'),
                    model=step.get('model'),
                    temperature=step.get('temperature', 0.7),
                    max_tokens=step.get('max_tokens', 2048),
                    context=context,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                response = await self._orchestrator.execute(request)
                results.append(response.model_dump())
                context[step.get('output_key', 'result')] = response.content

            elif step_type == 'transform':
                transform_type = step.get('transform', 'pass')
                if transform_type == 'json_parse':
                    try:
                        import json
                        context[step.get('output_key', 'result')] = json.loads(context.get('result', ''))
                    except:
                        pass

            elif step_type == 'condition':
                condition = step.get('condition', {})
                field = condition.get('field')
                operator = condition.get('operator', 'eq')
                value = condition.get('value')

                field_value = context.get(field)
                passed = False

                if operator == 'eq':
                    passed = field_value == value
                elif operator == 'gt':
                    passed = field_value > value
                elif operator == 'lt':
                    passed = field_value < value
                elif operator == 'contains':
                    passed = value in str(field_value)

                if not passed and step.get('else'):
                    results.append({'condition_failed': True, 'action': 'else'})

        return {
            'workflow_id': workflow_id,
            'workflow_name': workflow['name'],
            'steps_executed': len(results),
            'results': results,
            'final_context': context,
        }

    def list_workflows(self) -> list[dict]:
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        return self._workflows.get(workflow_id)


orchestrator = Orchestrator()
workflow_manager = WorkflowManager(orchestrator)


def get_orchestrator() -> Orchestrator:
    return orchestrator


def get_workflow_manager() -> WorkflowManager:
    return workflow_manager


async def init_orchestrator(
    ai_service: Optional[AIService] = None,
    config: Optional[OrchestrationConfig] = None,
    redis_pool=None,
) -> Orchestrator:
    global orchestrator, workflow_manager
    orchestrator = Orchestrator(ai_service, config, redis_pool)
    workflow_manager = WorkflowManager(orchestrator)
    return orchestrator