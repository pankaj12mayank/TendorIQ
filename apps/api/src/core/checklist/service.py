"""Compliance Checklist Engine Service"""

import json
import logging
import time
from datetime import datetime, date, timedelta
from typing import Optional, Any, List
from uuid import UUID, uuid4

from pydantic import ValidationError

from ..ai import AIService, ProviderType, AIResponse
from .schemas import (
    ChecklistStatus,
    DocumentStatus,
    DocumentType,
    ChecklistItem,
    ChecklistSection,
    SubmissionStep,
    ComplianceScore,
    MissingItemAlert,
    ChecklistExportConfig,
    ChecklistExportFormat,
    CompleteChecklist,
    ChecklistGenerationRequest,
    ChecklistGenerationResponse,
    ChecklistUpdateRequest,
)
from .prompts import ChecklistPrompts, ChecklistConfig


logger = logging.getLogger(__name__)


class ChecklistParseError(Exception):
    pass


class ChecklistValidator:
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


class ChecklistEngine:
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service

    async def generate(self, request: ChecklistGenerationRequest) -> ChecklistGenerationResponse:
        start_time = time.time()
        checklist_id = str(uuid4())
        warnings: list[str] = []

        try:
            messages = [
                {'role': 'system', 'content': ChecklistPrompts.SYSTEM_PROMPT},
                {'role': 'user', 'content': ChecklistPrompts.CHECKLIST_GENERATION_PROMPT.format(document_text=request.document_text[:10000])},
            ]

            response = await self._ai_service.complete(
                messages=messages,
                provider=ProviderType.OPENAI,
                model=ChecklistConfig.DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=4096,
            )

            data = ChecklistValidator.fix_json_response(response.content)

            mandatory_count = 0
            optional_count = 0
            total_time_minutes = 0

            for section in data.get('sections', []):
                for item in section.get('items', []):
                    if item.get('is_mandatory', True):
                        mandatory_count += 1
                    else:
                        optional_count += 1
                    total_time_minutes += item.get('estimated_time_minutes', 30)

            estimated_hours = total_time_minutes / 60

            return ChecklistGenerationResponse(
                checklist_id=checklist_id,
                status=ChecklistStatus.PENDING,
                name=data.get('name', 'Tender Compliance Checklist'),
                total_items=mandatory_count + optional_count,
                mandatory_items=mandatory_count,
                optional_items=optional_count,
                estimated_time_hours=round(estimated_hours, 1),
                generation_time_ms=int((time.time() - start_time) * 1000),
                confidence=0.85,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f'Checklist generation failed: {e}')
            return ChecklistGenerationResponse(
                checklist_id=checklist_id,
                status=ChecklistStatus.PENDING,
                name='Tender Compliance Checklist',
                total_items=0,
                mandatory_items=0,
                optional_items=0,
                estimated_time_hours=0,
                generation_time_ms=int((time.time() - start_time) * 1000),
                confidence=0,
                warnings=[str(e)],
            )

    async def get_full_checklist(
        self,
        document_text: str,
        document_id: Optional[UUID] = None,
    ) -> CompleteChecklist:
        messages = [
            {'role': 'system', 'content': ChecklistPrompts.SYSTEM_PROMPT},
            {'role': 'user', 'content': ChecklistPrompts.CHECKLIST_GENERATION_PROMPT.format(document_text=document_text[:10000])},
        ]

        response = await self._ai_service.complete(
            messages=messages,
            provider=ProviderType.OPENAI,
            model=ChecklistConfig.DEFAULT_MODEL,
            temperature=0.1,
            max_tokens=4096,
        )

        data = ChecklistValidator.fix_json_response(response.content)

        checklist = CompleteChecklist(
            checklist_id=str(uuid4()),
            document_id=document_id,
            name=data.get('name', 'Tender Compliance Checklist'),
            description=data.get('description'),
            status=ChecklistStatus.PENDING,
        )

        sections = []
        total_items = 0
        mandatory_items = 0
        optional_items = 0

        for section_data in data.get('sections', []):
            items = []
            for item_data in section_data.get('items', []):
                item = ChecklistItem(
                    name=item_data.get('name', ''),
                    description=item_data.get('description'),
                    document_type=DocumentType(item_data.get('document_type', 'other')),
                    is_mandatory=item_data.get('is_mandatory', True),
                    is_waivable=item_data.get('is_waivable', False),
                    due_date=item_data.get('due_date'),
                    estimated_time_minutes=item_data.get('estimated_time_minutes', 30),
                    category=item_data.get('category'),
                    order=item_data.get('order', 0),
                )
                items.append(item)
                total_items += 1
                if item.is_mandatory:
                    mandatory_items += 1
                else:
                    optional_items += 1

            section = ChecklistSection(
                name=section_data.get('name', ''),
                description=section_data.get('description'),
                order=section_data.get('order', 0),
                items=items,
                mandatory_count=sum(1 for i in items if i.is_mandatory),
                optional_count=sum(1 for i in items if not i.is_mandatory),
            )
            sections.append(section)

        checklist.sections = sections
        checklist.total_items = total_items
        checklist.mandatory_items = mandatory_items
        checklist.optional_items = optional_items

        steps = []
        for step_data in data.get('submission_steps', []):
            step = SubmissionStep(
                name=step_data.get('name', ''),
                description=step_data.get('description'),
                order=step_data.get('order', 0),
                instructions=step_data.get('instructions', []),
                required_documents=step_data.get('required_document_types', []),
                estimated_duration_minutes=step_data.get('estimated_duration_minutes', 60),
            )
            steps.append(step)

        checklist.submission_steps = sorted(steps, key=lambda s: s.order)

        checklist.score = self._calculate_score(checklist)

        return checklist

    def _calculate_score(self, checklist: CompleteChecklist) -> ComplianceScore:
        total_items = checklist.total_items
        completed = sum(
            1 for section in checklist.sections
            for item in section.items
            if item.status == DocumentStatus.SUBMITTED or item.is_submitted
        )

        mandatory_completed = sum(
            1 for section in checklist.sections
            for item in section.items
            if item.is_mandatory and (item.status == DocumentStatus.SUBMITTED or item.is_submitted)
        )

        pending = total_items - completed
        missing = sum(
            1 for section in checklist.sections
            for item in section.items
            if item.is_mandatory and item.status == DocumentStatus.NOT_STARTED
        )

        overall_score = (completed / total_items * 100) if total_items > 0 else 0
        mandatory_score = (mandatory_completed / checklist.mandatory_items * 100) if checklist.mandatory_items > 0 else 0

        risk_level = 'low'
        if missing > checklist.mandatory_items * 0.3:
            risk_level = 'high'
        elif missing > checklist.mandatory_items * 0.1:
            risk_level = 'medium'

        submission_probability = mandatory_score

        return ComplianceScore(
            total_items=total_items,
            mandatory_items=checklist.mandatory_items,
            completed_items=completed,
            pending_items=pending,
            missing_items=missing,
            mandatory_completed=mandatory_completed,
            mandatory_pending=checklist.mandatory_items - mandatory_completed,
            overall_score=round(overall_score, 2),
            mandatory_score=round(mandatory_score, 2),
            optional_score=round((completed - mandatory_completed) / max(1, checklist.optional_items) * 100, 2),
            compliance_percentage=round(mandatory_score, 2),
            readiness_percentage=round(overall_score, 2),
            risk_level=risk_level,
            submission_probability=round(submission_probability, 2),
        )

    def update_item(
        self,
        checklist: CompleteChecklist,
        item_id: str,
        updates: ChecklistUpdateRequest,
    ) -> CompleteChecklist:
        for section in checklist.sections:
            for item in section.items:
                if item.item_id == item_id:
                    if updates.status:
                        item.status = updates.status
                    if updates.is_submitted is not None:
                        item.is_submitted = updates.is_submitted
                    if updates.notes:
                        item.notes = updates.notes
                    if updates.rejection_reason:
                        item.rejection_reason = updates.rejection_reason

                    if item.is_submitted or item.status == DocumentStatus.SUBMITTED:
                        item.progress_percent = 100
                        item.status = DocumentStatus.SUBMITTED
                    elif item.status == DocumentStatus.COLLECTING:
                        item.progress_percent = 50
                    elif item.status == DocumentStatus.PREPARING:
                        item.progress_percent = 75

                    break

        checklist.score = self._calculate_score(checklist)
        checklist.updated_at = datetime.utcnow()

        completed = sum(
            s.completed_count for s in checklist.sections
        )
        total = sum(
            len(s.items) for s in checklist.sections
        )
        checklist.completion_percentage = (completed / total * 100) if total > 0 else 0
        checklist.overall_progress = checklist.completion_percentage

        return checklist

    def get_missing_items(self, checklist: CompleteChecklist) -> List[MissingItemAlert]:
        alerts = []

        for section in checklist.sections:
            for item in section.items:
                if item.is_mandatory and item.status == DocumentStatus.NOT_STARTED:
                    days_left = None
                    if item.due_date:
                        days_left = (item.due_date - date.today()).days

                    severity = 'medium'
                    if days_left is not None and days_left < 3:
                        severity = 'critical'
                    elif days_left is not None and days_left < 7:
                        severity = 'high'

                    alert = MissingItemAlert(
                        item_name=item.name,
                        item_id=item.item_id,
                        category=item.category or section.name,
                        priority='high' if item.is_mandatory else 'medium',
                        severity=severity,
                        deadline=item.due_date,
                        days_remaining=days_left,
                        impact='Cannot submit tender without this mandatory item',
                        action_required=f'Collect and prepare {item.name}',
                        suggested_deadline=item.due_date.isoformat() if item.due_date else None,
                    )
                    alerts.append(alert)

        return sorted(alerts, key=lambda a: a.days_remaining or 999)


