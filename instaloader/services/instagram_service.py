"""Instagram service encapsulating Instaloader logic for the API.

This module keeps the web endpoints thin by moving the Instaloader calls and
session handling here. Blocking Instaloader calls are executed in a thread
pool so the async event loop is not blocked.
"""
from __future__ import annotations

import os
from typing import Optional, List, Tuple, Any

from starlette.concurrency import run_in_threadpool

from instaloader.api import (
    make_loader,
    get_profile_json,
    get_post_json,
    get_post_media,
    get_stories_for_user,
    get_story_media,
)
from instaloader import TwoFactorAuthRequiredException, BadCredentialsException


class InstagramService:
    """Service that manages an Instaloader instance and exposes async methods.

    The service keeps an optional in-memory shared loader (`self.loader`) which
    is useful for endpoints that require a logged-in session (stories).
    """

    def __init__(self):
        self.loader = None  # type: Optional[Any]
        self.pending_2fa = None
        self.session = None

    async def _make_loader(self):
        # make_loader is a small, quick call but may do I/O in some configs
        return await run_in_threadpool(make_loader)

    async def load_saved_session_if_any(self) -> Optional[str]:
        """Scan ~/.config/instaloader for session-<username> files and load the first working one.

        Returns username if loaded, else None.
        """
        session_dir = os.path.expanduser(os.path.join('~', '.config', 'instaloader'))
        if not os.path.isdir(session_dir):
            return None
        for fn in os.listdir(session_dir):
            if not fn.startswith('session-'):
                continue
            username = fn[len('session-'):]
            sessionfile = os.path.join(session_dir, fn)
            try:
                L = await self._make_loader()
                # load_session_from_file is blocking; run in thread
                await run_in_threadpool(L.load_session_from_file, username, sessionfile)
                if L.context.is_logged_in:
                    self.loader = L
                    try:
                        self.session = await run_in_threadpool(L.save_session)
                    except Exception:
                        self.session = None
                    return username
                await run_in_threadpool(L.close)
            except Exception:
                try:
                    await run_in_threadpool(L.close)
                except Exception:
                    pass
                continue
        return None

    # DB persistence is intentionally not handled here. A background worker
    # should be responsible for persisting sessions into a database.

    async def login(self, username: str, password: str):
        """Attempt to login and persist loader in service state on success.

        May raise TwoFactorAuthRequiredException or other exceptions.
        """
        L = await self._make_loader()
        try:
            # synchronous login -> run in threadpool
            await run_in_threadpool(L.login, username, password)
        except TwoFactorAuthRequiredException:
            # keep pending state to complete 2fa
            self.pending_2fa = L
            raise
        except Exception:
            # ensure loader closed on failure
            try:
                await run_in_threadpool(L.close)
            except Exception:
                pass
            raise

        # success -> store loader
        self.loader = L
        try:
            self.session = await run_in_threadpool(L.save_session)
        except Exception:
            self.session = None

        return self.session

    async def two_factor(self, code: str):
        L = self.pending_2fa
        if not L:
            raise RuntimeError('no pending 2fa')
        try:
            await run_in_threadpool(L.two_factor_login, code)
        except BadCredentialsException:
            raise
        # success
        self.loader = L
        try:
            self.session = await run_in_threadpool(L.save_session)
        except Exception:
            self.session = None
        self.pending_2fa = None
        return self.session

    def is_logged_in(self) -> bool:
        return bool(self.loader and getattr(self.loader.context, 'is_logged_in', False))

    def get_username(self) -> Optional[str]:
        if not self.loader:
            return None
        return getattr(self.loader.context, 'username', None)

    async def logout(self):
        if not self.loader:
            raise RuntimeError('not logged in')
        try:
            await run_in_threadpool(self.loader.close)
        finally:
            self.loader = None
            self.session = None
            self.pending_2fa = None

    # Read-only helpers
    async def get_profile(self, username: str):
        # use a transient loader (no login needed for public profiles)
        L = await self._make_loader()
        try:
            return await run_in_threadpool(get_profile_json, L, username)
        finally:
            await run_in_threadpool(L.close)

    async def get_post(self, shortcode: str):
        L = await self._make_loader()
        try:
            return await run_in_threadpool(get_post_json, L, shortcode)
        finally:
            await run_in_threadpool(L.close)

    async def get_post_media(self, shortcode: str) -> List[dict]:
        L = await self._make_loader()
        try:
            return await run_in_threadpool(get_post_media, L, shortcode)
        finally:
            await run_in_threadpool(L.close)

    async def get_post_media_bytes(self, shortcode: str, index: int = 1) -> Tuple[bytes, str]:
        """Return (bytes, mime) for a particular media index (1-based) of a post.

        This helper fetches the media list (in threadpool) and then executes the
        media getter callback in the threadpool as well so callers get bytes
        directly without dealing with callables.
        """
        items = await self.get_post_media(shortcode)
        if index < 1 or index > len(items):
            raise IndexError('media index out of range')
        item = items[index - 1]
        getter = item.get('get_bytes')
        if not getter:
            raise RuntimeError('no getter for media')
        # getter is a sync callable — run in threadpool
        return await run_in_threadpool(getter)

    async def get_stories_for_user(self, username: str):
        # requires logged-in loader
        if not self.loader or not getattr(self.loader.context, 'is_logged_in', False):
            raise RuntimeError('server not logged in')
        return await run_in_threadpool(get_stories_for_user, self.loader, username)

    async def get_story_media(self, username: str, index: int = 1) -> Tuple[bytes, str]:
        if not self.loader or not getattr(self.loader.context, 'is_logged_in', False):
            raise RuntimeError('server not logged in')
        return await run_in_threadpool(get_story_media, self.loader, username, index)


_global_service: Optional[InstagramService] = None


def get_global_service() -> InstagramService:
    """Return a singleton InstagramService for use in simple deployments.

    Use this factory from non-FastAPI code (worker, scripts). For FastAPI
    endpoints prefer the `get_service_dep` dependency which returns this
    singleton as well.
    """
    global _global_service
    if _global_service is None:
        _global_service = InstagramService()
    return _global_service


async def get_service_dep() -> InstagramService:
    """FastAPI dependency to inject the global InstagramService.

    Kept as an async function so it can be used as an `Depends(...)` in
    async endpoints uniformly.
    """
    return get_global_service()
