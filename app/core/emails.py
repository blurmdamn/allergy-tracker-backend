from __future__ import annotations

import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings


async def send_email(to_email: str, subject: str, html: str, text: str | None = None) -> None:
    """
    Унифицированная отправка email.
    - console: печатает письмо в терминал (fallback/dev)
    - sendgrid: отправляет через SendGrid
    """
    provider = (settings.EMAIL_PROVIDER or "console").lower()

    if provider == "console":
        print("\n=== EMAIL (console) ===")
        print("To:", to_email)
        print("Subject:", subject)
        if text:
            print(text)
        else:
            print(html)
        print("=======================\n")
        return

    if provider == "sendgrid":
        if not settings.SENDGRID_API_KEY:
            # безопасный fallback
            print("SENDGRID_API_KEY is missing. Falling back to console.")
            settings.EMAIL_PROVIDER = "console"
            await send_email(to_email, subject, html, text=text)
            return

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=html,
            plain_text_content=text,
        )

        # sendgrid SDK синхронный -> отправляем в отдельном потоке, чтобы не блокировать event loop
        def _send_sync():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)

        await asyncio.to_thread(_send_sync)
        return

    raise ValueError(f"Unknown EMAIL_PROVIDER: {provider}")
