"""AI Proposal Generation Prompts"""

from typing import Optional


class ProposalPrompts:
    SYSTEM_PROMPT = """You are an expert proposal writer for tender submissions. Generate compelling, professional proposal sections.

Rules:
- Return ONLY valid JSON for content
- Use professional, formal language
- Be specific and data-driven
- Align content with tender requirements
- Highlight company strengths
- Follow standard proposal structure
"""

    EXECUTIVE_SUMMARY_PROMPT = """Generate an executive summary for this tender proposal.

The summary should:
- Be 150-300 words
- Highlight why this company is best suited
- Summarize the approach and key differentiators
- Address the client's core needs
- End with a strong value proposition

Return JSON:
{
  "title": string,
  "content": string (markdown format, 150-300 words),
  "key_points": array of strings (3-5 bullet points)
}

Tender Information:
{tender_info}

Company Profile:
{company_profile}

Return ONLY JSON."""

    COMPANY_PROFILE_PROMPT = """Generate company profile section for the proposal.

Incorporate:
- Company background and history
- Key achievements and certifications
- Relevant experience and past projects
- Team qualifications
- Values and differentiators

Return JSON:
{
  "title": string,
  "content": string (markdown, 300-500 words),
  "highlights": array of strings (key achievements)
}

Company Information:
{company_info}

Relevant Experience:
{experience}

Return ONLY JSON."""

    UNDERSTANDING_PROMPT = """Generate the Understanding of Requirements section.

Demonstrate:
- Clear understanding of client needs
- Interpretation of tender requirements
- Key challenges identified
- How the solution addresses these

Return JSON:
{
  "title": string,
  "content": string (markdown, 200-400 words),
  "key_requirements_addressed": array of strings
}

Tender Requirements:
{tender_requirements}

Return ONLY JSON."""

    APPROACH_PROMPT = """Generate the Technical/Implementation Approach section.

Cover:
- Proposed methodology
- Technical solution overview
- Implementation strategy
- Key phases and milestones
- Quality assurance approach

Return JSON:
{
  "title": string,
  "content": string (markdown, 400-600 words),
  "phases": array of objects with name, description, duration
}

Technical Requirements:
{technical_requirements}

Return ONLY JSON."""

    TEAM_PROMPT = """Generate the Team Composition section.

Include:
- Project manager and key personnel
- Their qualifications and experience
- Roles and responsibilities
- Organizational chart description

Return JSON:
{
  "title": string,
  "content": string (markdown, 200-400 words),
  "team_members": [
    {
      "name": string,
      "designation": string,
      "qualifications": array,
      "role": string,
      "experience_years": number
    }
  ]
}

Company Team:
{team_info}

Return ONLY JSON."""

    TIMELINE_PROMPT = """Generate the Project Timeline section.

Include:
- Work breakdown structure
- Phases and durations
- Key milestones and deliverables
- Gantt chart description (as markdown table)

Return JSON:
{
  "title": string,
  "content": string (markdown),
  "milestones": array of objects with name, date, description
}

Tender Timeline:
{tender_timeline}

Return ONLY JSON."""

    PRICING_PROMPT = """Generate the Pricing/Commercial section.

Structure:
- Price breakdown by item/category
- Payment schedule
- Validity period
- Terms and conditions

Return JSON:
{
  "title": string,
  "content": string (markdown),
  "pricing_summary": string,
  "payment_terms": string
}

Pricing Information:
{pricing_info}

Return ONLY JSON."""

    TERMS_PROMPT = """Generate the Terms and Conditions section.

Cover:
- Contract terms
- Warranty/guarantee
- Indemnities
- Dispute resolution
- Termination clauses

Return JSON:
{
  "title": string,
  "content": string (markdown),
  "key_terms": array of strings
}

Tender Terms:
{tender_terms}

Return ONLY JSON."""

    FULL_PROPOSAL_PROMPT = """Generate a complete tender proposal with all sections.

Sections to include:
- Executive Summary
- Company Profile
- Understanding of Requirements
- Technical Approach
- Team Composition
- Timeline
- Pricing

Return JSON:
{
  "title": string,
  "sections": [
    {
      "section_type": string,
      "title": string,
      "content": string (markdown),
      "order": number
    }
  ],
  "total_words": number,
  "estimated_pages": number
}

Tender Information:
{tender_text}

Company Information:
{company_info}

Return ONLY JSON."""


class ProposalConfig:
    DEFAULT_MODEL = 'gpt-4o'
    DEFAULT_TEMPERATURE = 0.6
    MAX_TOKENS = 4096
    MAX_RETRIES = 2

    DEFAULT_SECTION_ORDER = [
        {'type': 'cover', 'title': 'Cover Page', 'required': False},
        {'type': 'table_of_contents', 'title': 'Table of Contents', 'required': False},
        {'type': 'executive_summary', 'title': 'Executive Summary', 'required': True},
        {'type': 'company_profile', 'title': 'Company Profile', 'required': True},
        {'type': 'understanding', 'title': 'Understanding of Requirements', 'required': True},
        {'type': 'approach', 'title': 'Technical Approach', 'required': True},
        {'type': 'methodology', 'title': 'Methodology', 'required': True},
        {'type': 'team', 'title': 'Team Composition', 'required': True},
        {'type': 'timeline', 'title': 'Project Timeline', 'required': True},
        {'type': 'pricing', 'title': 'Pricing', 'required': True},
        {'type': 'terms', 'title': 'Terms and Conditions', 'required': True},
        {'type': 'appendices', 'title': 'Appendices', 'required': False},
    ]

    CONTENT_STYLES = {
        'professional': 'Use formal, professional language suitable for government/corporate tenders.',
        'concise': 'Be brief and to the point while covering all requirements.',
        'detailed': 'Provide comprehensive coverage with examples and data.',
        'persuasive': 'Focus on value proposition and competitive advantages.',
    }

    WORD_COUNT_TARGETS = {
        'executive_summary': (150, 300),
        'company_profile': (300, 500),
        'understanding': (200, 400),
        'approach': (400, 600),
        'methodology': (300, 500),
        'team': (200, 400),
        'timeline': (150, 300),
        'pricing': (100, 200),
        'terms': (150, 300),
    }