"""Export Engine - Export Service and Orchestration"""

import io
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import UploadFile

from .schemas import (
    ExportFormat,
    ExportJob,
    ExportLog,
    ExportRequest,
    ExportResponse,
    ExportStatus,
    ExportTemplate,
    ExportType,
)
from .engine import ExportEngine, TemplateManager, get_export_engine, get_template_manager
from .pdf_generator import PDFGenerator, get_pdf_generator
from .docx_generator import DOCXGenerator, get_docx_generator

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(
        self,
        engine: Optional[ExportEngine] = None,
        template_manager: Optional[TemplateManager] = None,
    ):
        self._engine = engine or get_export_engine()
        self._template_manager = template_manager or get_template_manager()
        self._pdf = get_pdf_generator()
        self._docx = get_docx_generator()
        self._logs: list[ExportLog] = []
        self._inline_source: dict[str, dict] = {}

    def set_inline_source(self, job_id: str, data: dict) -> None:
        self._inline_source[job_id] = data

    def _log_action(self, export_id: str, action: str, user_id: str, organization_id: str, **kwargs):
        log = ExportLog(
            export_id=export_id,
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            details=kwargs if kwargs else None,
        )
        self._logs.append(log)

    def _get_template(self, request: ExportRequest) -> ExportTemplate:
        if request.template_id:
            template = self._engine.get_template(request.template_id)
            if template:
                return template
        return self._template_manager.get_for_document_type(request.export_type)

    def _get_source_data(self, source_type: str, source_id: str) -> Optional[dict]:
        from ..proposal.service import proposal_engine

        try:
            if source_type == 'proposal':
                proposal = proposal_engine.get_proposal(source_id)
                if proposal:
                    from ..proposal.service import ProposalExporter
                    exporter = ProposalExporter(proposal)
                    return json.loads(exporter.to_json())
        except Exception as e:
            logger.error(f'Failed to fetch source data: {e}')

        return None

    def create_export(self, request: ExportRequest, user_id: str, organization_id: str) -> ExportJob:
        job = self._engine.create_export_job(request, user_id, organization_id)

        self._log_action(
            job.export_id,
            'export_created',
            user_id,
            organization_id,
            export_type=request.export_type.value,
            format=request.format.value,
            source_id=request.source_id,
            job_id=job.job_id,
            status=job.status.value,
        )

        return job

    def process_export(self, job_id: str) -> Optional[ExportJob]:
        job = self._engine.get_job(job_id)
        if not job:
            logger.error(f'Export job not found: {job_id}')
            return None

        self._engine.update_job_status(job_id, ExportStatus.PROCESSING)

        source_data = self._inline_source.pop(job_id, None) or self._get_source_data(
            job.source_type, job.source_id
        )
        if not source_data:
            self._engine.update_job_status(
                job_id,
                ExportStatus.FAILED,
                error_message='Source data not found',
            )
            return job

        template = None
        if job.template_id:
            template = self._engine.get_template(job.template_id)

        if job.format == ExportFormat.PDF:
            generator = get_pdf_generator(template)
            content = generator.generate_generic_pdf(source_data, job.export_type)
            filename = f'{job.export_id}.pdf'
        elif job.format == ExportFormat.DOCX:
            generator = get_docx_generator(template)
            content = generator.generate_generic_docx(source_data, job.export_type)
            filename = f'{job.export_id}.docx'
        elif job.format == ExportFormat.HTML:
            content = self._generate_html(source_data, job.export_type, template)
            filename = f'{job.export_id}.html'
        elif job.format == ExportFormat.MARKDOWN:
            content = self._generate_markdown(source_data, job.export_type)
            filename = f'{job.export_id}.md'
        elif job.format == ExportFormat.JSON:
            content = json.dumps(source_data, indent=2, default=str).encode()
            filename = f'{job.export_id}.json'
        elif job.format == ExportFormat.CSV:
            content = self._generate_csv(source_data, job.export_type)
            filename = f'{job.export_id}.csv'
        else:
            self._engine.update_job_status(
                job_id,
                ExportStatus.FAILED,
                error_message=f'Unsupported format: {job.format}',
            )
            return job

        file_path = self._engine._get_file_path(job_id, job.export_id, job.format)
        with open(file_path, 'wb') as f:
            f.write(content)

        file_size = os.path.getsize(file_path)

        self._engine.update_job_status(
            job_id,
            ExportStatus.COMPLETED,
            file_path=file_path,
            file_size_bytes=file_size,
            download_url=f'/api/v1/exports/{job.export_id}/download',
        )

        self._log_action(
            job.export_id,
            'export_completed',
            job.requested_by,
            job.organization_id,
            file_size_bytes=file_size,
            format=job.format.value,
            job_id=job.job_id,
            status=job.status.value,
        )

        logger.info(f'Export completed: {job.export_id} ({file_size} bytes)')
        return job

    def _generate_html(self, data: dict, doc_type: ExportType, template: Optional[ExportTemplate] = None) -> bytes:
        template = template or self._template_manager.get_default()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{data.get('title', data.get('name', 'Export'))}</title>
    <style>
        body {{ font-family: '{template.font_family}', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; color: #2d3748; }}
        .header {{ background: {template.primary_color}; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 24px; }}
        .header .meta {{ font-size: 12px; opacity: 0.9; }}
        .section {{ margin-bottom: 25px; }}
        .section h2 {{ color: {template.primary_color}; border-bottom: 2px solid {template.accent_color}; padding-bottom: 8px; }}
        .content {{ line-height: 1.7; }}
        .footer {{ text-align: center; color: {template.secondary_color}; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; }}
        .watermark {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); font-size: 80px; color: rgba(128,128,128,0.1); pointer-events: none; z-index: -1; }}
    </style>