class ChecklistExporter:
    def __init__(self, checklist: CompleteChecklist):
        self._checklist = checklist

    def to_dict(self) -> dict:
        return self._checklist.model_dump()

    def to_json(self) -> str:
        return json.dumps(self._checklist.model_dump(), indent=2, default=str)

    def to_csv(self) -> str:
        rows = ['Section,Item Name,Mandatory,Status,Due Date,Notes']

        for section in self._checklist.sections:
            for item in section.items:
                due_date = item.due_date.isoformat() if item.due_date else ''
                rows.append(
                    f'"{section.name}","{item.name}",{item.is_mandatory},'
                    f'{item.status.value},{due_date},"{item.notes or ""}"'
                )

        return '\n'.join(rows)

    def to_markdown(self) -> str:
        md = f"# {self._checklist.name}\n\n"

        if self._checklist.description:
            md += f"{self._checklist.description}\n\n"

        md += f"**Progress:** {self._checklist.completion_percentage:.1f}%\n"
        md += f"**Score:** {self._checklist.score.overall_score:.1f}/100\n\n"

        for section in self._checklist.sections:
            md += f"## {section.name}\n\n"

            completed = sum(1 for i in section.items if i.is_submitted)
            total = len(section.items)
            md += f"Progress: {completed}/{total}\n\n"

            for item in section.items:
                status_icon = '[x]' if item.is_submitted else '[ ]'
                mandatory_tag = ' **(Required)**' if item.is_mandatory else ''
                md += f"- {status_icon} {item.name}{mandatory_tag}\n"

                if item.due_date:
                    md += f"  - Due: {item.due_date.isoformat()}\n"
                if item.notes:
                    md += f"  - Notes: {item.notes}\n"

            md += '\n'

        md += "## Submission Steps\n\n"
        for i, step in enumerate(self._checklist.submission_steps, 1):
            status_icon = '[x]' if step.is_completed else '[ ]'
            md += f"{i}. {status_icon} **{step.name}**"
            if step.estimated_duration_minutes:
                md += f" ({step.estimated_duration_minutes} min)"
            md += '\n'
            for instruction in step.instructions:
                md += f"   - {instruction}\n"

        return md

    def to_html(self) -> str:
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self._checklist.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .section-header {{ background: #e5e7eb; padding: 10px; border-radius: 4px; }}
        .item {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        .mandatory {{ font-weight: bold; }}
        .completed {{ color: green; }}
        .pending {{ color: orange; }}
        .progress-bar {{ background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ background: #22c55e; height: 100%; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self._checklist.name}</h1>
        <p>{self._checklist.description or ''}</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {self._checklist.completion_percentage}%"></div>
        </div>
        <p>Progress: {self._checklist.completion_percentage:.1f}% | Score: {self._checklist.score.overall_score:.1f}/100</p>
    </div>
"""

        for section in self._checklist.sections:
            html += f"""
    <div class="section">
        <div class="section-header">
            <h2>{section.name}</h2>
            <p>{section.completed_count}/{len(section.items)} completed</p>
        </div>
"""
            for item in section.items:
                status_class = 'completed' if item.is_submitted else 'pending'
                status_text = '✓' if item.is_submitted else '○'
                mandatory_class = ' mandatory' if item.is_mandatory else ''
                due = f" | Due: {item.due_date.isoformat()}" if item.due_date else ""

                html += f"""
        <div class="item{status_class}{mandatory_class}">
            <span>{status_text}</span> {item.name}{due}
        </div>
"""
            html += "</div>\n"

        html += """
</body>
</html>
"""
        return html


checklist_engine = ChecklistEngine()


def get_checklist_engine() -> ChecklistEngine:
    return checklist_engine