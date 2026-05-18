"""Structured Extraction Service with Validation and Retry"""

import asyncio
import json
import logging
import time
from datetime import datetime, date
from typing import Optional, Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from ..ai import AIService, ProviderType, AIResponse
from ..orchestrator import Orchestrator
from .schemas import (
    ExtractionStatus,
    TenderSummary,
    EligibilityCriteria,
    TechnicalRequirementsCollection,
    FinancialRequirementsCollection,
    DeadlinesCollection,
    MandatoryDocumentsCollection,
    ClausesCollection,
    ContractTerms,
    AwardCriteriaCollection,
    ContactInformation,
    SubmissionGuidelines,
    CompleteExtractionResult,
    ExtractionRequest,
    ExtractionResponse,
)
from .prompts import PromptTemplates, ExtractionConfig


logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    def __init__(self, message: str, field: Optional[str] = None, retryable: bool = True):
        self.message = message
        self.field = field
        self.retryable = retryable
        super().__init__(self.message)


class ValidationFallback:
    @staticmethod
    def fix_json_response(raw_response: str) -> dict:
        raw_response = raw_response.strip()

        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.startswith('```'):
            raw_response = raw_response[3:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()

        for quote in ['"""', "'''"]:
            if raw_response.startswith(quote) and raw_response.endswith(quote):
                raw_response = raw_response[3:-3].strip()

        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass

        try:
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = raw_response[start_idx:end_idx + 1]
                return json.loads(json_str)
        except:
            pass

        try:
            start_idx = raw_response.find('[')
            end_idx = raw_response.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = raw_response[start_idx:end_idx + 1]
                return json.loads(json_str)
        except:
            pass

        return {}


class ExtractionValidator:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_tender_summary(self, data: dict) -> tuple[Optional[TenderSummary], list[str]]:
        try:
            summary = TenderSummary(**data)
            return summary, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            summary = TenderSummary(
                title=data.get('title', ''),
                reference_number=data.get('reference_number'),
                description=data.get('description', ''),
                organization=data.get('organization', ''),
                department=data.get('department'),
                category=data.get('category'),
                type=data.get('type'),
                summary_confidence=0.5,
            )
            return summary, errors

    def validate_eligibility(self, data: dict) -> tuple[Optional[EligibilityCriteria], list[str]]:
        try:
            eligibility = EligibilityCriteria(**data)
            return eligibility, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            eligibility = EligibilityCriteria(
                criteria=data.get('criteria', []),
                min_experience_years=data.get('min_experience_years'),
                required_certifications=data.get('required_certifications', []),
                required_registrations=data.get('required_registrations', []),
                exclusions=data.get('exclusions', []),
                eligibility_confidence=0.5,
            )
            return eligibility, errors

    def validate_technical(self, data: dict) -> tuple[Optional[TechnicalRequirementsCollection], list[str]]:
        try:
            technical = TechnicalRequirementsCollection(**data)
            return technical, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            tech_reqs = data.get('requirements', [])
            requirements = []
            for req in tech_reqs:
                if isinstance(req, dict):
                    requirements.append(req)
            technical = TechnicalRequirementsCollection(
                requirements=requirements,
                total_requirements=len(requirements),
                technical_confidence=0.5,
            )
            return technical, errors

    def validate_financial(self, data: dict) -> tuple[Optional[FinancialRequirementsCollection], list[str]]:
        try:
            financial = FinancialRequirementsCollection(**data)
            return financial, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            financial = FinancialRequirementsCollection(
                items=data.get('items', []),
                total_value=data.get('total_value'),
                currency=data.get('currency', 'INR'),
                has_bid_security=data.get('has_bid_security', False),
                bid_security_amount=data.get('bid_security_amount'),
                financial_confidence=0.5,
            )
            return financial, errors

    def validate_deadlines(self, data: dict) -> tuple[Optional[DeadlinesCollection], list[str]]:
        try:
            deadlines = DeadlinesCollection(**data)
            return deadlines, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            deadlines_list = data.get('deadlines', [])
            deadlines_obj = []
            for d in deadlines_list:
                if isinstance(d, dict):
                    deadlines_obj.append(d)
            deadlines = DeadlinesCollection(
                deadlines=deadlines_obj,
                submission_deadline=data.get('submission_deadline'),
                earliest_deadline=data.get('earliest_deadline'),
                total_deadlines=len(deadlines_obj),
                deadlines_confidence=0.5,
            )
            return deadlines, errors

    def validate_documents(self, data: dict) -> tuple[Optional[MandatoryDocumentsCollection], list[str]]:
        try:
            documents = MandatoryDocumentsCollection(**data)
            return documents, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            MandatoryDocumentsCollection(
                documents=data.get('documents', []),
                total_mandatory=data.get('total_mandatory', 0),
                total_optional=data.get('total_optional', 0),
                documents_confidence=0.5,
            )

    def validate_clauses(self, data: dict) -> tuple[Optional[ClausesCollection], list[str]]:
        try:
            clauses = ClausesCollection(**data)
            return clauses, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            clauses = ClausesCollection(
                clauses=data.get('clauses', []),
                total_clauses=data.get('total_clauses', 0),
                critical_count=data.get('critical_count', 0),
                clauses_confidence=0.5,
            )
            return clauses, errors

    def validate_contract(self, data: dict) -> tuple[Optional[ContractTerms], list[str]]:
        try:
            contract = ContractTerms(**data)
            return contract, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            return None, errors

    def validate_award(self, data: dict) -> tuple[Optional[AwardCriteriaCollection], list[str]]:
        try:
            award = AwardCriteriaCollection(**data)
            return award, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            award = AwardCriteriaCollection(
                criteria=data.get('criteria', []),
                total_criteria=data.get('total_criteria', 0),
                evaluation_method=data.get('evaluation_method'),
                award_confidence=0.5,
            )
            return award, errors

    def validate_contact(self, data: dict) -> Optional[ContactInformation]:
        try:
            return ContactInformation(**data)
        except ValidationError:
            return None

    def validate_submission(self, data: dict) -> tuple[Optional[SubmissionGuidelines], list[str]]:
        try:
            submission = SubmissionGuidelines(**data)
            return submission, []
        except ValidationError as e:
            errors = [f'{err["loc"]}: {err["msg"]}' for err in e.errors()]
            if self.strict:
                return None, errors
            submission = SubmissionGuidelines(
                method=data.get('method'),
                format_required=data.get('format_required', []),
                language=data.get('language', 'English'),
                guidelines_confidence=0.5,
            )
            return submission, errors


class ExtractionService:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        orchestrator: Optional[Orchestrator] = None,
    ):
        self._ai_service = ai_service
        self._orchestrator = orchestrator
        self._validator = ExtractionValidator()

    async def extract(
        self,
        document_text: str,
        request: ExtractionRequest,
    ) -> ExtractionResponse:
        extraction_id = str(uuid4())
        start_time = time.time()
        retry_count = 0
        errors: list[str] = []
        all_warnings: list[str] = []

        result = CompleteExtractionResult(
            extraction_id=extraction_id,
            document_id=request.document_id,
            status=ExtractionStatus.EXTRACTING,
        )

        extraction_order = ExtractionConfig.EXTRACTION_ORDER
        if request.fields_to_extract:
            extraction_order = [f for f in extraction_order if f in request.fields_to_extract]

        self._validator.strict = request.validation_strict

        for extraction_type in extraction_order:
            try:
                field_result = await self._extract_field(
                    extraction_type=extraction_type,
                    document_text=document_text,
                    retry=request.retry_on_failure,
                )

                setattr(result, extraction_type, field_result.get('data'))
                all_warnings.extend(field_result.get('warnings', []))

            except Exception as e:
                logger.error(f'Extraction failed for {extraction_type}: {e}')
                errors.append(f'{extraction_type}: {str(e)}')

                if extraction_type in ExtractionConfig.CRITICAL_EXTRACTIONS:
                    result.status = ExtractionStatus.PARTIAL
                    break

        if not errors:
            result.status = ExtractionStatus.VALIDATED
        elif result.status != ExtractionStatus.PARTIAL:
            result.status = ExtractionStatus.PARTIAL

        result.overall_confidence = self._calculate_overall_confidence(result)
        result.validation_errors = errors
        result.warnings = all_warnings

        processing_time = int((time.time() - start_time) * 1000)

        return ExtractionResponse(
            extraction_id=extraction_id,
            status=result.status,
            result=result,
            confidence=result.overall_confidence,
            processing_time_ms=processing_time,
            retry_count=retry_count,
            errors=errors,
        )

    async def _extract_field(
        self,
        extraction_type: str,
        document_text: str,
        retry: bool = True,
    ) -> dict:
        prompt = PromptTemplates.get_prompt(extraction_type, document_text)

        for attempt in range(ExtractionConfig.MAX_RETRIES if retry else 1):
            try:
                messages = [
                    {'role': 'system', 'content': PromptTemplates.get_system_prompt()},
                    {'role': 'user', 'content': prompt},
                ]

                response = await self._call_ai(messages)

                raw_json = response.content
                parsed = ValidationFallback.fix_json_response(raw_json)

                validated_data = self._validate_extraction(extraction_type, parsed)

                confidence = self._estimate_confidence(extraction_type, parsed, validated_data)

                return {
                    'data': validated_data,
                    'confidence': confidence,
                    'raw': raw_json,
                    'warnings': [],
                }

            except Exception as e:
                logger.warning(f'Attempt {attempt + 1} failed for {extraction_type}: {e}')
                if attempt < ExtractionConfig.MAX_RETRIES - 1:
                    await asyncio.sleep(ExtractionConfig.RETRY_DELAYS[attempt])
                else:
                    raise ExtractionError(str(e), extraction_type, retryable=True)

        raise ExtractionError('Max retries exceeded', extraction_type)

    async def _call_ai(self, messages: list[dict]) -> AIResponse:
        if self._ai_service:
            return await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=ExtractionConfig.DEFAULT_MODEL,
                temperature=ExtractionConfig.DEFAULT_TEMPERATURE,
                max_tokens=ExtractionConfig.DEFAULT_MAX_TOKENS,
            )
        else:
            raise ExtractionError('AI service not configured')

    def _validate_extraction(self, extraction_type: str, data: dict) -> Any:
        validators = {
            'summary': self._validator.validate_tender_summary,
            'eligibility': self._validator.validate_eligibility,
            'technical': self._validator.validate_technical,
            'financial': self._validator.validate_financial,
            'deadlines': self._validator.validate_deadlines,
            'documents': self._validator.validate_documents,
            'clauses': self._validator.validate_clauses,
            'contract': self._validator.validate_contract,
            'award': self._validator.validate_award,
            'contact': self._validator.validate_contact,
            'submission': self._validator.validate_submission,
        }

        validator = validators.get(extraction_type)
        if validator:
            result, errors = validator(data)
            if errors:
                self._validator.warnings.extend(errors)
            return result

        return data

    def _estimate_confidence(
        self,
        extraction_type: str,
        raw_data: dict,
        validated_data: Any,
    ) -> float:
        if validated_data is None:
            return 0.0

        base_confidence = 0.7

        required_fields = {
            'summary': ['title', 'organization', 'description'],
            'eligibility': ['criteria'],
            'technical': ['requirements'],
            'financial': ['items'],
            'deadlines': ['deadlines'],
            'documents': ['documents'],
            'clauses': ['clauses'],
        }

        expected_fields = required_fields.get(extraction_type, [])
        if expected_fields:
            found_fields = sum(1 for f in expected_fields if f in raw_data and raw_data[f])
            field_ratio = found_fields / len(expected_fields)
            base_confidence *= (0.7 + 0.3 * field_ratio)

        return min(1.0, base_confidence)

    def _calculate_overall_confidence(self, result: CompleteExtractionResult) -> float:
        confidence_fields = [
            result.tender_summary.summary_confidence if result.tender_summary else 0,
            result.eligibility_criteria.eligibility_confidence if result.eligibility_criteria else 0,
            result.technical_requirements.technical_confidence if result.technical_requirements else 0,
            result.financial_requirements.financial_confidence if result.financial_requirements else 0,
            result.deadlines.deadlines_confidence if result.deadlines else 0,
            result.mandatory_documents.documents_confidence if result.mandatory_documents else 0,
            result.clauses.clauses_confidence if result.clauses else 0,
        ]

        if not confidence_fields:
            return 0.0

        return sum(confidence_fields) / len(confidence_fields)

    async def extract_single_field(
        self,
        extraction_type: str,
        document_text: str,
    ) -> dict:
        result = await self._extract_field(extraction_type, document_text)
        return result

    async def quick_extract(self, document_text: str) -> CompleteExtractionResult:
        critical_types = ['summary', 'deadlines', 'eligibility']
        result = CompleteExtractionResult()

        for extraction_type in critical_types:
            try:
                field_result = await self._extract_field(extraction_type, document_text)
                setattr(result, extraction_type, field_result.get('data'))
            except Exception as e:
                logger.error(f'Quick extract failed for {extraction_type}: {e}')

        result.overall_confidence = self._calculate_overall_confidence(result)
        return result


