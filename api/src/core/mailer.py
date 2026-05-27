"""SMTP mail sender for password reset and test mails."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .smtp_settings import is_smtp_configured


def send_smtp_email(
    *,
    smtp_settings: dict,
    to_email: str,
    subject: str,
    text_body: str,
) -> None:
    if not is_smtp_configured(smtp_settings):
        raise ValueError('SMTP is not configured')

    host = str(smtp_settings.get('host') or '').strip()
    port = int(smtp_settings.get('port') or 587)
    sender_email = str(smtp_settings.get('sender_email') or '').strip()
    sender_name = str(smtp_settings.get('sender_name') or 'TenderIQ').strip()
    app_password = str(smtp_settings.get('app_password') or '').strip()

    msg = EmailMessage()
    msg['From'] = f'{sender_name} <{sender_email}>'
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(text_body)

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, app_password)
        server.send_message(msg)
