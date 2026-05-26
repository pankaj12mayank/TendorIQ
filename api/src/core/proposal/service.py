"""Proposal Generation Engine"""

import json
import logging
import time
from datetime import datetime
from typing import Optional, Any, List
from uuid import UUID, uuid4

from ..ai import AIService, ProviderType
from .schemas import (
    ProposalStatus,
    SectionType,
    ProposalSection,
    CompanyProfile,
    CompanyIntelligence,
    ProposalDraft,
    ProposalPricing,
    ProposalGenerationRequest,
    ProposalGenerationResponse,
    SectionUpdateRequest,
    RegenerationRequest,
    ProposalExportFormat,
)
from .prompts import ProposalPrompts, ProposalConfig


logger = logging.getLogger(__name__)


class ProposalParseError(Exception):
    pass


class ContentValidator:
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


class SectionGenerator:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def generate_section(
        self,
        section_type: SectionType,
        tender_text: str,
        company_info: str,
        style: str = 'professional',
    ) -> dict:
        if not self._ai_service:
            return {'title': '', 'content': '', 'order': 0}

        prompts = {
            SectionType.EXECUTIVE_SUMMARY: ProposalPrompts.EXECUTIVE_SUMMARY_PROMPT,
            SectionType.COMPANY_PROFILE: ProposalPrompts.COMPANY_PROFILE_PROMPT,
            SectionType.UNDERSTANDING: ProposalPrompts.UNDERSTANDING_PROMPT,
            SectionType.APPROACH: ProposalPrompts.APPROACH_PROMPT,
            SectionType.TEAM: ProposalPrompts.TEAM_PROMPT,
            SectionType.TIMELINE: ProposalPrompts.TIMELINE_PROMPT,
            SectionType.PRICING: ProposalPrompts.PRICING_PROMPT,
            SectionType.TERMS: ProposalPrompts.TERMS_PROMPT,
        }

        prompt_template = prompts.get(section_type)
        if not prompt_template:
            return {'title': '', 'content': '', 'order': 0}

        messages = [
            {'role': 'system', 'content': ProposalPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt_template.format(
                tender_info=tender_text[:5000],
                company_profile=company_info[:2000],
                tender_requirements=tender_text[:5000],
                technical_requirements=tender_text[:5000],
                tender_timeline=tender_text[:3000],
                tender_terms=tender_text[:3000],
                company_info=company_info[:2000],
                experience='',
                team_info=company_info[:2000],
                pricing_info=tender_text[:2000],
            )},
        ]

        try:
            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=ProposalConfig.DEFAULT_MODEL,
                temperature=0.6,
                max_tokens=4096,
            )

            data = ContentValidator.fix_json_response(response.content)
            return data

        except Exception as e:
            logger.error(f'Section generation failed for {section_type}: {e}')
            return {'title': '', 'content': '', 'order': 0}


