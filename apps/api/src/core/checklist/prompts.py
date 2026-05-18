"""AI Compliance Checklist Generation Prompts"""

from typing import Optional


class ChecklistPrompts:
    SYSTEM_PROMPT = """You are an expert tender compliance analyst. Generate comprehensive compliance checklists from tender documents.

Rules:
- Return ONLY valid JSON
- Extract ALL mandatory documents requirements
- Identify optional but recommended documents
- Generate realistic preparation steps
- Consider deadline constraints
- Flag critical missing items
"""

    CHECKLIST_GENERATION_PROMPT = """Generate a compliance checklist for this tender document.

Extract and organize:
1. Required documents (mandatory)
2. Optional but recommended documents
3. Registration and certification requirements
4. Financial document requirements
5. Technical document requirements
6. Submission steps in order

Return JSON:
{
  "name": string (checklist name),
  "description": string,
  "sections": [
    {
      "name": string,
      "description": string,
      "order": number,
      "items": [
        {
          "name": string,
          "description": string,
          "document_type": "certificate|registration|license|declaration|financial_document|technical_document|experience_proof|identity_proof|other",
          "is_mandatory": boolean,
          "is_waivable": boolean,
          "due_date": string (YYYY-MM-DD, optional),
          "estimated_time_minutes": number,
          "category": string,
          "order": number
        }
      ]
    }
  ],
  "submission_steps": [
    {
      "name": string,
      "description": string,
      "order": number,
      "instructions": array of strings,
      "required_document_types": array of strings,
      "estimated_duration_minutes": number
    }
  ],
  "mandatory_items_count": number,
  "optional_items_count": number,
  "estimated_total_time_hours": number
}

Document:
{document_text}

Return ONLY JSON."""

    MISSING_ITEMS_DETECTION_PROMPT = """Analyze this tender checklist and identify missing or incomplete items.

For each section, identify:
- Items that might be missing
- Items that need clarification
- Deadline-related risks
- Common requirements often overlooked

Return JSON:
{
  "missing_items": [
    {
      "item_name": string,
      "category": string,
      "priority": "high|medium|low",
      "severity": "critical|high|medium|low",
      "impact": string,
      "action_required": string,
      "suggested_deadline": string (YYYY-MM-DD, optional)
    }
  ],
  "warnings": array of strings,
  "suggestions": array of strings
}

Checklist items:
{checklist_items}

Document:
{document_text}

Return ONLY JSON."""

    SUBMISSION_STEPS_PROMPT = """Generate a step-by-step submission guide for this tender.

Consider:
- Document collection phase
- Document preparation phase
- Review and verification phase
- Final submission phase

Return JSON:
{
  "steps": [
    {
      "name": string,
      "description": string,
      "order": number,
      "instructions": array of strings,
      "estimated_duration_minutes": number,
      "depends_on_previous": boolean
    }
  ],
  "total_estimated_time_hours": number
}

Document:
{document_text}

Return ONLY JSON."""

    COMPLIANCE_SCORING_PROMPT = """Calculate compliance score for this checklist.

Consider:
- Mandatory items completed
- Deadline adherence
- Document quality
- Overall readiness

Return JSON:
{
  "total_items": number,
  "completed_items": number,
  "missing_items": number,
  "overall_score": number (0-100),
  "compliance_percentage": number (0-100),
  "readiness_percentage": number (0-100),
  "risk_level": "low|medium|high|critical",
  "submission_probability": number (0-100)
}

Checklist:
{checklist_json}

Document:
{document_text}

Return ONLY JSON."""


class ChecklistConfig:
    DEFAULT_MODEL = 'gpt-4o-mini'
    DEFAULT_TEMPERATURE = 0.2
    MAX_RETRIES = 3

    DEFAULT_SECTIONS = [
        {'name': 'Identity & Registration', 'order': 1},
        {'name': 'Financial Documents', 'order': 2},
        {'name': 'Technical Documents', 'order': 3},
        {'name': 'Experience & Certifications', 'order': 4},
        {'name': 'Declarations & Affidavits', 'order': 5},
        {'name': 'Legal Documents', 'order': 6},
        {'name': 'Quality Certifications', 'order': 7},
    ]

    DEFAULT_DOCUMENT_TYPES = [
        {'type': 'certificate', 'description': 'Certificates and attestations'},
        {'type': 'registration', 'description': 'Registration documents'},
        {'type': 'license', 'description': 'Licenses and permits'},
        {'type': 'declaration', 'description': 'Declarations and affidavits'},
        {'type': 'financial_document', 'description': 'Financial statements and proofs'},
        {'type': 'technical_document', 'description': 'Technical specifications and capabilities'},
        {'type': 'experience_proof', 'description': 'Work experience and project references'},
        {'type': 'identity_proof', 'description': 'Identity and authorization documents'},
    ]

    DEFAULT_STEPS = [
        {'name': 'Document Collection', 'description': 'Collect all required documents', 'order': 1},
        {'name': 'Document Verification', 'description': 'Verify documents are complete and valid', 'order': 2},
        {'name': 'Document Preparation', 'description': 'Prepare certified copies if needed', 'order': 3},
        {'name': 'Form Filling', 'description': 'Complete all required forms', 'order': 4},
        {'name': 'Review & Sign', 'description': 'Review all documents and sign where required', 'order': 5},
        {'name': 'Final Submission', 'description': 'Submit the complete bid', 'order': 6},
    ]