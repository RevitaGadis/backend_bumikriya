import sys

from app.core.config import settings
from app.services.email_service import send_email, get_last_email_error


def main() -> None:
    if not settings.RESEND_API_KEY:
        print("RESEND_API_KEY belum diatur di file env.")
        print("1. Daftar di https://resend.com dan buat API key (re_...).")
        print("2. Masukkan ke env: RESEND_API_KEY=re_...")
        return

    to = input("Email tujuan tes: ").strip() or "m.azkanabhan07@gmail.com"
    ok = send_email(
        to_email=to,
        subject="Tes Email Bumikriya",
        body_html="<p>Halo, ini email <strong>tes</strong> dari Bumikriya.</p>",
        body_text="Halo, ini email tes dari Bumikriya.",
    )
    if ok:
        print("Email terkirim.")
    else:
        print(f"GAGAL: {get_last_email_error()}")
        raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())
