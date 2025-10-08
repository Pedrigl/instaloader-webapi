import os
import argparse
import subprocess
import browser_cookie3
from instaloader import Instaloader


def _attempt_fix_permissions(path: str) -> bool:
    """Try to create the directory and fix ownership so the current user can write.

    Returns True if the directory is writable after the attempt, False otherwise.
    This function will call sudo chown if necessary and available (it will prompt
    for a password)."""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        # creation failed — we'll still try chown below which may also fail
        pass

    # If writable already, we're done
    if os.access(path, os.W_OK):
        return True

    uid = os.getuid()
    gid = os.getgid()
    owner = f"{uid}:{gid}"
    print(f"Attempting to change ownership of {path} to {owner} (sudo may ask for your password)...")
    try:
        subprocess.run(["sudo", "chown", owner, path], check=False)
        # ensure user write bit is set
        subprocess.run(["sudo", "chmod", "u+rw", path], check=False)
    except Exception as e:
        print(f"Failed to run sudo to fix permissions: {e}")
        return False

    return os.access(path, os.W_OK)


def import_chrome_session(output_dir: str | None = None, fix_permissions: bool = True):
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
    try:
        os.makedirs(session_dir, exist_ok=True)
    except Exception:
        # Will handle below via permission fix attempt
        pass

    # If asked, attempt to fix permissions so the current user can write here
    if fix_permissions and not os.access(session_dir, os.W_OK):
        ok = _attempt_fix_permissions(session_dir)
        if not ok:
            print(f"Could not make {session_dir} writable even after attempting fixes.")

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
    p.add_argument('--fix-permissions', action='store_true', help='Attempt to create/fix permissions on the output directory using sudo')
    args = p.parse_args()
    import_chrome_session(args.out, fix_permissions=args.fix_permissions)


if __name__ == "__main__":
    _cli()