</head>
<body>
"""

        if template.show_watermark and template.watermark:
            html += f'    <div class="watermark">{template.watermark.text}</div>\n'

        title = data.get('title', data.get('name', 'Document Export'))
        html += f'    <div class="header">\n        <h1>{title}</h1>\n        <div class="meta">'

        if data.get('status'):
            html += f' Status: {data["status"]} |'
        if data.get('version'):
            html += f' Version: {data["version"]} |'
        html += f' Generated: {datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")}'
        html += '</div>\n    </div>\n'

        if data.get('summary'):
            html += '    <div class="section">\n        <h2>Executive Summary</h2>\n        <div class="content">' + data['summary'] + '</div>\n    </div>\n'

        sections = data.get('sections', [])
        for section in sections:
            html += f'    <div class="section">\n        <h2>{section.get("title", "")}</h2>\n        <div class="content">'
            content = section.get('content', '') or section.get('description', '')
            html += content.replace('\n', '<br>')
            html += '</div>\n    </div>\n'

        if data.get('completion_percentage') is not None:
            html += f'    <div class="section">\n        <h2>Progress</h2>\n        <p>Completion: {data["completion_percentage"]:.1f}% | Score: {data.get("score", {}).get("overall_score", 0):.1f}/100</p>\n    </div>\n'

        html += f"""    <div class="footer">
        Generated by TenderIQ | {datetime.utcnow().strftime("%d %b %Y %H:%M UTC")}
    </div>
</body>
</html>"""

        return html.encode('utf-8')

    def _generate_markdown(self, data: dict, doc_type: ExportType) -> bytes:
        md = f"# {data.get('title', data.get('name', 'Document'))}\n\n"

        if data.get('status'):
            md += f"**Status:** {data['status']} | "
        if data.get('version'):
            md += f"**Version:** {data['version']} | "
        md += f"**Generated:** {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}\n\n"
        md += "---\n\n"

        if data.get('summary'):
            md += "## Executive Summary\n\n" + data['summary'] + "\n\n---\n\n"

        for section in data.get('sections', []):
            md += f"## {section.get('title', '')}\n\n"
            content = section.get('content', '') or section.get('description', '')
            md += content + "\n\n"

        if data.get('completion_percentage') is not None:
            md += f"## Progress\n\n- **Completion:** {data['completion_percentage']:.1f}%\n"
            md += f"- **Score:** {data.get('score', {}).get('overall_score', 0):.1f}/100\n\n"

        md += "---\n*Generated by TenderIQ*\n"
        return md.encode('utf-8')

    def _generate_csv(self, data: dict, doc_type: ExportType) -> bytes:
        if doc_type == ExportType.CHECKLIST:
            rows = ['Section', 'Item', 'Mandatory', 'Status', 'Due Date', 'Notes']
            for section in data.get('sections', []):
                for item in section.get('items', []):
                    rows.append(
                        f'"{section.get("name", "")}","{item.get("name", "")}",'
                        f'{item.get("is_mandatory", False)},'
                        f'"{item.get("status", "pending")}","{item.get("due_date", "")}","{item.get("notes", "")}"'
                    )
        elif doc_type == ExportType.RISK_ANALYSIS:
            rows = ['Category', 'Risk', 'Severity', 'Impact', 'Mitigation', 'Likelihood', 'Consequence']
            for category in data.get('risk_categories', []):
                for risk in category.get('risks', []):
                    rows.append(
                        f'"{category.get("name", "")}","{risk.get("title", "")}",'
                        f'"{risk.get("severity", "low")}","{risk.get("impact", "medium")}",'
                        f'"{risk.get("mitigation", "")}","{risk.get("likelihood", "")}","{risk.get("consequence", "")}"'
                    )
        else:
            rows = ['Field', 'Value']
            for key, value in data.items():
                if key not in ('sections', 'items', 'risks', 'content', 'summary'):
                    rows.append(f'"{key}","{value}"')

        return '\n'.join(rows).encode('utf-8')

    def get_export_file(self, export_id: str) -> Optional[tuple[bytes, str, str]]:
        export = self._engine.get_export(export_id)
        if not export:
            return None

        job = None
        for j in self._engine._jobs.values():
            if j.export_id == export_id and j.status == ExportStatus.COMPLETED:
                job = j
                break

        if not job or not job.file_path or not os.path.exists(job.file_path):
            return None

        with open(job.file_path, 'rb') as f:
            content = f.read()

        mime_types = {
            ExportFormat.PDF: 'application/pdf',
            ExportFormat.DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ExportFormat.HTML: 'text/html',
            ExportFormat.MARKDOWN: 'text/markdown',
            ExportFormat.JSON: 'application/json',
            ExportFormat.CSV: 'text/csv',
        }

        filename = f"{export.title.replace(' ', '_')[:50]}.{export.format.value}"
        return content, mime_types.get(export.format, 'application/octet-stream'), filename

    def register_template(self, template: ExportTemplate) -> ExportTemplate:
        return self._engine.register_template(template)

    def list_templates(self) -> list[ExportTemplate]:
        return self._engine.list_templates()

    def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        return self._engine.get_job(job_id)

    def get_export_history(self, organization_id: str, limit: int = 50) -> list[ExportLog]:
        return [log for log in self._logs if log.organization_id == organization_id][-limit:]


export_service = ExportService()


def get_export_service() -> ExportService:
    return export_service