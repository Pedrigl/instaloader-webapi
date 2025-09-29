import os
import argparse
import browser_cookie3
from instaloader import Instaloader


def import_chrome_session(output_dir: str | None = None):
    """Import Instagram cookies from Chrome and save an Instaloader session.

    By default this writes session files into a local `./sessions` directory so
    they can be mounted into the container or checked into your project (if you
    choose).
    """
    # Pega cookies do Chrome para Instagram
    cj = browser_cookie3.chrome(domain_name='instagram.com')

    L = Instaloader(max_connection_attempts=1)
    L.context._session.cookies.update(cj)

    username = L.test_login()
    if not username:
        raise SystemExit("❌ Not logged in. Please log in to Instagram in Chrome first.")

    print(f"✅ Imported session cookie for {username}")

    # Default to a project-local sessions folder unless overridden
    if output_dir is None:
        output_dir = os.environ.get('SESSION_OUTPUT_DIR') or os.path.join(os.getcwd(), 'sessions')

    session_dir = os.path.abspath(os.path.expanduser(output_dir))
    os.makedirs(session_dir, exist_ok=True)

    sessionfile = os.path.join(session_dir, f"session-{username}")
    L.context.username = username
    try:
        L.save_session_to_file(sessionfile)
        print(f"💾 Session saved to {sessionfile}")
    except PermissionError:
        legacy_dir = os.path.expanduser(os.path.join('~', '.config', 'instaloader'))
        os.makedirs(legacy_dir, exist_ok=True)
        legacy_file = os.path.join(legacy_dir, f"session-{username}")
        L.save_session_to_file(legacy_file)
        print(f"⚠️  Could not write to {session_dir} (permission denied).")
        print(f"💾 Saved session to fallback location: {legacy_file}")
        print(\
            "To use project-local sessions (./sessions), change ownership or permissions:\n"
            f"  sudo chown $(id -u):$(id -g) {session_dir} || sudo chmod u+rw {session_dir}\n"
            "Then rerun this script and copy the session files into ./sessions for the container."
        )


def _cli():
    p = argparse.ArgumentParser(description='Import Instagram session cookies from Chrome')
    p.add_argument('-o', '--out', help='Output directory for session files (default: ./sessions)')
    args = p.parse_args()
    import_chrome_session(args.out)


if __name__ == "__main__":
    _cli()
