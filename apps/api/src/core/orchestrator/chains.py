"""Chain Execution Engine for AI Workflows"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..ai import AIService, AIResponse, ProviderType
from .prompts import PromptTemplate, PromptRegistry


logger = logging.getLogger(__name__)


class ChainStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class StepType(str, Enum):
    PROMPT = 'prompt'
    TRANSFORM = 'transform'
    FILTER = 'filter'
    ROUTER = 'router'
    MERGE = 'merge'
    CONDITION = 'condition'
    PARALLEL = 'parallel'
    LOOP = 'loop'


@dataclass
class ChainStepResult:
    step_id: str
    step_name: str
    step_type: StepType
    input_data: dict
    output_data: Any
    success: bool
    error: Optional[str] = None
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class ChainExecution:
    chain_id: str
    name: str
    status: ChainStatus
    steps: list[ChainStepResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_latency_ms: int = 0
    metadata: dict = field(default_factory=dict)

    def add_step(self, result: ChainStepResult) -> None:
        self.steps.append(result)
        if not self.start_time:
            self.start_time = datetime.now(timezone.utc)
        if result.success:
            self.total_latency_ms += result.latency_ms

    def complete(self) -> None:
        self.status = ChainStatus.COMPLETED
        self.end_time = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        self.status = ChainStatus.FAILED
        self.end_time = datetime.now(timezone.utc)
        self.metadata['error'] = error


class ChainStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    step_type: StepType
    config: dict = Field(default_factory=dict)
    next_step: Optional[str] = None
    error_handler: Optional[str] = None
    conditions: Optional[dict] = None

    class Config:
        use_enum_values = True


class ChainDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    steps: list[ChainStep]
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    timeout: int = 300
    max_retries: int = 3
    tags: list[str] = Field(default_factory=list)


class ChainExecutor:
    def __init__(
        self,
        ai_service: AIService,
        prompt_registry: Optional[PromptRegistry] = None,
    ):
        self.ai_service = ai_service
        self.prompt_registry = prompt_registry or PromptRegistry()
        self._transforms: dict[str, Callable] = {}
        self._register_default_transforms()

    def _register_default_transforms(self) -> None:
        self._transforms['json_parse'] = self._json_transform
        self._transforms['extract_entities'] = self._entity_transform
        self._transforms['filter_by_confidence'] = self._confidence_filter
        self._transforms['merge_results'] = self._merge_transform

    async def execute(
        self,
        chain: ChainDefinition,
        input_data: dict,
        context: Optional[dict] = None,
    ) -> ChainExecution:
        execution = ChainExecution(
            chain_id=chain.id,
            name=chain.name,
            status=ChainStatus.RUNNING,
        )

        context = context or {}
        current_data = input_data.copy()

        try:
            for step in chain.steps:
                result = await self._execute_step(
                    step=step,
                    input_data=current_data,
                    context=context,
                    execution=execution,
                    chain=chain,
                )

                execution.add_step(result)

                if not result.success:
                    if step.error_handler:
                        error_step = self._find_step(chain, step.error_handler)
                        if error_step:
                            await self._execute_step(
                                step=error_step,
                                input_data=current_data,
                                context=context,
                                execution=execution,
                                chain=chain,
                            )
                    else:
                        execution.fail(result.error or 'Step failed')
                        break

                current_data = result.output_data

                if step.next_step:
                    next_idx = self._find_step_index(chain, step.next_step)
                    if next_idx >= 0:
                        chain.steps = chain.steps[next_idx:]

            if execution.status == ChainStatus.RUNNING:
                execution.complete()

        except Exception as e:
            logger.error(f'Chain execution failed: {e}')
            execution.fail(str(e))

        return execution

    async def _execute_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
        execution: ChainExecution,
        chain: ChainDefinition,
    ) -> ChainStepResult:
        import time
        start_time = time.time()

        try:
            if step.step_type == StepType.PROMPT:
                output = await self._execute_prompt_step(step, input_data, context)
            elif step.step_type == StepType.TRANSFORM:
                output = await self._execute_transform_step(step, input_data, context)
            elif step.step_type == StepType.FILTER:
                output = await self._execute_filter_step(step, input_data, context)
            elif step.step_type == StepType.ROUTER:
                output = await self._execute_router_step(step, input_data, context)
            elif step.step_type == StepType.MERGE:
                output = await self._execute_merge_step(step, input_data, context)
            elif step.step_type == StepType.CONDITION:
                output = await self._execute_condition_step(step, input_data, context)
            elif step.step_type == StepType.PARALLEL:
                output = await self._execute_parallel_step(step, input_data, context, chain)
            else:
                raise ValueError(f'Unknown step type: {step.step_type}')

            latency_ms = int((time.time() - start_time) * 1000)

            return ChainStepResult(
                step_id=step.id,
                step_name=step.name,
                step_type=step.step_type,
                input_data=input_data,
                output_data=output,
                success=True,
                latency_ms=latency_ms,
                metadata={'step_config': step.config},
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f'Step {step.name} failed: {e}')

            return ChainStepResult(
                step_id=step.id,
                step_name=step.name,
                step_type=step.step_type,
                input_data=input_data,
                output_data=None,
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )

    async def _execute_prompt_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> dict:
        prompt_config = step.config
        prompt_template_id = prompt_config.get('prompt_template_id')
        messages = prompt_config.get('messages', [])

        if prompt_template_id:
            template = self.prompt_registry.get(prompt_template_id)
            if template:
                rendered = template.render(**input_data)
                messages = [{'role': 'user', 'content': rendered}]

        provider_type = ProviderType(prompt_config.get('provider', 'openai'))
        model = prompt_config.get('model')
        temperature = prompt_config.get('temperature', 0.7)
        max_tokens = prompt_config.get('max_tokens', 2048)

        response = await self.ai_service.complete(
            messages=messages,
            provider=provider_type,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            'content': response.content,
            'usage': response.usage.to_dict(),
            'cost': response.cost.to_dict(),
            'latency_ms': response.latency_ms,
            'finish_reason': response.finish_reason,
        }

    async def _execute_transform_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> Any:
        transform_type = step.config.get('type', 'json_parse')
        transform_func = self._transforms.get(transform_type)

        if transform_func:
            return await transform_func(step.config, input_data, context)
        else:
            return input_data

    async def _execute_filter_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> dict:
        filter_config = step.config
        results = input_data if isinstance(input_data, list) else [input_data]

        min_confidence = filter_config.get('min_confidence', 0.0)
        max_results = filter_config.get('max_results', 100)

        if min_confidence > 0:
            results = [r for r in results if r.get('confidence', 1.0) >= min_confidence]

        return {'items': results[:max_results], 'total': len(results)}

    async def _execute_router_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> dict:
        routes = step.config.get('routes', {})
        criteria = step.config.get('criteria', 'content_length')

        if criteria == 'content_length':
            length = len(input_data.get('content', ''))
            for route_key, threshold in routes.items():
                if length <= threshold:
                    return {'route': route_key, 'next_step': route_key, 'data': input_data}

        return {'route': 'default', 'next_step': None, 'data': input_data}

    async def _execute_merge_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> dict:
        sources = step.config.get('sources', [])
        merge_type = step.config.get('merge_type', 'concat')

        results = []
        for source in sources:
            source_data = context.get(source) or input_data.get(source)
            if source_data:
                results.append(source_data)

        if merge_type == 'concat':
            return {'merged': ' '.join(str(r) for r in results)}
        elif merge_type == 'union':
            merged = {}
            for r in results:
                if isinstance(r, dict):
                    merged.update(r)
            return {'merged': merged}
        else:
            return {'merged': results}

    async def _execute_condition_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
    ) -> dict:
        conditions = step.config.get('conditions', [])
        condition_type = step.config.get('type', 'all')

        satisfied = []
        for cond in conditions:
            field = cond.get('field')
            operator = cond.get('operator', 'eq')
            value = cond.get('value')

            field_value = input_data.get(field) or context.get(field)

            if operator == 'eq':
                match = field_value == value
            elif operator == 'ne':
                match = field_value != value
            elif operator == 'gt':
                match = field_value > value
            elif operator == 'lt':
                match = field_value < value
            elif operator == 'contains':
                match = value in str(field_value)
            else:
                match = False

            satisfied.append(match)

        if condition_type == 'all':
            result = all(satisfied)
        else:
            result = any(satisfied)

        return {'condition_met': result, 'data': input_data}

    async def _execute_parallel_step(
        self,
        step: ChainStep,
        input_data: dict,
        context: dict,
        chain: ChainDefinition,
    ) -> dict:
        parallel_steps = step.config.get('steps', [])
        results = []

        tasks = []
        for ps in parallel_steps:
            ps_def = ChainStep(**ps)
            tasks.append(self._execute_step(ps_def, input_data, context, None, chain))

        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        for sr in step_results:
            if isinstance(sr, Exception):
                results.append({'error': str(sr)})
            else:
                results.append(sr.output_data)

        return {'parallel_results': results}

    def _json_transform(self, config: dict, input_data: dict, context: dict) -> dict:
        content = input_data.get('content', '')
        try:
            import json
            return json.loads(content)
        except:
            return {'raw': content, 'parse_error': True}

    def _entity_transform(self, config: dict, input_data: dict, context: dict) -> dict:
        return {'entities': [], 'count': 0}

    def _confidence_filter(self, config: dict, input_data: dict, context: dict) -> dict:
        threshold = config.get('threshold', 0.5)
        items = input_data if isinstance(input_data, list) else [input_data]
        filtered = [i for i in items if i.get('confidence', 1.0) >= threshold]
        return {'items': filtered, 'count': len(filtered)}

    def _merge_transform(self, config: dict, input_data: dict, context: dict) -> dict:
        return {'merged': input_data}

    def _find_step(self, chain: ChainDefinition, step_id: str) -> Optional[ChainStep]:
        for step in chain.steps:
            if step.id == step_id:
                return step
        return None

    def _find_step_index(self, chain: ChainDefinition, step_id: str) -> int:
        for i, step in enumerate(chain.steps):
            if step.id == step_id:
                return i
        return -1