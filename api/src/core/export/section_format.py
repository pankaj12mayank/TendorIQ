"""Format analysis dashboard sections as readable export text."""

from __future__ import annotations

import json
from typing import Any


def format_dashboard_section(key: str, value: Any) -> str:
    if value is None:
        return ''
    if not isinstance(value, dict):
        return str(value)

    lines: list[str] = []

    if key == 'summary':
        conf = value.get('confidence')
        if isinstance(conf, dict):
            lines.append(f"Confidence: {conf.get('label', '')} ({conf.get('value', '')})")
        if value.get('overallAssessment'):
            lines.append(str(value['overallAssessment']))
        for item in value.get('keyFindings') or []:
            lines.append(f"• {item}")
        return '\n'.join(lines)

    if key == 'eligibility':
        lines.append(f"Overall score: {value.get('overallScore', 0)}%")
        for c in value.get('criteria') or []:
            if isinstance(c, dict):
                status = '✓' if c.get('met') else '✗'
                lines.append(f"{status} {c.get('name', c.get('id', 'Criterion'))}: {c.get('notes', '')}")
        return '\n'.join(lines)

    if key == 'technical':
        lines.append(f"Compliance: {value.get('complianceRate', 0)}%")
        for r in value.get('requirements') or []:
            if isinstance(r, dict):
                lines.append(f"- [{r.get('status', '')}] {r.get('title', '')}: {r.get('detail', '')}")
        return '\n'.join(lines)

    if key == 'financial':
        lines.append(f"Total: {value.get('totalValue', 0)} {value.get('currency', 'USD')}")
        for item in value.get('items') or []:
            if isinstance(item, dict):
                lines.append(f"- {item.get('label', '')}: {item.get('amount', '')} {item.get('notes', '')}")
        return '\n'.join(lines)

    if key == 'risks':
        lines.append(f"Risk score: {value.get('overallRiskScore', 0)}")
        for r in value.get('risks') or []:
            if isinstance(r, dict):
                lines.append(
                    f"- [{r.get('severity', '')}] {r.get('title', '')}: {r.get('mitigation', '')}"
                )
        return '\n'.join(lines)

    if key == 'deadlines':
        for d in value.get('deadlines') or []:
            if isinstance(d, dict):
                crit = ' (critical)' if d.get('critical') else ''
                lines.append(f"- {d.get('label', '')}: {d.get('date', '')}{crit}")
        return '\n'.join(lines)

    if key in ('mandatoryDocs', 'mandatory_docs'):
        lines.append(f"Completion: {value.get('overallCompletion', 0)}%")
        for d in value.get('documents') or []:
            if isinstance(d, dict):
                lines.append(f"- {d.get('name', '')}: {d.get('status', '')}")
        return '\n'.join(lines)

    if key == 'importantClauses':
        for c in value.get('clauses') or []:
            if isinstance(c, dict):
                lines.append(f"### {c.get('title', '')} ({c.get('category', '')})")
                lines.append(c.get('excerpt', ''))
                lines.append(f"Impact: {c.get('impact', '')}\n")
        return '\n'.join(lines)

    return json.dumps(value, indent=2, default=str)


def organization_line(company: dict | None) -> str | None:
    if not company:
        return None
    parts = []
    if company.get('company_name'):
        parts.append(str(company['company_name']))
    if company.get('address'):
        parts.append(str(company['address']))
    if company.get('phone'):
        parts.append(f"Tel: {company['phone']}")
    if company.get('website'):
        parts.append(str(company['website']))
    return ' | '.join(parts) if parts else None
