"""Risk Analysis Schemas and Models"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class RiskCategory(str, Enum):
    FINANCIAL = 'financial'
    TECHNICAL = 'technical'
    LEGAL = 'legal'
    COMPLIANCE = 'compliance'
    OPERATIONAL = 'operational'
    SCHEDULING = 'scheduling'
    REPUTATIONAL = 'reputational'
    HIDDEN_CLAUSE = 'hidden_clause'


class RiskStatus(str, Enum):
    PENDING = 'pending'
    ANALYZING = 'analyzing'
    DETECTED = 'detected'
    MITIGATED = 'mitigated'
    ACCEPTED = 'accepted'
    DISMISSED = 'dismissed'


class RiskSource(str, Enum):
    TENDER_DOCUMENT = 'tender_document'
    CONTRACT = 'contract'
    CLAUSE = 'clause'
    ELIGIBILITY = 'eligibility'
    TECHNICAL_SPEC = 'technical_spec'
    FINANCIAL_TERM = 'financial_term'
    DEADLINE = 'deadline'


class RiskIndicator(BaseModel):
    indicator_type: str = Field(..., description="Type of risk indicator")
    value: str = Field(..., description="Indicator value/finding")
    evidence: Optional[str] = Field(None, description="Evidence from document")
    location: Optional[str] = Field(None, description="Document location (page/paragraph)")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Indicator confidence")


class RiskFinding(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Risk finding title")
    description: str = Field(..., description="Detailed description")
    category: RiskCategory = Field(..., description="Risk category")
    severity: SeverityLevel = Field(..., description="Severity level")
    score: float = Field(default=0.0, ge=0, le=100, description="Numerical risk score 0-100")

    source: Optional[RiskSource] = Field(None, description="Source of risk")
    source_location: Optional[str] = Field(None, description="Document location")
    source_text: Optional[str] = Field(None, description="Original text")

    indicators: list[RiskIndicator] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list, description="Potential consequences")
    affected_parties: list[str] = Field(default_factory=list, description="Affected stakeholders")

    likelihood: float = Field(default=0.0, ge=0, le=1, description="Probability of occurrence")
    impact: float = Field(default=0.0, ge=0, le=1, description="Impact if occurs")
    overall_score: float = Field(default=0.0, ge=0, le=100)

    is_hidden: bool = Field(default=False, description="Hidden clause flag")
    is_mandatory_disclosure: bool = Field(default=False, description="Requires disclosure")
    requires_attention: bool = Field(default=True)

    mitigation_suggestions: list[str] = Field(default_factory=list)
    preventive_measures: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)

    confidence: float = Field(default=0.0, ge=0, le=1)
    detection_method: Optional[str] = Field(None, description="How it was detected")
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class FinancialRisk(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid4()))
    risk_type: str = Field(..., description="Type of financial risk")
    description: str = Field(..., description="Risk description")

    estimated_value: Optional[float] = Field(None, description="Estimated financial impact")
    currency: str = Field(default="INR")
    percentage_impact: Optional[float] = Field(None, description="Percentage impact on contract value")

    cost_overrun_risk: bool = Field(default=False)
    payment_delay_risk: bool = Field(default=False)
    currency_fluctuation_risk: bool = Field(default=False)
    liquidity_risk: bool = Field(default=False)
    inflation_risk: bool = Field(default=False)

    severity: SeverityLevel = SeverityLevel.MEDIUM
    score: float = Field(default=0.0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0, le=1)

    warning_message: Optional[str] = Field(None)
    recommendations: list[str] = Field(default_factory=list)


class TechnicalRisk(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid4()))
    risk_type: str = Field(..., description="Type of technical risk")

    technology_dependency: Optional[str] = Field(None, description="Technology involved")
    complexity_level: str = Field(default="medium")
    integration_risk: bool = Field(default=False)

    skill_gap_risk: bool = Field(default=False)
    resource_availability_risk: bool = Field(default=False)
    compatibility_risk: bool = Field(default=False)
    performance_risk: bool = Field(default=False)

    severity: SeverityLevel = SeverityLevel.MEDIUM
    score: float = Field(default=0.0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0, le=1)

    recommendations: list[str] = Field(default_factory=list)


class ComplianceRisk(BaseModel):
    risk_id: str = Field(default_factory=lambda: str(uuid4()))
    risk_type: str = Field(..., description="Type of compliance risk")

    regulation_type: Optional[str] = Field(None, description="Applicable regulation")
    compliance_requirement: str = Field(..., description="What must be complied with")
    current_gap: Optional[str] = Field(None, description="Current compliance gap")

    penalty_risk: bool = Field(default=False)
    legal_action_risk: bool = Field(default=False)
    certification_risk: bool = Field(default=False)

    severity: SeverityLevel = SeverityLevel.MEDIUM
    score: float = Field(default=0.0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0, le=1)

    recommendations: list[str] = Field(default_factory=list)


class HiddenClauseFinding(BaseModel):
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    clause_title: str = Field(..., description="Hidden clause title")
    clause_text: str = Field(..., description="Full clause text")
    clause_location: Optional[str] = Field(None, description="Page/section reference")

    clause_type: str = Field(..., description="Type: liability, penalty, termination, etc.")
    is_unusual_placement: bool = Field(default=False, description="Unusual placement")
    is_unclear_language: bool = Field(default=False, description="Ambiguous language")
    is_unfavorable_terms: bool = Field(default=False, description="One-sided terms")

    severity: SeverityLevel = SeverityLevel.HIGH
    score: float = Field(default=0.0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0, le=1)

    explanation: str = Field(..., description="Why this is a concern")
    recommendations: list[str] = Field(default_factory=list)


class ComplianceWarning(BaseModel):
    warning_id: str = Field(default_factory=lambda: str(uuid4()))
    warning_type: str = Field(..., description="Type of warning")
    severity: SeverityLevel = Field(..., description="Warning severity")

    title: str = Field(..., description="Warning title")
    message: str = Field(..., description="Warning message")
    description: str = Field(..., description="Detailed description")

    regulation_reference: Optional[str] = Field(None, description="Applicable regulation")
    requirement: Optional[str] = Field(None, description="What's required")

    is_critical: bool = Field(default=False)
    deadline: Optional[datetime] = Field(None, description="Action deadline")
    action_required: bool = Field(default=True)

    recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class Recommendation(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    category: str = Field(..., description="Recommendation category")

    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    rationale: str = Field(..., description="Why this is recommended")

    priority: str = Field(default="medium", description="high, medium, low")
    estimated_cost: Optional[float] = Field(None)
    estimated_benefit: Optional[float] = Field(None)

    associated_risks: list[str] = Field(default_factory=list)
    action_steps: list[str] = Field(default_factory=list)
    timeline: Optional[str] = Field(None, description="Implementation timeline")

    confidence: float = Field(default=0.0, ge=0, le=1)


class CompleteRiskAnalysis(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: Optional[UUID] = None
    extraction_id: Optional[str] = None

    status: RiskStatus = RiskStatus.PENDING
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    overall_confidence: float = Field(default=0.0, ge=0, le=1)

    overall_risk_score: float = Field(default=0.0, ge=0, le=100)
    overall_severity: SeverityLevel = SeverityLevel.LOW

    risks_detected: int = 0
    critical_risks: int = 0
    high_risks: int = 0
    medium_risks: int = 0
    low_risks: int = 0

    risk_findings: list[RiskFinding] = Field(default_factory=list)
    financial_risks: list[FinancialRisk] = Field(default_factory=list)
    technical_risks: list[TechnicalRisk] = Field(default_factory=list)
    compliance_risks: list[ComplianceRisk] = Field(default_factory=list)
    hidden_clauses: list[HiddenClauseFinding] = Field(default_factory=list)

    compliance_warnings: list[ComplianceWarning] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    risk_distribution: dict[str, int] = Field(default_factory=dict)
    category_breakdown: dict[str, int] = Field(default_factory=dict)

    summary: Optional[str] = Field(None, description="Executive summary")
    key_findings: list[str] = Field(default_factory=list, description="Top 5-10 key findings")

    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskAnalysisRequest(BaseModel):
    document_id: UUID
    document_text: str = Field(..., min_length=100)
    extraction_id: Optional[str] = None
    include_hidden_clause_detection: bool = Field(default=True)
    include_financial_analysis: bool = Field(default=True)
    include_technical_analysis: bool = Field(default=True)
    include_compliance_check: bool = Field(default=True)
    tenant_id: Optional[UUID] = None


class RiskAnalysisResponse(BaseModel):
    analysis_id: str
    status: RiskStatus
    overall_risk_score: float
    overall_severity: SeverityLevel
    critical_risks: int
    high_risks: int
    recommendations_count: int
    analysis_time_ms: int
    confidence: float
    errors: list[str] = Field(default_factory=list)


class RiskVisualizationData(BaseModel):
    risk_score_gauge: float = Field(ge=0, le=100)
    severity_distribution: dict[str, int]
    category_breakdown: dict[str, float]
    timeline_risks: list[dict]
    risk_heatmap: list[dict]
    recommendation_priority: list[dict]