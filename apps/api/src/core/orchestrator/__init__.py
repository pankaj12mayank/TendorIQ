"""AI Orchestrator Module

Centralized AI orchestration engine providing:
- Structured prompting with versioning
- Chain execution for complex workflows
- Response validation and schema enforcement
- Hallucination detection
- Full observability and logging
"""

from .prompts import (
    PromptType,
    PromptVersion,
    PromptTemplate,
    PromptRegistry,
    PromptBuilder,
)
from .chains import (
    StepType,
    ChainStep,
    ChainDefinition,
    ChainExecutor,
    ChainExecution,
    ChainStatus,
    ChainStepResult,
)
from .validation import (
    ValidationResult,
    HallucinationResult,
    ResponseValidator,
    HallucinationDetector,
    OutputSchemaValidator,
)
from .logging import (
    AIObservationType,
    AIObservation,
    TraceContext,
    AILogger,
    MetricsCollector,
)
from .service import (
    OrchestrationConfig,
    OrchestratorRequest,
    OrchestratorResponse,
    Orchestrator,
    WorkflowManager,
    orchestrator,
    workflow_manager,
    get_orchestrator,
    get_workflow_manager,
    init_orchestrator,
)


__all__ = [
    'PromptType',
    'PromptVersion',
    'PromptTemplate',
    'PromptRegistry',
    'PromptBuilder',
    'StepType',
    'ChainStep',
    'ChainDefinition',
    'ChainExecutor',
    'ChainExecution',
    'ChainStatus',
    'ChainStepResult',
    'ValidationResult',
    'HallucinationResult',
    'ResponseValidator',
    'HallucinationDetector',
    'OutputSchemaValidator',
    'AIObservationType',
    'AIObservation',
    'TraceContext',
    'AILogger',
    'MetricsCollector',
    'OrchestrationConfig',
    'OrchestratorRequest',
    'OrchestratorResponse',
    'Orchestrator',
    'WorkflowManager',
    'orchestrator',
    'workflow_manager',
    'get_orchestrator',
    'get_workflow_manager',
    'init_orchestrator',
]