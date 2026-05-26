"""Phase 6 — PDF-only export policy and report formatting."""

import pytest
from fastapi import HTTPException

from src.core.export.lite_policy import assert_lite_export_format, lite_formats_payload
from src.core.export.schemas import ExportFormat
from src.core.export.section_format import format_dashboard_section, organization_line


def test_lite_formats_payload_pdf_only():
    data = lite_formats_payload()
    assert data['pdf_only'] is True
    assert len(data['formats']) == 1
    assert data['formats'][0]['id'] == 'pdf'


def test_assert_lite_export_format_rejects_docx():
    with pytest.raises(HTTPException) as exc:
        assert_lite_export_format(ExportFormat.DOCX)
    assert exc.value.status_code == 400


def test_format_summary_section():
    text = format_dashboard_section(
        'summary',
        {
            'overallAssessment': 'Strong fit',
            'keyFindings': ['Deadline tight'],
            'confidence': {'value': 0.8, 'label': 'High'},
        },
    )
    assert 'Strong fit' in text
    assert 'Deadline tight' in text


def test_organization_line():
    org = organization_line(
        {'company_name': 'Acme', 'address': '1 Main St', 'phone': '555'}
    )
    assert 'Acme' in org
    assert '555' in org
