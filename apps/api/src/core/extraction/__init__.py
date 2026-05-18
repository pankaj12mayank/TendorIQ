"""Structured Extraction Module

AI-powered extraction engine for tender documents.
Extracts structured information with:
- Pydantic validation
- JSON-only outputs
- Confidence scoring
- Retry logic
- Validation fallback
"""

from .schemas import (
    ExtractionStatus,
    ConfidenceLevel,
    TenderSummary,
    EligibilityCriteria,
    TechnicalRequirement,
    TechnicalRequirementsCollection,
    FinancialRequirement,
    FinancialRequirementsCollection,
    Deadline,
    DeadlinesCollection,
    MandatoryDocument,
    MandatoryDocumentsCollection,
    Clause,
    ClausesCollection,
    ContractTerms,
    AwardCriteria,
    AwardCriteriaCollection,
    ContactInformation,
    SubmissionGuidelines,
    CompleteExtractionResult,
    ExtractionRequest,
    ExtractionResponse,
)
from .prompts import PromptTemplates, ExtractionConfig, ExtractionPrompts
from .service import (
    ExtractionError,
    ValidationFallback,
    ExtractionValidator,
    ExtractionService,
    ExtractionPipeline,
    extraction_service,
    extraction_pipeline,
    get_extraction_service,
    get_extraction_pipeline,
)


__all__ = [
    'ExtractionStatus',
    'ConfidenceLevel',
    'TenderSummary',
    'EligibilityCriteria',
    'TechnicalRequirement',
    'TechnicalRequirementsCollection',
    'FinancialRequirement',
    'FinancialRequirementsCollection',
    'Deadline',
    'DeadlinesCollection',
    'MandatoryDocument',
    'MandatoryDocumentsCollection',
    'Clause',
    'ClausesCollection',
    'ContractTerms',
    'AwardCriteria',
    'AwardCriteriaCollection',
    'ContactInformation',
    'SubmissionGuidelines',
    'CompleteExtractionResult',
    'ExtractionRequest',
    'ExtractionResponse',
    'PromptTemplates',
    'ExtractionConfig',
    'ExtractionPrompts',
    'ExtractionError',
    'ValidationFallback',
    'ExtractionValidator',
    'ExtractionService',
    'ExtractionPipeline',
    'extraction_service',
    'extraction_pipeline',
    'get_extraction_service',
    'get_extraction_pipeline',
]