import smtplib
from app.core.config import settings


def main() -> None:
    print(f"Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USER}")
    print(f"From: {settings.SMTP_FROM}")
    print(f"TLS: {settings.SMTP_USE_TLS}")

    if not settings.SMTP_HOST:
        print("SMTP_HOST belum diatur di file env. Tidak ada yang bisa dites.")
        return

    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        print("Login SMTP berhasil. Kredensial valid.")
        server.quit()
    except Exception as e:
        print(f"GAGAL: {type(e).__name__}: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
