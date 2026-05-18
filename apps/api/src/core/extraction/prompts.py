"""AI Extraction Prompts for Tender Documents"""

from typing import Optional


class ExtractionPrompts:
    SYSTEM_PROMPT = """You are an expert tender document analyzer. Extract structured information from tender documents and return ONLY valid JSON.
    
    Rules:
    - Return ONLY JSON, no additional text
    - Extract all information accurately
    - If information is not found, use null or empty array
    - Use confidence scores (0-1) for extracted fields
    - Be precise and detailed
    - Date formats: YYYY-MM-DD
    - Currency: Use standard codes (INR, USD, EUR)
    """

    TENDER_SUMMARY_PROMPT = """Extract tender summary information from the document.

    Return JSON with these fields:
    - title: string (full tender title)
    - reference_number: string (tender ID/reference number)
    - description: string (brief description)
    - organization: string (issuing organization)
    - department: string (optional)
    - category: string (optional)
    - type: string (open/limited/other)
    - summary_confidence: float (0-1)

    Document:
    {document_text}

    Return ONLY JSON."""

    ELIGIBILITY_PROMPT = """Extract eligibility criteria from the tender document.

    Return JSON with:
    - criteria: array of strings (list all eligibility conditions)
    - min_experience_years: number (optional)
    - required_certifications: array of strings
    - required_registrations: array of strings (GST, PAN, etc.)
    - exclusions: array of strings (disqualification conditions)
    - eligibility_confidence: float (0-1)

    Document:
    {document_text}

    Return ONLY JSON."""

    TECHNICAL_REQUIREMENTS_PROMPT = """Extract all technical requirements from the tender.

    Return JSON with:
    {
      "requirements": [
        {
          "specification_id": string (optional),
          "description": string (requirement description),
          "quantity": string (optional),
          "standards": array of strings (required standards),
          "specifications": object (detailed specs)
        }
      ],
      "total_requirements": number,
      "technical_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    FINANCIAL_REQUIREMENTS_PROMPT = """Extract financial requirements from the tender.

    Return JSON with:
    {
      "items": [
        {
          "item_description": string,
          "estimated_value": number (optional),
          "currency": string (default INR),
          "budget_range": string (optional),
          "payment_terms": string (optional)
        }
      ],
      "total_value": number (optional),
      "currency": string,
      "has_bid_security": boolean,
      "bid_security_amount": number (optional),
      "financial_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    DEADLINES_PROMPT = """Extract all deadlines from the tender document.

    Return JSON with:
    {
      "deadlines": [
        {
          "type": string (submission/pre-bid/clarification/other),
          "date": string (YYYY-MM-DD format, null if not found),
          "time": string (HH:MM format, optional),
          "datetime": string (ISO format, optional),
          "description": string (optional),
          "is_hard_deadline": boolean,
          "days_remaining": number (calculated from today, optional)
        }
      ],
      "submission_deadline": object (main submission deadline),
      "earliest_deadline": string (YYYY-MM-DD),
      "total_deadlines": number,
      "deadlines_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    MANDATORY_DOCUMENTS_PROMPT = """Extract mandatory documents list from tender.

    Return JSON with:
    {
      "documents": [
        {
          "document_name": string,
          "document_type": string (optional),
          "is_mandatory": boolean,
          "submission_method": string (optional),
          "copies_required": number (optional),
          "attestation_required": boolean
        }
      ],
      "total_mandatory": number,
      "total_optional": number,
      "documents_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    CLAUSES_PROMPT = """Extract important clauses from the tender document.

    Return JSON with:
    {
      "clauses": [
        {
          "clause_id": string (optional, clause reference),
          "title": string (optional),
          "category": string (legal/payment/penalty/dispute/termination/other),
          "content": string (full clause text),
          "is_critical": boolean,
          "penalty_clause": boolean,
          "dispute_resolution": string (optional)
        }
      ],
      "total_clauses": number,
      "critical_count": number,
      "clauses_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    CONTRACT_TERMS_PROMPT = """Extract contract terms from tender.

    Return JSON with:
    {
      "contract_duration": string (e.g., "12 months", "2 years"),
      "renewal_options": string (optional),
      "termination_clause": string (optional),
      "warranty_period": string (optional),
      "performance_guarantee": number (optional),
      "terms_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    AWARD_CRITERIA_PROMPT = """Extract award/evaluation criteria from tender.

    Return JSON with:
    {
      "criteria": [
        {
          "criteria_name": string,
          "weightage": number (percentage, 0-100),
          "description": string (optional),
          "is_primary": boolean
        }
      ],
      "total_criteria": number,
      "evaluation_method": string (L1/lowest bid/quality/cost),
      "award_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    CONTACT_INFO_PROMPT = """Extract contact information from tender.

    Return JSON with:
    {
      "contact_person": string (optional),
      "designation": string (optional),
      "department": string (optional),
      "phone": string (optional),
      "email": string (optional),
      "address": string (optional),
      "website": string (optional)
    }

    Document:
    {document_text}

    Return ONLY JSON."""

    SUBMISSION_GUIDELINES_PROMPT = """Extract submission guidelines.

    Return JSON with:
    {
      "method": string (online/offline/both),
      "format_required": array of strings (pdf/doc/xlsx),
      "language": string (default English),
      "number_of_copies": number (optional),
      "size_limits": string (optional),
      "guidelines_confidence": float (0-1)
    }

    Document:
    {document_text}

    Return ONLY JSON."""


class PromptTemplates:
    @staticmethod
    def get_prompt(extraction_type: str, document_text: str) -> str:
        prompts = {
            'summary': ExtractionPrompts.TENDER_SUMMARY_PROMPT,
            'eligibility': ExtractionPrompts.ELIGIBILITY_PROMPT,
            'technical': ExtractionPrompts.TECHNICAL_REQUIREMENTS_PROMPT,
            'financial': ExtractionPrompts.FINANCIAL_REQUIREMENTS_PROMPT,
            'deadlines': ExtractionPrompts.DEADLINES_PROMPT,
            'documents': ExtractionPrompts.MANDATORY_DOCUMENTS_PROMPT,
            'clauses': ExtractionPrompts.CLAUSES_PROMPT,
            'contract': ExtractionPrompts.CONTRACT_TERMS_PROMPT,
            'award': ExtractionPrompts.AWARD_CRITERIA_PROMPT,
            'contact': ExtractionPrompts.CONTACT_INFO_PROMPT,
            'submission': ExtractionPrompts.SUBMISSION_GUIDELINES_PROMPT,
        }

        template = prompts.get(extraction_type, ExtractionPrompts.TENDER_SUMMARY_PROMPT)
        return template.format(document_text=document_text)

    @staticmethod
    def get_system_prompt() -> str:
        return ExtractionPrompts.SYSTEM_PROMPT

    @staticmethod
    def get_all_prompts() -> dict[str, str]:
        return {
            'summary': ExtractionPrompts.TENDER_SUMMARY_PROMPT,
            'eligibility': ExtractionPrompts.ELIGIBILITY_PROMPT,
            'technical': ExtractionPrompts.TECHNICAL_REQUIREMENTS_PROMPT,
            'financial': ExtractionPrompts.FINANCIAL_REQUIREMENTS_PROMPT,
            'deadlines': ExtractionPrompts.DEADLINES_PROMPT,
            'documents': ExtractionPrompts.MANDATORY_DOCUMENTS_PROMPT,
            'clauses': ExtractionPrompts.CLAUSES_PROMPT,
            'contract': ExtractionPrompts.CONTRACT_TERMS_PROMPT,
            'award': ExtractionPrompts.AWARD_CRITERIA_PROMPT,
            'contact': ExtractionPrompts.CONTACT_INFO_PROMPT,
            'submission': ExtractionPrompts.SUBMISSION_GUIDELINES_PROMPT,
        }


class ExtractionConfig:
    DEFAULT_MODEL = 'gpt-4o-mini'
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 2048
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 5]

    EXTRACTION_ORDER = [
        'summary',
        'deadlines',
        'eligibility',
        'technical',
        'financial',
        'documents',
        'clauses',
        'contract',
        'award',
        'contact',
        'submission',
    ]

    CRITICAL_EXTRACTIONS = ['summary', 'deadlines', 'eligibility']