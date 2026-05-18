"""AI Risk Analysis Engine"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from ..ai import AIService, ProviderType, AIResponse
from .schemas import (
    RiskStatus,
    SeverityLevel,
    RiskCategory,
    RiskFinding,
    FinancialRisk,
    TechnicalRisk,
    ComplianceRisk,
    HiddenClauseFinding,
    ComplianceWarning,
    Recommendation,
    CompleteRiskAnalysis,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    RiskVisualizationData,
)
from .prompts import RiskPrompts, RiskPromptConfig, RiskThresholds


logger = logging.getLogger(__name__)


class RiskParseError(Exception):
    pass


class RiskValidator:
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
                return json.loads(raw_response[start_idx:end_idx + 1])
        except:
            pass

        return {}


class HiddenClauseDetector:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def detect(self, document_text: str) -> list[HiddenClauseFinding]:
        if not self._ai_service:
            logger.warning('AI service not configured for hidden clause detection')
            return []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.HIDDEN_CLAUSE_PROMPT.format(document_text=document_text[:8000])},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = RiskValidator.fix_json_response(response.content)
            clauses = data.get('hidden_clauses', [])

            findings = []
            for clause in clauses:
                try:
                    finding = HiddenClauseFinding(
                        clause_title=clause.get('clause_title', 'Unknown Clause'),
                        clause_text=clause.get('clause_text', ''),
                        clause_location=clause.get('clause_location'),
                        clause_type=clause.get('clause_type', 'other'),
                        is_unusual_placement=clause.get('is_unusual_placement', False),
                        is_unclear_language=clause.get('is_unclear_language', False),
                        is_unfavorable_terms=clause.get('is_unfavorable_terms', False),
                        severity=SeverityLevel(clause.get('severity', 'medium')),
                        score=clause.get('score', 50),
                        confidence=clause.get('confidence', 0.5),
                        explanation=clause.get('explanation', ''),
                        recommendations=clause.get('recommendations', []),
                    )
                    findings.append(finding)
                except Exception as e:
                    logger.warning(f'Failed to parse hidden clause: {e}')

            return findings

        except Exception as e:
            logger.error(f'Hidden clause detection failed: {e}')
            return []


class FinancialRiskDetector:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def detect(self, document_text: str) -> list[FinancialRisk]:
        if not self._ai_service:
            return []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.FINANCIAL_RISK_PROMPT.format(document_text=document_text[:8000])},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = RiskValidator.fix_json_response(response.content)
            risks = data.get('financial_risks', [])

            findings = []
            for risk in risks:
                try:
                    finding = FinancialRisk(
                        risk_type=risk.get('risk_type', 'unknown'),
                        description=risk.get('description', ''),
                        estimated_value=risk.get('estimated_value'),
                        currency=risk.get('currency', 'INR'),
                        percentage_impact=risk.get('percentage_impact'),
                        cost_overrun_risk='cost_overrun' in risk.get('risk_type', '').lower(),
                        payment_delay_risk='payment' in risk.get('risk_type', '').lower(),
                        severity=SeverityLevel(risk.get('severity', 'medium')),
                        score=risk.get('score', 50),
                        confidence=risk.get('financial_confidence', 0.5),
                        warning_message=risk.get('warning_message'),
                        recommendations=risk.get('recommendations', []),
                    )
                    findings.append(finding)
                except Exception as e:
                    logger.warning(f'Failed to parse financial risk: {e}')

            return findings

        except Exception as e:
            logger.error(f'Financial risk detection failed: {e}')
            return []


class TechnicalRiskDetector:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def detect(self, document_text: str) -> list[TechnicalRisk]:
        if not self._ai_service:
            return []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.TECHNICAL_RISK_PROMPT.format(document_text=document_text[:8000])},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = RiskValidator.fix_json_response(response.content)
            risks = data.get('technical_risks', [])

            findings = []
            for risk in risks:
                try:
                    finding = TechnicalRisk(
                        risk_type=risk.get('risk_type', 'unknown'),
                        technology_dependency=risk.get('technology_dependency'),
                        complexity_level=risk.get('complexity_level', 'medium'),
                        integration_risk=risk.get('integration_risk', False),
                        skill_gap_risk=risk.get('skill_gap_risk', False),
                        resource_availability_risk=risk.get('resource_availability_risk', False),
                        compatibility_risk=risk.get('compatibility_risk', False),
                        performance_risk=risk.get('performance_risk', False),
                        severity=SeverityLevel(risk.get('severity', 'medium')),
                        score=risk.get('score', 50),
                        confidence=risk.get('technical_confidence', 0.5),
                        recommendations=risk.get('recommendations', []),
                    )
                    findings.append(finding)
                except Exception as e:
                    logger.warning(f'Failed to parse technical risk: {e}')

            return findings

        except Exception as e:
            logger.error(f'Technical risk detection failed: {e}')
            return []


class ComplianceRiskDetector:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def detect(self, document_text: str) -> tuple[list[ComplianceRisk], list[ComplianceWarning]]:
        if not self._ai_service:
            return [], []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.COMPLIANCE_CHECK_PROMPT.format(document_text=document_text[:8000])},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = RiskValidator.fix_json_response(response.content)

            risks = []
            for risk in data.get('compliance_risks', []):
                try:
                    finding = ComplianceRisk(
                        risk_type=risk.get('risk_type', 'unknown'),
                        compliance_requirement=risk.get('compliance_requirement', ''),
                        regulation_type=risk.get('regulation_type'),
                        current_gap=risk.get('current_gap'),
                        penalty_risk=risk.get('penalty_risk', False),
                        legal_action_risk=risk.get('legal_action_risk', False),
                        severity=SeverityLevel(risk.get('severity', 'medium')),
                        score=risk.get('score', 50),
                        confidence=risk.get('compliance_confidence', 0.5),
                        recommendations=risk.get('recommendations', []),
                    )
                    risks.append(finding)
                except Exception as e:
                    logger.warning(f'Failed to parse compliance risk: {e}')

            warnings = []
            for warning in data.get('compliance_warnings', []):
                try:
                    w = ComplianceWarning(
                        warning_type=warning.get('warning_type', 'general'),
                        severity=SeverityLevel(warning.get('severity', 'medium')),
                        title=warning.get('title', ''),
                        message=warning.get('message', ''),
                        description=warning.get('message', ''),
                        regulation_reference=warning.get('regulation_reference'),
                        is_critical=warning.get('is_critical', False),
                        action_required=warning.get('action_required', True),
                        recommendations=warning.get('recommendations', []),
                        confidence=warning.get('compliance_confidence', 0.5),
                    )
                    warnings.append(w)
                except Exception as e:
                    logger.warning(f'Failed to parse compliance warning: {e}')

            return risks, warnings

        except Exception as e:
            logger.error(f'Compliance risk detection failed: {e}')
            return [], []


class RiskEngine:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service
        self._hidden_clause_detector = HiddenClauseDetector(ai_service)
        self._financial_detector = FinancialRiskDetector(ai_service)
        self._technical_detector = TechnicalRiskDetector(ai_service)
        self._compliance_detector = ComplianceRiskDetector(ai_service)

    async def analyze(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        start_time = time.time()
        analysis_id = str(uuid4())
        errors: list[str] = []

        result = CompleteRiskAnalysis(
            analysis_id=analysis_id,
            document_id=request.document_id,
            extraction_id=request.extraction_id,
            status=RiskStatus.ANALYZING,
        )

        try:
            if request.include_hidden_clause_detection:
                hidden_clauses = await self._hidden_clause_detector.detect(request.document_text)
                result.hidden_clauses = hidden_clauses

            if request.include_financial_analysis:
                financial_risks = await self._financial_detector.detect(request.document_text)
                result.financial_risks = financial_risks

            if request.include_technical_analysis:
                technical_risks = await self._technical_detector.detect(request.document_text)
                result.technical_risks = technical_risks

            if request.include_compliance_check:
                compliance_risks, warnings = await self._compliance_detector.detect(request.document_text)
                result.compliance_risks = compliance_risks
                result.compliance_warnings = warnings

            all_findings = await self._extract_general_risks(request.document_text)
            result.risk_findings = all_findings

            result.recommendations = await self._generate_recommendations(
                request.document_text,
                self._summarize_risks(result),
            )

            self._calculate_overall_scores(result)

            result.status = RiskStatus.DETECTED
            result.analyzed_at = datetime.utcnow()

            critical_count = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.CRITICAL)
            high_count = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.HIGH)

            critical_count += sum(1 for h in result.hidden_clauses if h.severity == SeverityLevel.CRITICAL)
            high_count += sum(1 for h in result.hidden_clauses if h.severity == SeverityLevel.HIGH)

        except Exception as e:
            logger.error(f'Risk analysis failed: {e}')
            errors.append(str(e))
            result.status = RiskStatus.PENDING
            result.warnings.append(f'Analysis error: {str(e)}')

        processing_time = int((time.time() - start_time) * 1000)

        return RiskAnalysisResponse(
            analysis_id=analysis_id,
            status=result.status,
            overall_risk_score=result.overall_risk_score,
            overall_severity=result.overall_severity,
            critical_risks=result.critical_risks,
            high_risks=result.high_risks,
            recommendations_count=len(result.recommendations),
            analysis_time_ms=processing_time,
            confidence=result.overall_confidence,
            errors=errors,
        )

    async def _extract_general_risks(self, document_text: str) -> list[RiskFinding]:
        if not self._ai_service:
            return []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.GENERAL_RISK_ANALYSIS_PROMPT.format(document_text=document_text[:8000])},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = RiskValidator.fix_json_response(response.content)
            findings = []

            for risk in data.get('risk_findings', []):
                try:
                    finding = RiskFinding(
                        title=risk.get('title', 'Unknown Risk'),
                        description=risk.get('description', ''),
                        category=RiskCategory(risk.get('category', 'operational')),
                        severity=SeverityLevel(risk.get('severity', 'medium')),
                        score=risk.get('score', 50),
                        likelihood=risk.get('likelihood', 0.5),
                        impact=risk.get('impact', 0.5),
                        overall_score=risk.get('score', 50),
                        consequences=risk.get('consequences', []),
                        mitigation_suggestions=risk.get('mitigation_suggestions', []),
                        confidence=risk.get('confidence', 0.5),
                        detection_method='ai_general_risk_analysis',
                    )
                    findings.append(finding)
                except Exception as e:
                    logger.warning(f'Failed to parse risk finding: {e}')

            result.summary = data.get('summary')
            result.key_findings = data.get('key_findings', [])

            return findings

        except Exception as e:
            logger.error(f'General risk extraction failed: {e}')
            return []

    async def _generate_recommendations(self, document_text: str, risks_summary: str) -> list[Recommendation]:
        if not self._ai_service:
            return []

        messages = [
            {'role': 'system', 'content': RiskPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': RiskPrompts.RECOMMENDATION_PROMPT.format(
                risks_summary=risks_summary,
                document_text=document_text[:8000]
            )},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=RiskPromptConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=2048,
            )

            data = RiskValidator.fix_json_response(response.content)
            recommendations = []

            for rec in data.get('recommendations', []):
                try:
                    recommendation = Recommendation(
                        category=rec.get('category', 'mitigate'),
                        title=rec.get('title', 'Unknown Recommendation'),
                        description=rec.get('description', ''),
                        rationale=rec.get('rationale', ''),
                        priority=rec.get('priority', 'medium'),
                        estimated_cost=rec.get('estimated_cost'),
                        estimated_benefit=rec.get('estimated_benefit'),
                        action_steps=rec.get('action_steps', []),
                        timeline=rec.get('timeline'),
                        confidence=rec.get('confidence', 0.5),
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.warning(f'Failed to parse recommendation: {e}')

            return recommendations

        except Exception as e:
            logger.error(f'Recommendation generation failed: {e}')
            return []

    def _summarize_risks(self, result: CompleteRiskAnalysis) -> str:
        summaries = []
        summaries.append(f'Total risks: {len(result.risk_findings)}')
        summaries.append(f'Critical: {result.critical_risks}, High: {result.high_risks}')
        summaries.append(f'Hidden clauses: {len(result.hidden_clauses)}')
        summaries.append(f'Financial risks: {len(result.financial_risks)}')
        return '; '.join(summaries)

    def _calculate_overall_scores(self, result: CompleteRiskAnalysis) -> None:
        all_scores = []

        for finding in result.risk_findings:
            all_scores.append(finding.score)

        for risk in result.financial_risks:
            all_scores.append(risk.score)

        for risk in result.technical_risks:
            all_scores.append(risk.score)

        for risk in result.compliance_risks:
            all_scores.append(risk.score)

        for clause in result.hidden_clauses:
            all_scores.append(clause.score)

        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            result.overall_risk_score = (avg_score * 0.4 + max_score * 0.6)
        else:
            result.overall_risk_score = 0

        result.overall_severity = SeverityLevel(RiskPromptConfig.get_severity(result.overall_risk_score))
        result.overall_confidence = 0.7

        result.critical_risks = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.CRITICAL)
        result.high_risks = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.HIGH)
        result.medium_risks = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.MEDIUM)
        result.low_risks = sum(1 for r in result.risk_findings if r.severity == SeverityLevel.LOW)

        result.critical_risks += sum(1 for h in result.hidden_clauses if h.severity == SeverityLevel.CRITICAL)
        result.high_risks += sum(1 for h in result.hidden_clauses if h.severity == SeverityLevel.HIGH)

        result.risks_detected = len(result.risk_findings) + len(result.hidden_clauses)

        result.risk_distribution = {
            'critical': result.critical_risks,
            'high': result.high_risks,
            'medium': result.medium_risks,
            'low': result.low_risks,
        }

        result.category_breakdown = {
            'financial': len(result.financial_risks),
            'technical': len(result.technical_risks),
            'legal': sum(1 for c in result.hidden_clauses),
            'compliance': len(result.compliance_risks),
        }

    def get_visualization_data(self, result: CompleteRiskAnalysis) -> RiskVisualizationData:
        return RiskVisualizationData(
            risk_score_gauge=result.overall_risk_score,
            severity_distribution=result.risk_distribution,
            category_breakdown=result.category_breakdown,
            timeline_risks=[],
            risk_heatmap=[],
            recommendation_priority=[
                {'priority': r.priority, 'title': r.title, 'category': r.category}
                for r in result.recommendations
            ],
        )


risk_engine = RiskEngine()


def get_risk_engine() -> RiskEngine:
    return risk_engine