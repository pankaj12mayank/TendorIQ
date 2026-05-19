"""Dynamic {{variable}} template rendering with validation and HTML sanitization."""

import html
import re
from typing import Any

VARIABLE_PATTERN = re.compile(r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}')
SCRIPT_PATTERN = re.compile(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', re.IGNORECASE)
ON_EVENT_PATTERN = re.compile(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE)


def sanitize_html(content: str) -> str:
    """Strip scripts and inline event handlers for XSS safety."""
    cleaned = SCRIPT_PATTERN.sub('', content)
    cleaned = ON_EVENT_PATTERN.sub('', cleaned)
    return cleaned


def extract_variables(content: str) -> list[str]:
    return list(dict.fromkeys(VARIABLE_PATTERN.findall(content)))


def render_template(
    subject: str,
    html_body: str,
    text_body: str | None,
    variables: dict[str, Any],
    defaults: dict[str, Any] | None = None,
    strict: bool = False,
) -> tuple[str, str, str | None, list[str]]:
    """
    Render subject, html, and text with variable substitution.
    Returns (subject, html, text, missing_variables).
    """
    merged = {**(defaults or {}), **variables}
    all_content = subject + html_body + (text_body or '')
    required_keys = set(extract_variables(all_content))
    missing = [k for k in required_keys if k not in merged or merged[k] is None]

    if strict and missing:
        return subject, html_body, text_body, missing

    def replace_vars(text: str) -> str:
        def replacer(match: re.Match) -> str:
            key = match.group(1)
            val = merged.get(key)
            if val is None:
                return match.group(0)
            return html.escape(str(val)) if '<' not in str(val) else str(val)

        return VARIABLE_PATTERN.sub(replacer, text)

    rendered_subject = replace_vars(subject)
    rendered_html = sanitize_html(replace_vars(html_body))
    rendered_text = replace_vars(text_body) if text_body else None
    return rendered_subject, rendered_html, rendered_text, missing