class ExtractionPipeline:
    def __init__(self, extraction_service: Optional[ExtractionService] = None):
        self._service = extraction_service or ExtractionService()

    async def run(
        self,
        document_text: str,
        request: ExtractionRequest,
    ) -> ExtractionResponse:
        return await self._service.extract(document_text, request)

    async def run_with_fallback(
        self,
        document_text: str,
        request: ExtractionRequest,
    ) -> ExtractionResponse:
        try:
            return await self.run(document_text, request)
        except Exception as e:
            logger.warning(f'Primary extraction failed, trying fallback: {e}')

            request.validation_strict = False
            request.retry_on_failure = True

            try:
                return await self.run(document_text, request)
            except Exception as e2:
                logger.error(f'Fallback also failed: {e2}')
                return ExtractionResponse(
                    extraction_id=str(uuid4()),
                    status=ExtractionStatus.FAILED,
                    errors=[str(e), str(e2)],
                    confidence=0.0,
                )

    async def batch_extract(
        self,
        documents: list[tuple[str, ExtractionRequest]],
    ) -> list[ExtractionResponse]:
        tasks = []
        for doc_text, req in documents:
            tasks.append(self._service.extract(doc_text, req))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(ExtractionResponse(
                    extraction_id=str(uuid4()),
                    status=ExtractionStatus.FAILED,
                    errors=[str(result)],
                    confidence=0.0,
                ))
            else:
                responses.append(result)

        return responses


extraction_service = ExtractionService()
extraction_pipeline = ExtractionPipeline(extraction_service)


def get_extraction_service() -> ExtractionService:
    return extraction_service


def get_extraction_pipeline() -> ExtractionPipeline:
    return extraction_pipeline