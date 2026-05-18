"""Export Engine - PDF Generator using ReportLab"""

import io
import logging
import math
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Frame,
    SimpleDocTemplate,
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate

from .schemas import ExportFormat, ExportTemplate, ExportWatermark, ExportType
from .engine import get_template_manager

logger = logging.getLogger(__name__)

PAGE_SIZES = {
    'a4': A4,
    'letter': (8.5 * inch, 11 * inch),
    'legal': (8.5 * inch, 14 * inch),
}

MARGINS = {
    'narrow': (0.5 * cm, 0.5 * cm, 0.5 * cm, 0.5 * cm),
    'normal': (1.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm),
    'wide': (2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm),
}


class PDFGenerator:
    def __init__(self, template: Optional[ExportTemplate] = None):
        self.template = template or get_template_manager().get_default()
        self._styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        primary = self.template.primary_color
        accent = self.template.accent_color

        self._styles.add(ParagraphStyle(
            name='DocTitle',
            parent=self._styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(primary),
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
        ))

        self._styles.add(ParagraphStyle(
            name='DocSubtitle',
            parent=self._styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(self.template.secondary_color),
            spaceAfter=12,
            alignment=TA_LEFT,
        ))

        self._styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self._styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(primary),
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
        ))

        self._styles.add(ParagraphStyle(
            name='BodyText',
            parent=self._styles['Normal'],
            fontSize=self.template.font_size,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=8,
            leading=16,
        ))

        self._styles.add(ParagraphStyle(
            name='Metadata',
            parent=self._styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor(self.template.secondary_color),
            spaceAfter=4,
        ))

        self._styles.add(ParagraphStyle(
            name='Footer',
            parent=self._styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor(self.template.secondary_color),
            alignment=TA_CENTER,
        ))

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _add_watermark(self, canvas, doc):
        if not self.template.show_watermark or not self.template.watermark:
            return

        wm = self.template.watermark
        canvas.saveState()

        canvas.setFillColor(colors.HexColor(wm.color))
        canvas.setFillAlpha(wm.opacity)
        canvas.setFont('Helvetica-Bold', wm.font_size)

        width = doc.pagesize[0]
        height = doc.pagesize[1]

        if wm.position.value == 'diagonal':
            canvas.translate(width / 2, height / 2)
            canvas.rotate(wm.diagonal_angle)
            text = f' {wm.text} '
            canvas.drawCentredString(0, 0, text * 3)
        elif wm.position.value == 'center':
            canvas.drawCentredString(width / 2, height / 2, wm.text)
        elif wm.position.value == 'corner':
            canvas.drawString(50, height - 50, wm.text)
        elif wm.position.value == 'tile':
            spacing = 200
            for x in range(0, int(width), spacing):
                for y in range(0, int(height), spacing):
                    canvas.saveState()
                    canvas.translate(x, y)
                    canvas.rotate(wm.diagonal_angle)
                    canvas.drawCentredString(0, 0, wm.text)
                    canvas.restoreState()

        canvas.restoreState()

    def _add_header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setFillColor(colors.HexColor(self.template.primary_color))
        canvas.rect(0, doc.pagesize[1] - 1 * cm, doc.pagesize[0], 1 * cm, fill=1, stroke=0)

        if self.template.company_name:
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawString(1.5 * cm, doc.pagesize[1] - 0.6 * cm, self.template.company_name)

        canvas.setFillColor(colors.HexColor(self.template.secondary_color))
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(
            doc.pagesize[0] - 1.5 * cm,
            doc.pagesize[1] - 0.6 * cm,
            canvas.getPageNumber(),
        )

        if self.template.show_timestamp:
            canvas.setFont('Helvetica', 7)
            timestamp = datetime.utcnow().strftime('%d %b %Y %H:%M UTC')
            canvas.drawString(1.5 * cm, 1 * cm, timestamp)

        if self.template.show_page_numbers:
            canvas.drawRightString(
                doc.pagesize[0] - 1.5 * cm,
                1 * cm,
                f'Page {canvas.getPageNumber()}',
            )

        canvas.restoreState()

    def generate_proposal_pdf(self, data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        story = []

        title_style = self._styles['DocTitle']
        story.append(Paragraph(data.get('title', 'Proposal Document'), title_style))

        meta_data = []
        if data.get('status'):
            meta_data.append(f"<b>Status:</b> {data['status']}")
        if data.get('version'):
            meta_data.append(f"<b>Version:</b> {data['version']}")
        if data.get('created_at'):
            meta_data.append(f"<b>Generated:</b> {data['created_at']}")
        if data.get('organization'):
            meta_data.append(f"<b>Organization:</b> {data['organization']}")

        if meta_data:
            story.append(Spacer(1, 0.3 * cm))
            for item in meta_data:
                story.append(Paragraph(item, self._styles['Metadata']))

        story.append(HRFlowable(
            width='100%',
            thickness=2,
            color=colors.HexColor(self.template.primary_color),
            spaceBefore=15,
            spaceAfter=20,
        ))

        for section in data.get('sections', []):
            story.append(Paragraph(section.get('title', ''), self._styles['SectionHeader']))

            content = section.get('content', '')
            if isinstance(content, str):
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        story.append(Paragraph(para, self._styles['BodyText']))

            if section.get('word_count'):
                story.append(Paragraph(
                    f"<i>Word count: {section['word_count']}</i>",
                    self._styles['Metadata']
                ))

            story.append(Spacer(1, 0.5 * cm))

        if data.get('summary'):
            story.append(Spacer(1, 1 * cm))
            story.append(Paragraph('Executive Summary', self._styles['SectionHeader']))
            story.append(Paragraph(data['summary'], self._styles['BodyText']))

        doc.build(
            story,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer,
        )

        content = buffer.getvalue()
        buffer.close()
        return content

    def generate_checklist_pdf(self, data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        story = []

        story.append(Paragraph(data.get('name', 'Compliance Checklist'), self._styles['DocTitle']))

        if data.get('description'):
            story.append(Paragraph(data['description'], self._styles['BodyText']))

        progress = data.get('completion_percentage', 0)
        score = data.get('score', {})

        summary_data = [
            ['Progress', f'{progress:.1f}%'],
            ['Overall Score', f"{score.get('overall_score', 0):.1f}/100"],
            ['Mandatory Items', f"{data.get('mandatory_completed', 0)}/{data.get('mandatory_total', 0)}"],
        ]

        summary_table = Table(summary_data, colWidths=[3 * cm, 4 * cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * cm))

        for section in data.get('sections', []):
            story.append(Paragraph(section.get('name', ''), self._styles['SectionHeader']))

            items_data = [['Item', 'Status', 'Due Date']]
            for item in section.get('items', []):
                status = '[x]' if item.get('is_submitted') else '[ ]'
                due = item.get('due_date', 'N/A')
                mandatory = ' (Required)' if item.get('is_mandatory') else ''
                items_data.append([
                    f"{status} {item.get('name', '')}{mandatory}",
                    item.get('status', 'pending').title(),
                    str(due)[:10] if due else 'N/A'
                ])

            items_table = Table(items_data, colWidths=[8 * cm, 3 * cm, 3 * cm])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.template.primary_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 0.5 * cm))

        if data.get('submission_steps'):
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph('Submission Steps', self._styles['SectionHeader']))
            for i, step in enumerate(data.get('submission_steps', []), 1):
                status = '[x]' if step.get('is_completed') else '[ ]'
                duration = f" ({step.get('estimated_duration_minutes', 0)} min)" if step.get('estimated_duration_minutes') else ''
                story.append(Paragraph(
                    f"{i}. {status} <b>{step.get('name', '')}</b>{duration}",
                    self._styles['BodyText']
                ))

        doc.build(
            story,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer,
        )

        content = buffer.getvalue()
        buffer.close()
        return content

    def generate_risk_analysis_pdf(self, data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        story = []

        story.append(Paragraph(data.get('title', 'Risk Analysis Report'), self._styles['DocTitle']))

        meta_items = []
        if data.get('tender_id'):
            meta_items.append(f"<b>Tender ID:</b> {data['tender_id']}")
        if data.get('overall_risk_score') is not None:
            score = data['overall_risk_score']
            severity = self._get_risk_severity(score)
            meta_items.append(f"<b>Overall Risk:</b> {score:.1f}/100 ({severity})")
        if data.get('analysis_date'):
            meta_items.append(f"<b>Analysis Date:</b> {data['analysis_date']}")

        for item in meta_items:
            story.append(Paragraph(item, self._styles['Metadata']))

        story.append(HRFlowable(
            width='100%',
            thickness=2,
            color=colors.HexColor(self.template.primary_color),
            spaceBefore=15,
            spaceAfter=20,
        ))

        if data.get('summary'):
            story.append(Paragraph('Executive Summary', self._styles['SectionHeader']))
            story.append(Paragraph(data['summary'], self._styles['BodyText']))
            story.append(Spacer(1, 0.5 * cm))

        risk_colors = {
            'critical': '#c53030',
            'high': '#dd6b20',
            'medium': '#d69e2e',
            'low': '#38a169',
        }

        for category in data.get('risk_categories', []):
            category_name = category.get('name', 'Category')
            story.append(Paragraph(category_name, self._styles['SectionHeader']))

            risks_data = [['Risk', 'Severity', 'Impact', 'Mitigation']]
            for risk in category.get('risks', []):
                severity = risk.get('severity', 'low').lower()
                impact = risk.get('impact', 'medium')
                mitigation = risk.get('mitigation', '')[:50] + '...' if len(risk.get('mitigation', '')) > 50 else risk.get('mitigation', '')
                risks_data.append([
                    risk.get('title', ''),
                    severity.upper(),
                    impact.title(),
                    mitigation,
                ])

            if len(risks_data) > 1:
                risks_table = Table(risks_data, colWidths=[4.5 * cm, 2.5 * cm, 2.5 * cm, 4.5 * cm])
                risks_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.template.primary_color)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BACKGROUND', (1, 1), (1, -1), colors.HexColor(risk_colors.get(severity, '#718096'))),
                    ('TEXTCOLOR', (1, 1), (1, -1), colors.white),
                ]))
                story.append(risks_table)
            story.append(Spacer(1, 0.5 * cm))

        doc.build(
            story,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer,
        )

        content = buffer.getvalue()
        buffer.close()
        return content

    def _get_risk_severity(self, score: float) -> str:
        if score >= 90:
            return 'Critical'
        elif score >= 70:
            return 'High'
        elif score >= 40:
            return 'Medium'
        else:
            return 'Low'

    def generate_generic_pdf(self, data: dict, doc_type: ExportType = ExportType.CUSTOM) -> bytes:
        if doc_type == ExportType.PROPOSAL:
            return self.generate_proposal_pdf(data)
        elif doc_type == ExportType.CHECKLIST:
            return self.generate_checklist_pdf(data)
        elif doc_type == ExportType.RISK_ANALYSIS:
            return self.generate_risk_analysis_pdf(data)
        else:
            return self.generate_custom_pdf(data)

    def generate_custom_pdf(self, data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        story = []

        title = data.get('title') or data.get('name') or 'Document'
        story.append(Paragraph(title, self._styles['DocTitle']))

        for key, value in data.items():
            if key in ('title', 'name', 'sections', 'items', 'risks', 'content'):
                continue
            story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self._styles['Metadata']))

        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=20))

        if 'sections' in data:
            for section in data['sections']:
                story.append(Paragraph(section.get('title', ''), self._styles['SectionHeader']))
                content = section.get('content', '') or section.get('description', '')
                if isinstance(content, str):
                    for para in content.split('\n\n'):
                        if para.strip():
                            story.append(Paragraph(para, self._styles['BodyText']))
                story.append(Spacer(1, 0.3 * cm))

        doc.build(
            story,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer,
        )

        content = buffer.getvalue()
        buffer.close()
        return content


pdf_generator = PDFGenerator()


def get_pdf_generator(template: Optional[ExportTemplate] = None) -> PDFGenerator:
    return PDFGenerator(template)