"""Async email delivery via fastapi-mail.

In dev/test environments, MAIL_SERVER is empty — send functions log instead of
raising so that endpoint tests pass without real SMTP credentials.
"""
from app.core.config import settings
from app.core.logging import logger


async def send_verification_email(email: str, token: str) -> None:
    verify_url = f"{settings.app_base_url}/verify-email?token={token}"
    if not settings.mail_server:
        logger.info("email.verification.skipped", email=email, url=verify_url)
        return
    try:
        from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_tls,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
        )
        message = MessageSchema(
            subject="Verify your FantasyHub account",
            recipients=[email],
            body=f"Click to verify your account: {verify_url}",
            subtype=MessageType.plain,
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        logger.error("email.verification.failed", email=email, error=str(e))


async def send_password_reset_email(email: str, token: str) -> None:
    reset_url = f"{settings.app_base_url}/reset-password?token={token}"
    if not settings.mail_server:
        logger.info("email.reset.skipped", email=email, url=reset_url)
        return
    try:
        from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_tls,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
        )
        message = MessageSchema(
            subject="Reset your FantasyHub password",
            recipients=[email],
            body=f"Click to reset your password: {reset_url}",
            subtype=MessageType.plain,
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        logger.error("email.reset.failed", email=email, error=str(e))
