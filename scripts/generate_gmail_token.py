import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

SCOPE = "https://www.googleapis.com/auth/gmail.send"
REDIRECT_PORT = 8969
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def main() -> int:
    if not (settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET):
        print("Set GMAIL_CLIENT_ID & GMAIL_CLIENT_SECRET dulu di file env.")
        print()
        print("Langkah (console.cloud.google.com):")
        print("  1. Pilih project -> buka 'APIs & Services' -> 'OAuth consent screen' (External)")
        print("  2. Tambah scope: https://www.googleapis.com/auth/gmail.send")
        print("  3. 'Credentials' -> Create Credentials -> OAuth client ID -> Desktop app")
        print(f"  4. Tambahkan redirect URI: {REDIRECT_URI}")
        print("  5. Salin Client ID & Client Secret ke env: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET")
        return 1

    auth_params = {
        "client_id": settings.GMAIL_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    print("1. Buka URL ini di browser (login pakai bumikriya2@gmail.com):")
    print(AUTH_URL + "?" + urllib.parse.urlencode(auth_params))
    print()

    code_holder = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if "code" in qs:
                code_holder["code"] = qs["code"][0]
                self.wfile.write(b"<h2>Berhasil! Silakan tutup tab ini.</h2>")
            else:
                self.wfile.write(
                    f"<h2>Error: {qs.get('error', ['Tidak ada kode'])[0]}</h2>".encode("utf-8")
                )

        def log_message(self, *args):
            pass

    print("2. Server lokal aktif di " + REDIRECT_URI + " menunggu redirect dari Google...")
    server = HTTPServer(("localhost", REDIRECT_PORT), Handler)
    while "code" not in code_holder:
        server.handle_request()
    server.server_close()

    exchange_data = urllib.parse.urlencode({
        "code": code_holder["code"],
        "client_id": settings.GMAIL_CLIENT_ID,
        "client_secret": settings.GMAIL_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    token_request = urllib.request.Request(
        TOKEN_URL,
        data=exchange_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(token_request, timeout=30) as resp:
            token_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("Token exchange GAGAL:", e.read().decode("utf-8", "replace"))
        return 1
    except Exception as e:
        print("Token exchange GAGAL:", type(e).__name__, e)
        return 1

    refresh_token = token_info.get("refresh_token")
    print()
    print("3. Simpan nilai berikut ke file env / Railway Variables:")
    if refresh_token:
        print("GMAIL_REFRESH_TOKEN=" + refresh_token)
    else:
        print("Tidak ada refresh_token dikembalikan.")
        print("Jika akun sudah pernah consent, revoke akses di https://myaccount.google.com/connections lalu ulangi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
