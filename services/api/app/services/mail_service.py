"""Simple mail delivery: SMTP if configured, otherwise local outbox."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from app.config import Settings


def send_email(
    *,
    settings: Settings,
    to_email: str,
    subject: str,
    body: str,
) -> dict:
    """Send email or write to data/mail_outbox. Never logs secrets."""
    outbox = settings.data_dir / "mail_outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    safe_to = to_email.replace("@", "_at_")
    path = outbox / f"{stamp}_{safe_to}.txt"
    payload = (
        f"To: {to_email}\n"
        f"From: {settings.smtp_from or settings.smtp_user or 'noreply@mywave.local'}\n"
        f"Subject: {subject}\n"
        f"Date: {datetime.now(timezone.utc).isoformat()}\n\n"
        f"{body}\n"
    )
    path.write_text(payload, encoding="utf-8")

    delivered = False
    error: str | None = None
    if settings.smtp_host and settings.smtp_from:
        try:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = settings.smtp_from
            message["To"] = to_email
            message.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
            delivered = True
        except Exception as exc:  # noqa: BLE001 — surface mail errors without crashing request
            error = str(exc)
            (outbox / f"{stamp}_ERROR.txt").write_text(error, encoding="utf-8")

    return {
        "delivered_smtp": delivered,
        "outbox_path": str(path),
        "error": error,
    }
