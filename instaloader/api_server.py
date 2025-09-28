from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from instaloader import TwoFactorAuthRequiredException, BadCredentialsException
from typing import Optional

from instaloader.api import (
    make_loader,
    get_profile_json,
    get_post_json,
    get_post_media,
    get_stories_for_user,
    get_story_media,
)
import os
from instaloader.instaloader import get_default_session_filename

app = FastAPI()


# A simple in-memory way to keep a logged-in Instaloader for reuse across requests.
# In production you should persist the session securely and consider thread-safety.
def get_shared_loader(app: FastAPI):
    return getattr(app.state, 'loader', None)


def load_saved_session_if_any():
    """Scan ~/.config/instaloader for saved session files and load the first working session.

    This looks for files named `session-<username>` in the default config dir and attempts to
    load them. On success the loader is stored in app.state.loader and its session dict in
    app.state.session.
    """
    session_dir = os.path.expanduser(os.path.join('~', '.config', 'instaloader'))
    if not os.path.isdir(session_dir):
        return
    for fn in os.listdir(session_dir):
        if not fn.startswith('session-'):
            continue
        username = fn[len('session-'):]
        sessionfile = os.path.join(session_dir, fn)
        try:
            L = make_loader()
            # load_session_from_file raises FileNotFoundError if missing, or other errors
            L.load_session_from_file(username, sessionfile)
            # verify
            if L.context.is_logged_in:
                app.state.loader = L
                try:
                    app.state.session = L.save_session()
                except Exception:
                    app.state.session = None
                print(f'Loaded saved session for {username} from {sessionfile}')
                return
            L.close()
        except Exception:
            try:
                L.close()
            except Exception:
                pass
            continue


# Attempt to load a saved session at import time so the server can use it immediately.
load_saved_session_if_any()


class LoginBody(BaseModel):
    username: str
    password: str


@app.post('/login')
def login(body: LoginBody):
    """Log in and keep the logged-in Instaloader in memory for subsequent requests.

    Warning: This stores the session in memory in app.state.loader. For a production
    deployment persist session data to a secure store and reuse it across processes.
    """
    # Create loader and try to log in
    L = make_loader()
    try:
        L.login(body.username, body.password)
    except TwoFactorAuthRequiredException:
        # Keep L alive with pending two-factor auth state and inform client
        app.state.pending_2fa = L
        return {"status": "2fa_required", "detail": "Two-factor authentication required. Call /login/2fa with the code."}
    except Exception as e:
        L.close()
        raise HTTPException(status_code=403, detail=str(e))
    # store loader for reuse
    app.state.loader = L
    # store session dict (optional)
    try:
        app.state.session = L.save_session()
    except Exception:
        app.state.session = None
    return {"status": "logged_in", "username": body.username}



class TwoFactorBody(BaseModel):
    code: str


@app.post('/login/2fa')
def login_2fa(body: TwoFactorBody):
    L = app.state.pending_2fa if hasattr(app.state, 'pending_2fa') else None
    if not L:
        raise HTTPException(status_code=400, detail='no pending two-factor authentication')
    try:
        L.two_factor_login(body.code)
    except BadCredentialsException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        # Keep pending state for retry or clear depending on error
        raise HTTPException(status_code=500, detail=str(e))
    # success: move pending loader to active loader
    app.state.loader = L
    try:
        app.state.session = L.save_session()
    except Exception:
        app.state.session = None
    app.state.pending_2fa = None
    return {"status": "logged_in", "username": L.context.username}


@app.post('/logout')
def logout():
    L = get_shared_loader(app)
    if not L:
        # still clear pending 2fa if any
        pending = getattr(app.state, 'pending_2fa', None)
        if pending:
            try:
                pending.close()
            finally:
                app.state.pending_2fa = None
        raise HTTPException(status_code=400, detail='not logged in')
    try:
        L.close()
    finally:
        app.state.loader = None
        app.state.session = None
        # also clear pending 2fa if any
        app.state.pending_2fa = None
    return {"status": "logged_out"}


@app.get('/login/status')
def login_status():
    L = get_shared_loader(app)
    if not L or not getattr(L.context, 'is_logged_in', False):
        return {"logged_in": False}
    return {"logged_in": True, "username": L.context.username}


@app.get('/profile/{username}')
def profile(username: str):
    L = make_loader()
    try:
        data = get_profile_json(L, username)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        L.close()



@app.get('/stories/{username}')
def stories(username: str):
    """Return list of current story items for given username.

    Requires the loader to be logged in to view that user's stories (private stories require follow).
    """
    shared = get_shared_loader(app)
    if not shared or not getattr(shared.context, 'is_logged_in', False):
        raise HTTPException(status_code=401, detail='server not logged in; call /login or import a session')
    try:
        items = get_stories_for_user(shared, username)
        # remove callables before returning JSON serializable structure
        for it in items:
            it.pop('get_bytes', None)
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/stories/{username}/media/{index}')
def story_media(username: str, index: int = 1):
    """Stream the bytes for the story item at 1-based `index` for `username`."""
    shared = get_shared_loader(app)
    if not shared or not getattr(shared.context, 'is_logged_in', False):
        raise HTTPException(status_code=401, detail='server not logged in; call /login or import a session')
    try:
        content, mime = get_story_media(shared, username, index)
        return Response(content, media_type=mime)
    except IndexError:
        raise HTTPException(status_code=404, detail='story index out of range')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/post/{shortcode}')
def post(shortcode: str):
    L = make_loader()
    try:
        data = get_post_json(L, shortcode)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        L.close()


@app.get('/post/{shortcode}/media/{index}')
def post_media(shortcode: str, index: int = 1):
    """Stream a particular media of a post. `index` is 1-based."""
    L = make_loader()
    try:
        items = get_post_media(L, shortcode)
        if index < 1 or index > len(items):
            raise HTTPException(status_code=404, detail='media index out of range')
        item = items[index - 1]
        content, mime = item['get_bytes']()
        return Response(content, media_type=mime)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        L.close()
