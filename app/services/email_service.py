import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP not configured. Email to %s not sent.\nSubject: %s\nBody:\n%s",
            to_email, subject, body_text or body_html,
        )
        return False

    message = MIMEMultipart("alternative")
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body_text or "Silakan lihat email dalam format HTML.", "plain"))
    message.attach(MIMEText(body_html, "html"))

    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            if settings.SMTP_USE_TLS:
                server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], message.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False