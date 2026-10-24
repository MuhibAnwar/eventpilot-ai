"""Registration email via SMTP (HTML + plain text, optional PDF attachments)."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

from app.email_templates import certificate_email, confirmation_email, pass_email

Attachment = tuple[str, bytes, str]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def smtp_configured() -> bool:
    required = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM")
    return all(os.getenv(k, "").strip() for k in required)


def email_status() -> dict[str, Any]:
    ok = smtp_configured()
    return {
        "smtp_configured": ok,
        "connected": ok,
        "from_address": os.getenv("SMTP_FROM", "").strip() or None,
        "smtp_host": os.getenv("SMTP_HOST", "").strip() or None,
    }


def build_confirmation_preview(name: str, email: str) -> dict[str, str]:
    subject, plain, html_body = confirmation_email(name)
    return {
        "to": email,
        "subject": subject,
        "body": plain,
        "html": html_body,
    }


def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    attachments: list[Attachment] | None = None,
) -> dict[str, Any]:
    if not smtp_configured():
        return {
            "sent": False,
            "detail": "Email not sent: configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM in .env",
        }

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME", "EventPilot AI").strip() or "EventPilot AI"
    use_tls = _env_bool("SMTP_USE_TLS", default=True)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_addr))
    msg["To"] = to
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    for filename, data, mime in attachments or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype or "octet-stream", filename=filename)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as exc:
        return {
            "sent": False,
            "detail": f"Email delivery failed: {exc}",
            "error": str(exc)[:200],
        }

    return {"sent": True, "detail": f"Email sent to {to}"}


def send_confirmation_email(name: str, email: str) -> dict[str, Any]:
    subject, plain, html_body = confirmation_email(name)
    result = send_email(to=email, subject=subject, body=plain, html_body=html_body)
    if result.get("sent"):
        result["detail"] = f"Confirmation email (1/3) sent to {email}"
    return result


def send_pass_email(name: str, email: str, pass_pdf: bytes) -> dict[str, Any]:
    subject, plain, html_body = pass_email(name)
    result = send_email(
        to=email,
        subject=subject,
        body=plain,
        html_body=html_body,
        attachments=[("event-pass.pdf", pass_pdf, "application/pdf")],
    )
    if result.get("sent"):
        result["detail"] = f"Pass email (2/3) with PDF sent to {email}"
    return result


def send_certificate_email(name: str, email: str, cert_pdf: bytes) -> dict[str, Any]:
    subject, plain, html_body = certificate_email(name)
    result = send_email(
        to=email,
        subject=subject,
        body=plain,
        html_body=html_body,
        attachments=[("certificate.pdf", cert_pdf, "application/pdf")],
    )
    if result.get("sent"):
        result["detail"] = f"Certificate email (3/3) with PDF sent to {email}"
    return result