class ProposalEngine:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service
        self._section_generator = SectionGenerator(ai_service)
        self._proposals: dict[str, ProposalDraft] = {}

    async def generate(
        self,
        request: ProposalGenerationRequest,
    ) -> ProposalGenerationResponse:
        start_time = time.time()
        proposal_id = str(uuid4())
        warnings: list[str] = []

        proposal = ProposalDraft(
            proposal_id=proposal_id,
            tender_id=request.tender_id,
            document_id=request.document_id,
            title=request.title or 'Tender Proposal',
            status=ProposalStatus.GENERATING,
        )

        company_info = self._get_company_info(request.company_intelligence_id)

        sections_to_generate = [
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.COMPANY_PROFILE,
            SectionType.UNDERSTANDING,
            SectionType.APPROACH,
            SectionType.TEAM,
            SectionType.TIMELINE,
        ]

        generated_count = 0
        total_words = 0

        for section_type in sections_to_generate:
            try:
                section_data = await self._section_generator.generate_section(
                    section_type=section_type,
                    tender_text=request.document_text,
                    company_info=company_info,
                    style=request.style,
                )

                section = ProposalSection(
                    section_type=section_type,
                    title=section_data.get('title', section_type.value.replace('_', ' ').title()),
                    content=section_data.get('content', ''),
                    order=len(proposal.sections),
                    is_generated=True,
                    word_count=len(section_data.get('content', '').split()),
                )
                section.word_count = len(section.content.split())
                proposal.sections.append(section)

                generated_count += 1
                total_words += section.word_count

            except Exception as e:
                logger.warning(f'Failed to generate section {section_type}: {e}')
                warnings.append(f'Failed to generate {section_type.value}')

        proposal.status = ProposalStatus.COMPLETED
        proposal.total_words = total_words
        proposal.estimated_pages = max(1, total_words // 300)

        proposal.updated_at = datetime.utcnow()
        self._proposals[proposal_id] = proposal

        return ProposalGenerationResponse(
            proposal_id=proposal_id,
            status=proposal.status,
            title=proposal.title,
            sections_generated=generated_count,
            total_words=total_words,
            generation_time_ms=int((time.time() - start_time) * 1000),
            confidence=0.85 if generated_count > 4 else 0.6,
            warnings=warnings,
        )

    def _get_company_info(self, intelligence_id: Optional[str]) -> str:
        return """Company with extensive experience in tender submissions.
        ISO certified, established 2010, 500+ employees.
        Successfully completed 200+ projects.""" + (
            f" Intelligence ID: {intelligence_id}" if intelligence_id else ""
        )

    def get_proposal(self, proposal_id: str) -> Optional[ProposalDraft]:
        return self._proposals.get(proposal_id)

    def update_section(
        self,
        proposal_id: str,
        section_id: str,
        content: str,
        edited_by: Optional[str] = None,
    ) -> Optional[ProposalDraft]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        for section in proposal.sections:
            if section.section_id == section_id:
                section.content = content
                section.is_edited = True
                section.last_modified = datetime.utcnow()
                section.modified_by = edited_by
                section.word_count = len(content.split())
                section.version += 1
                break

        proposal.updated_at = datetime.utcnow()
        return proposal

    async def regenerate_section(
        self,
        proposal_id: str,
        section_id: str,
        request: RegenerationRequest,
    ) -> Optional[ProposalSection]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        section = None
        for s in proposal.sections:
            if s.section_id == section_id:
                section = s
                break

        if not section:
            return None

        old_content = section.content if request.keep_existing_content else ''

        section_data = await self._section_generator.generate_section(
            section_type=section.section_type,
            tender_text=old_content,
            company_info='',
            style=request.style,
        )

        section.content = section_data.get('content', section.content)
        section.is_generated = True
        section.last_modified = datetime.utcnow()
        section.version += 1
        section.word_count = len(section.content.split())

        proposal.updated_at = datetime.utcnow()
        return section

    def get_section(self, proposal_id: str, section_id: str) -> Optional[ProposalSection]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        for section in proposal.sections:
            if section.section_id == section_id:
                return section

        return None

    def add_section(
        self,
        proposal_id: str,
        section_type: SectionType,
        title: str,
        content: str = '',
    ) -> Optional[ProposalSection]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        section = ProposalSection(
            section_type=section_type,
            title=title,
            content=content,
            order=len(proposal.sections),
        )
        section.word_count = len(content.split())
        proposal.sections.append(section)
        proposal.updated_at = datetime.utcnow()

        return section

    def delete_section(self, proposal_id: str, section_id: str) -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        original_length = len(proposal.sections)
        proposal.sections = [s for s in proposal.sections if s.section_id != section_id]
        proposal.updated_at = datetime.utcnow()

        return len(proposal.sections) < original_length

    def reorder_sections(self, proposal_id: str, section_ids: List[str]) -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        section_map = {s.section_id: s for s in proposal.sections}
        proposal.sections = []

        for i, section_id in enumerate(section_ids):
            if section_id in section_map:
                section = section_map[section_id]
                section.order = i
                proposal.sections.append(section)

        proposal.updated_at = datetime.utcnow()
        return True

    def duplicate_section(self, proposal_id: str, section_id: str) -> Optional[ProposalSection]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        original = None
        for section in proposal.sections:
            if section.section_id == section_id:
                original = section
                break

        if not original:
            return None

        new_section = ProposalSection(
            section_type=original.section_type,
            title=f"{original.title} (Copy)",
            content=original.content,
            order=len(proposal.sections),
            editable=original.editable,
            required_for_submission=original.required_for_submission,
        )
        new_section.word_count = original.word_count

        proposal.sections.append(new_section)
        proposal.updated_at = datetime.utcnow()

        return new_section

    def get_proposal_summary(self, proposal_id: str) -> dict:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {}

        total_words = sum(s.word_count for s in proposal.sections)
        generated_sections = sum(1 for s in proposal.sections if s.is_generated)
        edited_sections = sum(1 for s in proposal.sections if s.is_edited)

        return {
            'proposal_id': proposal_id,
            'title': proposal.title,
            'status': proposal.status.value,
            'total_sections': len(proposal.sections),
            'generated_sections': generated_sections,
            'edited_sections': edited_sections,
            'total_words': total_words,
            'estimated_pages': max(1, total_words // 300),
            'completion_percentage': round((generated_sections / max(1, len(ProposalConfig.DEFAULT_SECTION_ORDER))) * 100, 1),
        }


class CompanyIntelligenceManager:
    def __init__(self):
        self._profiles: dict[str, CompanyIntelligence] = {}

    def create_profile(self, profile: CompanyProfile) -> str:
        intelligence = CompanyIntelligence(
            company_profile=profile,
        )
        self._profiles[intelligence.intelligence_id] = intelligence
        return intelligence.intelligence_id

    def get_profile(self, intelligence_id: str) -> Optional[CompanyIntelligence]:
        return self._profiles.get(intelligence_id)

    def update_profile(self, intelligence_id: str, updates: dict) -> bool:
        intelligence = self._profiles.get(intelligence_id)
        if not intelligence:
            return False

        if 'company_profile' in updates and updates['company_profile']:
            if isinstance(updates['company_profile'], dict):
                intelligence.company_profile = CompanyProfile(**updates['company_profile'])
            else:
                intelligence.company_profile = updates['company_profile']

        if 'team_members' in updates:
            intelligence.team_members = updates['team_members']

        if 'past_projects' in updates:
            intelligence.past_projects = updates['past_projects']

        intelligence.updated_at = datetime.utcnow()
        return True

    def add_team_member(self, intelligence_id: str, member: dict) -> bool:
        intelligence = self._profiles.get(intelligence_id)
        if not intelligence:
            return False

        from .schemas import TeamMember
        team_member = TeamMember(**member)
        intelligence.team_members.append(team_member)
        intelligence.updated_at = datetime.utcnow()
        return True

    def add_project(self, intelligence_id: str, project: dict) -> bool:
        intelligence = self._profiles.get(intelligence_id)
        if not intelligence:
            return False

        from .schemas import ExperienceProject
        exp_project = ExperienceProject(**project)
        intelligence.past_projects.append(exp_project)
        intelligence.updated_at = datetime.utcnow()
        return True

    def get_intelligence_summary(self, intelligence_id: str) -> dict:
        intelligence = self._profiles.get(intelligence_id)
        if not intelligence:
            return {}

        return {
            'intelligence_id': intelligence_id,
            'company_name': intelligence.company_profile.company_name if intelligence.company_profile else 'Unknown',
            'team_count': len(intelligence.team_members),
            'project_count': len(intelligence.past_projects),
            'updated_at': intelligence.updated_at.isoformat(),
        }


class ProposalExporter:
    def __init__(self, proposal: ProposalDraft):
        self._proposal = proposal

    def to_markdown(self) -> str:
        md = f"# {self._proposal.title}\n\n"
        md += f"**Status:** {self._proposal.status.value}\n"
        md += f"**Version:** {self._proposal.version}\n"
        md += f"**Generated:** {self._proposal.created_at.strftime('%Y-%m-%d')}\n\n"
        md += "---\n\n"

        for section in sorted(self._proposal.sections, key=lambda s: s.order):
            md += f"## {section.title}\n\n"
            md += f"{section.content}\n\n"

        return md

    def to_html(self) -> str:
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self._proposal.title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; }}
        h1 {{ color: #1a365d; border-bottom: 3px solid #3182ce; padding-bottom: 10px; }}
        h2 {{ color: #2c5282; margin-top: 30px; }}
        .metadata {{ color: #718096; font-size: 14px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .word-count {{ color: #a0aec0; font-size: 12px; }}
        @media print {{ body {{ padding: 20px; }} }}
    </style>
</head>
<body>
    <h1>{self._proposal.title}</h1>
    <div class="metadata">
        Status: {self._proposal.status.value} | Version: {self._proposal.version}
    </div>
"""

        for section in sorted(self._proposal.sections, key=lambda s: s.order):
            html += f"""
    <div class="section">
        <h2>{section.title}</h2>
        <div>{section.content.replace(chr(10), '<br>')}</div>
        <div class="word-count">{section.word_count} words</div>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def to_json(self) -> str:
        return json.dumps(self._proposal.model_dump(), indent=2, default=str)

    def to_summary(self) -> dict:
        return {
            'proposal_id': self._proposal.proposal_id,
            'title': self._proposal.title,
            'status': self._proposal.status.value,
            'sections': [
                {'title': s.title, 'type': s.section_type.value, 'words': s.word_count}
                for s in self._proposal.sections
            ],
            'total_words': self._proposal.total_words,
            'estimated_pages': self._proposal.estimated_pages,
        }


proposal_engine = ProposalEngine()
company_intelligence_manager = CompanyIntelligenceManager()


def get_proposal_engine() -> ProposalEngine:
    return proposal_engine


def get_company_intelligence_manager() -> CompanyIntelligenceManager:
    return company_intelligence_manager