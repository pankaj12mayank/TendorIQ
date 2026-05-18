"""Proposal Generation API Router"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...core.proposal import (
    ProposalEngine,
    SectionType,
    ProposalDraft,
    ProposalGenerationRequest,
    SectionUpdateRequest,
    RegenerationRequest,
    get_proposal_engine,
)


router = APIRouter(prefix='/proposal', tags=['proposal'])


class GenerateProposalRequest(BaseModel):
    tender_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    document_text: str = Field(..., min_length=100)
    company_intelligence_id: Optional[str] = None
    title: Optional[str] = None
    style: str = 'professional'
    tone: str = 'formal'
    length: str = 'medium'


class UpdateSectionRequest(BaseModel):
    section_id: str
    content: str
    edited_by: Optional[str] = None


class RegenerateSectionRequest(BaseModel):
    section_id: str
    keep_existing_content: bool = False
    style: str = 'professional'


class AddSectionRequest(BaseModel):
    section_type: str
    title: str
    content: str = ''


class CreateIntelligenceRequest(BaseModel):
    company_name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    services: List[str] = []
    certifications: List[str] = []
    key_clients: List[str] = []


@router.post('/generate')
async def generate_proposal(
    request: GenerateProposalRequest,
    engine: ProposalEngine = Depends(get_proposal_engine),
):
    try:
        gen_request = ProposalGenerationRequest(
            tender_id=request.tender_id,
            document_id=request.document_id,
            document_text=request.document_text,
            company_intelligence_id=request.company_intelligence_id,
            title=request.title,
            style=request.style,
            tone=request.tone,
            length=request.length,
        )
        return await engine.generate(gen_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{proposal_id}')
async def get_proposal(proposal_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    proposal = engine.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return proposal.model_dump()


@router.get('/{proposal_id}/summary')
async def get_proposal_summary(proposal_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    summary = engine.get_proposal_summary(proposal_id)
    if not summary:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return summary


@router.get('/{proposal_id}/sections')
async def get_sections(proposal_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    proposal = engine.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return {'sections': [s.model_dump() for s in proposal.sections]}


@router.get('/{proposal_id}/sections/{section_id}')
async def get_section(proposal_id: str, section_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    section = engine.get_section(proposal_id, section_id)
    if not section:
        raise HTTPException(status_code=404, detail='Section not found')
    return section.model_dump()


@router.patch('/{proposal_id}/sections/{section_id}')
async def update_section(
    proposal_id: str,
    section_id: str,
    request: UpdateSectionRequest,
    engine: ProposalEngine = Depends(get_proposal_engine),
):
    proposal = engine.update_section(proposal_id, section_id, request.content, request.edited_by)
    if not proposal:
        raise HTTPException(status_code=404, detail='Proposal or section not found')
    return {'success': True, 'section_id': section_id}


@router.post('/{proposal_id}/sections/{section_id}/regenerate')
async def regenerate_section(
    proposal_id: str,
    section_id: str,
    request: RegenerateSectionRequest,
    engine: ProposalEngine = Depends(get_proposal_engine),
):
    try:
        regen_request = RegenerationRequest(
            section_id=section_id,
            keep_existing_content=request.keep_existing_content,
            style=request.style,
        )
        section = await engine.regenerate_section(proposal_id, section_id, regen_request)
        if not section:
            raise HTTPException(status_code=404, detail='Proposal or section not found')
        return section.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/{proposal_id}/sections')
async def add_section(
    proposal_id: str,
    request: AddSectionRequest,
    engine: ProposalEngine = Depends(get_proposal_engine),
):
    section_type = SectionType(request.section_type)
    section = engine.add_section(proposal_id, section_type, request.title, request.content)
    if not section:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return section.model_dump()


@router.delete('/{proposal_id}/sections/{section_id}')
async def delete_section(proposal_id: str, section_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    success = engine.delete_section(proposal_id, section_id)
    if not success:
        raise HTTPException(status_code=404, detail='Proposal or section not found')
    return {'success': True}


@router.post('/{proposal_id}/sections/reorder')
async def reorder_sections(proposal_id: str, section_ids: List[str], engine: ProposalEngine = Depends(get_proposal_engine)):
    success = engine.reorder_sections(proposal_id, section_ids)
    if not success:
        raise HTTPException(status_code=404, detail='Proposal not found')
    return {'success': True}


@router.post('/{proposal_id}/sections/{section_id}/duplicate')
async def duplicate_section(proposal_id: str, section_id: str, engine: ProposalEngine = Depends(get_proposal_engine)):
    section = engine.duplicate_section(proposal_id, section_id)
    if not section:
        raise HTTPException(status_code=404, detail='Proposal or section not found')
    return section.model_dump()


@router.post('/{proposal_id}/export')
async def export_proposal(proposal_id: str, format: str = 'markdown', engine: ProposalEngine = Depends(get_proposal_engine)):
    proposal = engine.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail='Proposal not found')

    from ...core.proposal.service import ProposalExporter
    exporter = ProposalExporter(proposal)

    if format == 'markdown':
        return Response(content=exporter.to_markdown().encode(), media_type='text/markdown')
    elif format == 'html':
        return Response(content=exporter.to_html().encode(), media_type='text/html')
    elif format == 'json':
        return Response(content=exporter.to_json().encode(), media_type='application/json')
    else:
        raise HTTPException(status_code=400, detail=f'Unsupported format: {format}')


@router.get('/intelligence/{intelligence_id}')
async def get_intelligence(intelligence_id: str):
    from ...core.proposal.service import get_company_intelligence_manager
    manager = get_company_intelligence_manager()
    intelligence = manager.get_profile(intelligence_id)
    if not intelligence:
        raise HTTPException(status_code=404, detail='Company intelligence not found')
    return intelligence.model_dump()


@router.post('/intelligence')
async def create_intelligence(request: CreateIntelligenceRequest):
    from ...core.proposal.schemas import CompanyProfile
    from ...core.proposal.service import get_company_intelligence_manager

    manager = get_company_intelligence_manager()
    profile = CompanyProfile(
        company_name=request.company_name,
        tagline=request.tagline,
        description=request.description,
        founded_year=request.founded_year,
        headquarters=request.headquarters,
        services=request.services,
        certifications=request.certifications,
        key_clients=request.key_clients,
    )
    intelligence_id = manager.create_profile(profile)
    return {'intelligence_id': intelligence_id}


@router.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'proposal'}