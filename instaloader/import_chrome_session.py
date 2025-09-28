import os
import browser_cookie3
from instaloader import Instaloader

def import_chrome_session():
    # Pega cookies do Chrome para Instagram
    cj = browser_cookie3.chrome(domain_name='instagram.com')

    L = Instaloader(max_connection_attempts=1)
    L.context._session.cookies.update(cj)

    username = L.test_login()
    if not username:
        raise SystemExit("❌ Not logged in. Please log in to Instagram in Chrome first.")

    print(f"✅ Imported session cookie for {username}")

    # Caminho padrão do instaloader (~/.config/instaloader/session-<username>)
    session_dir = os.path.expanduser("~/.config/instaloader")
    os.makedirs(session_dir, exist_ok=True)

    sessionfile = os.path.join(session_dir, f"session-{username}")
    L.context.username = username
    L.save_session_to_file(sessionfile)

    print(f"💾 Session saved to {sessionfile}")

if __name__ == "__main__":
    import_chrome_session()
