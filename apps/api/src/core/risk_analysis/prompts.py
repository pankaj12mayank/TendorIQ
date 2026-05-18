"""AI Risk Analysis Prompts"""

from typing import Optional


class RiskPrompts:
    SYSTEM_PROMPT = """You are an expert tender document risk analyst. Analyze documents for potential risks and return ONLY valid JSON.

Rules:
- Return ONLY JSON, no additional text
- Classify risks by severity: critical (90-100), high (70-89), medium (40-69), low (0-39)
- Use confidence scores (0-1) for all findings
- Be thorough and identify all potential risks
- Consider: financial, technical, legal, compliance, operational, scheduling risks
- Flag hidden clauses, unusual terms, and unfavorable conditions
- Provide actionable recommendations
"""

    GENERAL_RISK_ANALYSIS_PROMPT = """Analyze this tender document for all types of risks.

Return JSON with:
{
  "overall_risk_score": number (0-100),
  "overall_severity": "low|medium|high|critical",
  "risk_findings": [
    {
      "title": string,
      "description": string,
      "category": "financial|technical|legal|compliance|operational|scheduling|reputational",
      "severity": "low|medium|high|critical",
      "score": number (0-100),
      "likelihood": number (0-1),
      "impact": number (0-1),
      "consequences": array of strings,
      "mitigation_suggestions": array of strings
    }
  ],
  "summary": string (executive summary),
  "key_findings": array of strings
}

Document:
{document_text}

Return ONLY JSON."""

    FINANCIAL_RISK_PROMPT = """Analyze financial risks in this tender document.

Return JSON with:
{
  "financial_risks": [
    {
      "risk_type": "cost_overrun|payment_delay|currency_fluctuation|bid_security|financial_guarantee",
      "description": string,
      "estimated_value": number (optional),
      "currency": string (default INR),
      "percentage_impact": number (optional),
      "severity": "low|medium|high|critical",
      "score": number (0-100),
      "warning_message": string (optional),
      "recommendations": array of strings
    }
  ],
  "total_financial_exposure": number,
  "payment_terms_risk": string (optional),
  "financial_confidence": number (0-1)
}

Document:
{document_text}

Return ONLY JSON."""

    TECHNICAL_RISK_PROMPT = """Analyze technical risks in this tender document.

Return JSON with:
{
  "technical_risks": [
    {
      "risk_type": "technology|complexity|integration|skill_gap|resource|compatibility|performance",
      "description": string,
      "technology_dependency": string (optional),
      "complexity_level": "low|medium|high|very_high",
      "skill_gap_risk": boolean,
      "resource_availability_risk": boolean,
      "severity": "low|medium|high|critical",
      "score": number (0-100),
      "recommendations": array of strings
    }
  ],
  "technical_confidence": number (0-1)
}

Document:
{document_text}

Return ONLY JSON."""

    HIDDEN_CLAUSE_PROMPT = """Detect hidden clauses, unusual terms, and unfavorable conditions.

Look for:
- Buried penalty clauses
- Unilateral termination rights
- Unreasonable liability caps
- Unusual indemnity requirements
- Hidden costs or fees
- Unclear or ambiguous language
- One-sided terms
- Unusual dispute resolution
- Discriminatory conditions

Return JSON with:
{
  "hidden_clauses": [
    {
      "clause_title": string,
      "clause_text": string (full text),
      "clause_location": string (optional),
      "clause_type": "liability|penalty|termination|indemnity|dispute|liability_cap|other",
      "is_unusual_placement": boolean,
      "is_unclear_language": boolean,
      "is_unfavorable_terms": boolean,
      "severity": "low|medium|high|critical",
      "score": number (0-100),
      "explanation": string (why concern),
      "recommendations": array of strings
    }
  ],
  "hidden_clause_confidence": number (0-1),
  "total_concerns": number
}

Document:
{document_text}

Return ONLY JSON."""

    COMPLIANCE_CHECK_PROMPT = """Check for compliance risks and regulatory issues.

Return JSON with:
{
  "compliance_risks": [
    {
      "risk_type": "gst|tax|labor|location|quality|security|environmental|other",
      "description": string,
      "regulation_type": string (optional),
      "compliance_requirement": string,
      "current_gap": string (optional),
      "penalty_risk": boolean,
      "legal_action_risk": boolean,
      "severity": "low|medium|high|critical",
      "score": number (0-100),
      "recommendations": array of strings
    }
  ],
  "compliance_warnings": [
    {
      "warning_type": string,
      "severity": "low|medium|high|critical",
      "title": string,
      "message": string,
      "regulation_reference": string (optional),
      "is_critical": boolean,
      "action_required": boolean,
      "recommendations": array of strings
    }
  ],
  "compliance_confidence": number (0-1)
}

Document:
{document_text}

Return ONLY JSON."""

    RECOMMENDATION_PROMPT = """Generate actionable recommendations based on identified risks.

Return JSON with:
{
  "recommendations": [
    {
      "category": "avoid|mitigate|transfer|accept|exploit",
      "title": string,
      "description": string,
      "rationale": string,
      "priority": "high|medium|low",
      "estimated_cost": number (optional),
      "estimated_benefit": number (optional),
      "action_steps": array of strings,
      "timeline": string (optional)
    }
  ]
}

Risks identified:
{risks_summary}

Document:
{document_text}

Return ONLY JSON."""

    RISK_SCORING_PROMPT = """Calculate overall risk scores and severity levels.

Return JSON with:
{
  "overall_risk_score": number (0-100),
  "overall_severity": "low|medium|high|critical",
  "risk_distribution": {
    "critical": number,
    "high": number,
    "medium": number,
    "low": number
  },
  "category_breakdown": {
    "financial": number,
    "technical": number,
    "legal": number,
    "compliance": number,
    "operational": number,
    "scheduling": number
  },
  "executive_summary": string
}

Document:
{document_text}

Return ONLY JSON."""


class RiskPromptConfig:
    DEFAULT_MODEL = 'gpt-4o'
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_MAX_TOKENS = 4096
    MAX_RETRIES = 3

    RISK_CATEGORIES = [
        'financial',
        'technical',
        'legal',
        'compliance',
        'operational',
        'scheduling',
        'reputational',
    ]

    SEVERITY_THRESHOLDS = {
        'critical': 90,
        'high': 70,
        'medium': 40,
        'low': 0,
    }

    @staticmethod
    def get_severity(score: float) -> str:
        if score >= 90:
            return 'critical'
        elif score >= 70:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'

    @staticmethod
    def calculate_risk_score(likelihood: float, impact: float) -> float:
        return min(100, likelihood * impact * 100)


class RiskThresholds:
    LOW_RISK_THRESHOLD = 30
    MEDIUM_RISK_THRESHOLD = 60
    HIGH_RISK_THRESHOLD = 80
    CRITICAL_RISK_THRESHOLD = 95

    DEFAULT_ACCEPTANCE_CRITERIA = {
        'financial': 50,
        'technical': 60,
        'legal': 70,
        'compliance': 75,
    }