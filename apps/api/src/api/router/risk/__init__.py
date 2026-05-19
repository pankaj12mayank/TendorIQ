"""Risk Analysis API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ....core.risk_analysis import (
    RiskEngine,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    CompleteRiskAnalysis,
    get_risk_engine,
)


router = APIRouter(prefix='/risk', tags=['risk_analysis'])


class AnalyzeRequest(BaseModel):
    document_id: UUID
    document_text: str = Field(..., min_length=100)
    extraction_id: Optional[str] = None
    include_hidden_clause_detection: bool = True
    include_financial_analysis: bool = True
    include_technical_analysis: bool = True
    include_compliance_check: bool = True


class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: str
    overall_risk_score: float
    overall_severity: str
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    total_risks: int
    recommendations_count: int
    hidden_clauses_count: int
    financial_risks_count: int
    technical_risks_count: int
    compliance_risks_count: int
    analysis_time_ms: int
    confidence: float
    summary: Optional[str] = None
    key_findings: list[str]
    warnings: list[str]


@router.post('/analyze', response_model=AnalyzeResponse)
async def analyze_risks(
    request: AnalyzeRequest,
    engine: RiskEngine = Depends(get_risk_engine),
):
    try:
        analysis_req = RiskAnalysisRequest(
            document_id=request.document_id,
            document_text=request.document_text,
            extraction_id=request.extraction_id,
            include_hidden_clause_detection=request.include_hidden_clause_detection,
            include_financial_analysis=request.include_financial_analysis,
            include_technical_analysis=request.include_technical_analysis,
            include_compliance_check=request.include_compliance_check,
        )

        response = await engine.analyze(analysis_req)

        result = CompleteRiskAnalysis(
            analysis_id=response.analysis_id,
            document_id=request.document_id,
            status=response.status,
        )

        result.risks_detected = response.critical_risks + response.high_risks + 0 + 0
        result.critical_risks = response.critical_risks
        result.high_risks = response.high_risks
        result.overall_risk_score = response.overall_risk_score
        result.overall_severity = response.overall_severity

        visualization = engine.get_visualization_data(result)

        return AnalyzeResponse(
            analysis_id=response.analysis_id,
            status=response.status.value,
            overall_risk_score=response.overall_risk_score,
            overall_severity=response.overall_severity.value,
            critical_risks=response.critical_risks,
            high_risks=response.high_risks,
            medium_risks=result.medium_risks,
            low_risks=result.low_risks,
            total_risks=response.critical_risks + response.high_risks + result.medium_risks + result.low_risks,
            recommendations_count=response.recommendations_count,
            hidden_clauses_count=0,
            financial_risks_count=0,
            technical_risks_count=0,
            compliance_risks_count=0,
            analysis_time_ms=response.analysis_time_ms,
            confidence=response.confidence,
            summary=result.summary,
            key_findings=result.key_findings,
            warnings=result.warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/severity/levels')
async def get_severity_levels():
    return {
        'levels': [
            {'name': 'critical', 'min_score': 90, 'max_score': 100, 'color': '#dc2626'},
            {'name': 'high', 'min_score': 70, 'max_score': 89, 'color': '#f97316'},
            {'name': 'medium', 'min_score': 40, 'max_score': 69, 'color': '#eab308'},
            {'name': 'low', 'min_score': 0, 'max_score': 39, 'color': '#22c55e'},
        ]
    }


@router.get('/categories')
async def get_risk_categories():
    return {
        'categories': [
            {'name': 'financial', 'description': 'Financial and cost-related risks'},
            {'name': 'technical', 'description': 'Technology and implementation risks'},
            {'name': 'legal', 'description': 'Contractual and legal risks'},
            {'name': 'compliance', 'description': 'Regulatory and compliance risks'},
            {'name': 'operational', 'description': 'Operational and process risks'},
            {'name': 'scheduling', 'description': 'Timeline and scheduling risks'},
            {'name': 'reputational', 'description': 'Brand and reputation risks'},
        ]
    }


@router.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'risk_analysis'}