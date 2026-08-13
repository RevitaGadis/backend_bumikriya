import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 8
RESEND_API_URL = "https://api.resend.com/emails"
_LAST_EMAIL_ERROR = None


def get_last_email_error() -> str:
    return _LAST_EMAIL_ERROR or ""


def _send_via_resend(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    global _LAST_EMAIL_ERROR
    payload = {
        "from": settings.RESEND_FROM,
        "to": [to_email],
        "subject": subject,
        "html": body_html,
    }
    if body_text:
        payload["text"] = body_text

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        RESEND_API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "bumikriya-backend/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=SMTP_TIMEOUT) as resp:
            resp.read()
        _LAST_EMAIL_ERROR = None
        return True
    except urllib.error.HTTPError as e:
        _LAST_EMAIL_ERROR = (
            f"Resend HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        )
        logger.error("Resend failed for %s: %s", to_email, _LAST_EMAIL_ERROR)
        return False
    except Exception as e:
        _LAST_EMAIL_ERROR = f"{type(e).__name__}: {e}"
        logger.error("Resend request failed for %s: %s", to_email, _LAST_EMAIL_ERROR)
        return False


def _send_via_smtp(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    global _LAST_EMAIL_ERROR
    if not settings.SMTP_HOST:
        _LAST_EMAIL_ERROR = "SMTP_HOST is not configured"
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

    primary_port = settings.SMTP_PORT
    ports = [primary_port]
    if primary_port != 465:
        ports.append(465)

    last_error = None
    for port in ports:
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=SMTP_TIMEOUT)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=SMTP_TIMEOUT)
                if settings.SMTP_USE_TLS:
                    server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_email], message.as_string())
            server.quit()
            _LAST_EMAIL_ERROR = None
            return True
        except Exception as e:
            last_error = e
            logger.warning(
                "SMTP attempt to %s:%s failed for %s: %s",
                settings.SMTP_HOST, port, to_email, e,
            )

    _LAST_EMAIL_ERROR = f"{type(last_error).__name__}: {last_error}"
    logger.error("Failed to send email to %s: %s", to_email, _LAST_EMAIL_ERROR)
    return False


def send_email(to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
    if settings.RESEND_API_KEY:
        return _send_via_resend(to_email, subject, body_html, body_text)
    return _send_via_smtp(to_email, subject, body_html, body_text)
