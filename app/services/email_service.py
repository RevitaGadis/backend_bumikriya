import base64
import json
import logging
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


SMTP_TIMEOUT = 8
RESEND_API_URL = "https://api.resend.com/emails"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_LAST_EMAIL_ERROR = None


def get_last_email_error() -> str:
    return _LAST_EMAIL_ERROR or ""


def _build_message(to_email: str, subject: str, body_html: str, body_text: str) -> str:
    message = MIMEMultipart("alternative")
    message["From"] = settings.GMAIL_FROM or settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body_text or "Silakan lihat email dalam format HTML.", "plain"))
    message.attach(MIMEText(body_html, "html"))
    return message.as_string()


def _send_via_gmail(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    global _LAST_EMAIL_ERROR
    missing = [
        name
        for name, value in (
            ("GMAIL_CLIENT_ID", settings.GMAIL_CLIENT_ID),
            ("GMAIL_CLIENT_SECRET", settings.GMAIL_CLIENT_SECRET),
            ("GMAIL_REFRESH_TOKEN", settings.GMAIL_REFRESH_TOKEN),
        )
        if not value
    ]
    if missing:
        _LAST_EMAIL_ERROR = f"Gmail API belum dikonfigurasi: {', '.join(missing)}"
        logger.warning(
            "[%s] %s. Email to %s not sent.", _timestamp(), _LAST_EMAIL_ERROR, to_email
        )
        return False

    token_data = urllib.parse.urlencode({
        "refresh_token": settings.GMAIL_REFRESH_TOKEN,
        "client_id": settings.GMAIL_CLIENT_ID,
        "client_secret": settings.GMAIL_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    token_request = urllib.request.Request(
        GMAIL_TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(token_request, timeout=SMTP_TIMEOUT) as resp:
            token_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        _LAST_EMAIL_ERROR = (
            f"Gmail token HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        )
        logger.error(
            "[%s] Gmail token refresh failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False
    except Exception as e:
        _LAST_EMAIL_ERROR = f"{type(e).__name__}: {e}"
        logger.error(
            "[%s] Gmail token request failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False

    access_token = token_info.get("access_token")
    if not access_token:
        _LAST_EMAIL_ERROR = f"Gmail token refresh returned no access_token: {token_info}"
        logger.error(
            "[%s] Gmail token refresh failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False

    raw = base64.urlsafe_b64encode(
        _build_message(to_email, subject, body_html, body_text).encode("utf-8")
    ).decode("ascii")
    send_request = urllib.request.Request(
        GMAIL_SEND_URL,
        data=json.dumps({"raw": raw}).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(send_request, timeout=SMTP_TIMEOUT) as resp:
            resp.read()
        _LAST_EMAIL_ERROR = None
        logger.info("Email sent via Gmail API to %s", to_email)
        return True
    except urllib.error.HTTPError as e:
        _LAST_EMAIL_ERROR = (
            f"Gmail send HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        )
        logger.error(
            "[%s] Gmail send failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False
    except Exception as e:
        _LAST_EMAIL_ERROR = f"{type(e).__name__}: {e}"
        logger.error(
            "[%s] Gmail send request failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False


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
        logger.info("Email sent via Resend API to %s", to_email)
        return True
    except urllib.error.HTTPError as e:
        _LAST_EMAIL_ERROR = (
            f"Resend HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        )
        logger.error(
            "[%s] Resend failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False
    except Exception as e:
        _LAST_EMAIL_ERROR = f"{type(e).__name__}: {e}"
        logger.error(
            "[%s] Resend request failed for %s: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
        )
        return False


def _send_via_smtp(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    global _LAST_EMAIL_ERROR
    if not settings.SMTP_HOST:
        _LAST_EMAIL_ERROR = "SMTP_HOST is not configured"
        logger.warning(
            "[%s] SMTP not configured. Email to %s not sent.\nSubject: %s\nBody:\n%s",
            _timestamp(), to_email, subject, body_text or body_html,
        )
        return False

    message = _build_message(to_email, subject, body_html, body_text)

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
            logger.info("Email sent via SMTP to %s", to_email)
            return True
        except Exception as e:
            last_error = e
            logger.warning(
                "[%s] SMTP attempt to %s:%s failed for %s: %s",
                _timestamp(), settings.SMTP_HOST, port, to_email, e,
            )

    _LAST_EMAIL_ERROR = f"{type(last_error).__name__}: {last_error}"
    logger.error(
        "[%s] Failed to send email to %s via SMTP: %s", _timestamp(), to_email, _LAST_EMAIL_ERROR
    )
    return False


def send_email(to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
    configured_backends = []
    if settings.GMAIL_REFRESH_TOKEN:
        configured_backends.append("gmail")
    if settings.RESEND_API_KEY:
        configured_backends.append("resend")
    if settings.SMTP_HOST:
        configured_backends.append("smtp")
    logger.debug(
        "send_email called for %s. Configured backend(s): %s",
        to_email, ", ".join(configured_backends) or "none",
    )

    if settings.GMAIL_REFRESH_TOKEN:
        logger.info("Attempting to send email to %s via Gmail API", to_email)
        return _send_via_gmail(to_email, subject, body_html, body_text)
    if settings.RESEND_API_KEY:
        logger.info("Attempting to send email to %s via Resend API", to_email)
        return _send_via_resend(to_email, subject, body_html, body_text)
    logger.info("Attempting to send email to %s via SMTP", to_email)
    return _send_via_smtp(to_email, subject, body_html, body_text)
