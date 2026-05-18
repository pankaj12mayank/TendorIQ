"""Response Validation and Hallucination Detection"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ValidationError, create_model

from ..ai import AIResponse


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    schema_compliance: float = 1.0
    metadata: dict = {}


class HallucinationResult(BaseModel):
    score: float
    risk_level: str
    detected_issues: list[str] = []
    facts_confirmed: list[str] = []
    facts_contradicted: list[str] = []
    confidence: float
    recommendations: list[str] = []


class ResponseValidator:
    def __init__(self, redis_pool=None):
        self._redis = redis_pool
        self._schemas: dict[str, dict] = {}
        self._validation_cache: dict[str, ValidationResult] = {}

    def load_schema(self, schema_id: str, schema: dict) -> None:
        self._schemas[schema_id] = schema

    def validate(
        self,
        response: AIResponse,
        schema_id: Optional[str] = None,
        strict: bool = False,
    ) -> ValidationResult:
        errors = []
        warnings = []

        if not response.content:
            errors.append('Empty response content')
            return ValidationResult(is_valid=False, errors=errors)

        if schema_id and schema_id in self._schemas:
            schema_result = self._validate_against_schema(
                response.content,
                self._schemas[schema_id],
                strict,
            )
            errors.extend(schema_result.get('errors', []))
            warnings.extend(schema_result.get('warnings', []))

        format_result = self._validate_format(response.content)
        errors.extend(format_result.get('errors', []))
        warnings.extend(format_result.get('warnings', []))

        length_result = self._validate_length(response.content, response.usage)
        if not length_result.get('valid', True):
            warnings.append(length_result.get('message', ''))

        schema_compliance = max(0, 1 - (len(errors) * 0.1))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_compliance=schema_compliance,
            metadata={
                'response_length': len(response.content),
                'token_usage': response.usage.to_dict(),
                'finish_reason': response.finish_reason,
            },
        )

    def _validate_against_schema(
        self,
        content: str,
        schema: dict,
        strict: bool,
    ) -> dict:
        errors = []
        warnings = []

        try:
            data = json.loads(content)

            for field, field_schema in schema.get('properties', {}).items():
                field_type = field_schema.get('type')

                if field not in data:
                    if field_schema.get('required', False):
                        errors.append(f'Missing required field: {field}')
                else:
                    value = data[field]

                    if field_type == 'string' and not isinstance(value, str):
                        errors.append(f'Field {field} must be string')
                    elif field_type == 'number' and not isinstance(value, (int, float)):
                        errors.append(f'Field {field} must be number')
                    elif field_type == 'boolean' and not isinstance(value, bool):
                        errors.append(f'Field {field} must be boolean')
                    elif field_type == 'array' and not isinstance(value, list):
                        errors.append(f'Field {field} must be array')
                    elif field_type == 'object' and not isinstance(value, dict):
                        errors.append(f'Field {field} must be object')

                    if 'minLength' in field_schema and isinstance(value, str):
                        if len(value) < field_schema['minLength']:
                            errors.append(f'Field {field} too short')
                    if 'maxLength' in field_schema and isinstance(value, str):
                        if len(value) > field_schema['maxLength']:
                            errors.append(f'Field {field} exceeds max length')

        except json.JSONDecodeError as e:
            if strict:
                errors.append(f'Invalid JSON: {str(e)}')
            else:
                warnings.append('Response is not valid JSON')

        return {'errors': errors, 'warnings': warnings}

    def _validate_format(self, content: str) -> dict:
        errors = []
        warnings = []

        if content.count('```') >= 2:
            if not re.search(r'```\w*\n', content):
                warnings.append('Code blocks may not be properly formatted')

        if len(content) > 100000:
            warnings.append('Response is very long, may contain irrelevant content')

        if re.search(r'(\w)\1{5,}', content):
            warnings.append('Possible repeated character pattern detected')

        return {'errors': errors, 'warnings': warnings}

    def _validate_length(
        self,
        content: str,
        usage: Any,
    ) -> dict:
        max_tokens = 4000
        if hasattr(usage, 'max_output_tokens'):
            max_tokens = usage.max_output_tokens

        if hasattr(usage, 'completion_tokens'):
            if usage.completion_tokens > max_tokens:
                return {'valid': False, 'message': f'Output exceeded max tokens ({max_tokens})'}

        return {'valid': True}

    def validate_with_pydantic(
        self,
        content: str,
        model_class: type[BaseModel],
    ) -> tuple[bool, Optional[BaseModel], list[str]]:
        errors = []

        try:
            data = json.loads(content)
            validated = model_class.model_validate(data)
            return True, validated, []
        except json.JSONDecodeError as e:
            errors.append(f'Invalid JSON: {str(e)}')
            return False, None, errors
        except ValidationError as e:
            for err in e.errors():
                errors.append(f'{err["loc"]}: {err["msg"]}')
            return False, None, errors


class HallucinationDetector:
    def __init__(self, ai_service=None):
        self._ai_service = ai_service
        self._fact_cache: dict[str, bool] = {}

    async def detect(
        self,
        content: str,
        context: Optional[dict] = None,
        reference_facts: Optional[list[str]] = None,
    ) -> HallucinationResult:
        issues = []
        confirmed = []
        contradicted = []

        fact_density = self._check_fact_density(content)
        if fact_density > 0.3:
            issues.append(f'High fact density: {fact_density:.1%} of content appears factual')

        specificity_score = self._check_specificity(content)
        if specificity_score > 0.8:
            issues.append('Very specific claims detected - verify accuracy')

        repetition_score = self._check_repetition(content)
        if repetition_score > 0.5:
            issues.append(f'High repetition detected: {repetition_score:.1%}')

        vagueness_score = self._check_vagueness(content)
        if vagueness_score > 0.6:
            issues.append('Vague or non-committal language detected')

        overconfidence_score = self._check_overconfidence(content)
        if overconfidence_score > 0.7:
            issues.append('Overconfident claims - may be hallucinated')

        if reference_facts:
            for fact in reference_facts:
                if self._verify_fact(fact, content):
                    confirmed.append(fact)
                elif self._contradict_fact(fact, content):
                    contradicted.append(fact)

        risk_score = len(issues) / 10 + (1 - specificity_score) / 5 + (1 - vagueness_score) / 10
        risk_score = min(1, max(0, risk_score))

        if risk_score > 0.7:
            risk_level = 'high'
        elif risk_score > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        confidence = 1 - risk_score

        recommendations = []
        if risk_level == 'high':
            recommendations.append('Verify all factual claims with external sources')
            recommendations.append('Consider using a more conservative model')
        if overconfidence_score > 0.5:
            recommendations.append('Add uncertainty hedging to factual statements')
        if len(contradicted) > 0:
            recommendations.append('Review contradicted facts - may indicate hallucination')

        return HallucinationResult(
            score=risk_score,
            risk_level=risk_level,
            detected_issues=issues,
            facts_confirmed=confirmed,
            facts_contradicted=contradicted,
            confidence=confidence,
            recommendations=recommendations,
        )

    def _check_fact_density(self, content: str) -> float:
        fact_patterns = [
            r'\d{4}',  # Years
            r'\d+%',   # Percentages
            r'\$[0-9,]+',  # Money
            r'\b(According to|Research shows|Studies indicate)\b',
            r'\b(proven|confirmed|verified)\b',
        ]

        fact_matches = 0
        total_sentences = content.count('.') + 1
        for pattern in fact_patterns:
            fact_matches += len(re.findall(pattern, content, re.IGNORECASE))

        return min(1, fact_matches / max(1, total_sentences))

    def _check_specificity(self, content: str) -> float:
        specific_indicators = [
            r'\b(exactly|precisely|specifically)\b',
            r'\b[A-Z][a-z]+ [A-Z][a-z]+',  # Named entities
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
        ]

        specific_count = 0
        for pattern in specific_indicators:
            specific_count += len(re.findall(pattern, content, re.IGNORECASE))

        return min(1, specific_count / 20)

    def _check_repetition(self, content: str) -> float:
        words = content.lower().split()
        if len(words) < 10:
            return 0

        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        if not word_freq:
            return 0

        max_freq = max(word_freq.values())
        repeated_words = sum(1 for f in word_freq.values() if f > 5)

        return min(1, repeated_words / len(word_freq))

    def _check_vagueness(self, content: str) -> float:
        vague_words = [
            r'\b(maybe|perhaps|might|could|possibly)\b',
            r'\b(some|several|many|few)\b',
            r'\b(thinks|believes|feels|assumes)\b',
            r'\b(may|seems|appears)\b',
        ]

        vague_count = 0
        words = content.split()
        for pattern in vague_words:
            vague_count += len(re.findall(pattern, content, re.IGNORECASE))

        return min(1, vague_count / max(1, len(words) / 20))

    def _check_overconfidence(self, content: str) -> float:
        overconfident_patterns = [
            r'\b(definitely|absolutely|certainly|obviously|clearly)\b',
            r'\b(always|never|all|none)\b',
            r'\b(proven|guaranteed|certain)\b',
            r'\b(fact|truth|reality)\b',
        ]

        overconfident_count = 0
        for pattern in overconfident_patterns:
            overconfident_count += len(re.findall(pattern, content, re.IGNORECASE))

        vague_score = self._check_vagueness(content)
        confidence_ratio = overconfident_count / max(1, vague_score * 10)

        return min(1, confidence_ratio / 5)

    def _verify_fact(self, fact: str, content: str) -> bool:
        return fact.lower() in content.lower()

    def _contradict_fact(self, fact: str, content: str) -> bool:
        negation_patterns = [
            r'not\s+' + re.escape(fact[:20]),
            r"doesn't\s+",
            r"won't\s+",
            r'never\s+',
        ]
        for pattern in negation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    def _is_in_cache(self, claim: str) -> Optional[bool]:
        return self._fact_cache.get(claim[:100])


class OutputSchemaValidator:
    @staticmethod
    def create_model_from_schema(schema: dict) -> type[BaseModel]:
        model_name = schema.get('title', 'DynamicModel')
        fields = {}

        for field_name, field_config in schema.get('properties', {}).items():
            field_type_str = field_config.get('type', 'string')

            if field_type_str == 'string':
                field_type = str
            elif field_type_str == 'number':
                field_type = float
            elif field_type_str == 'integer':
                field_type = int
            elif field_type_str == 'boolean':
                field_type = bool
            elif field_type_str == 'array':
                items_type = field_config.get('items', {}).get('type', 'string')
                if items_type == 'string':
                    field_type = list[str]
                elif items_type == 'number':
                    field_type = list[float]
                elif items_type == 'integer':
                    field_type = list[int]
                else:
                    field_type = list[Any]
            elif field_type_str == 'object':
                field_type = dict[str, Any]
            else:
                field_type = Any

            default = None
            if 'default' in field_config:
                default = field_config['default']

            fields[field_name] = (field_type, ... if field_config.get('required') else default)

        return create_model(model_name, **fields)

    @staticmethod
    def validate_json_output(content: str, schema: dict) -> tuple[bool, Optional[dict], list[str]]:
        errors = []

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return False, None, [f'Invalid JSON: {str(e)}']

        model_class = OutputSchemaValidator.create_model_from_schema(schema)

        try:
            validated = model_class.model_validate(data)
            return True, validated.model_dump(), []
        except ValidationError as e:
            for err in e.errors():
                location = '.'.join(str(l) for l in err['loc'])
                errors.append(f'{location}: {err["msg"]}')
            return False, data, errors