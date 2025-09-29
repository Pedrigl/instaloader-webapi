"""Background worker to fetch Instagram data and persist to DB.

Usage:
  - Configure DATABASE_URL and WORKER_TARGETS (comma-separated usernames or post shortcodes prefixed) in env.
  - Run: python -m instaloader.worker.worker

This worker is intentionally simple. It fetches profiles and posts using the
`service` on-demand and stores the returned JSON into the database tables.
"""
import asyncio
import os
import signal
from typing import List

from instaloader.services.instagram_service import get_global_service

# Worker configuration via env
INTERVAL_SECONDS = 3600
WORKER_TARGETS = os.getenv('WORKER_TARGETS', '')  # comma separated: username,post:Bxxxxx


async def handle_profile(db, username: str):
    try:
        svc = get_global_service()
        data = await svc.get_profile(username)
        # import crud lazily to avoid requiring DB dependencies at import time
        from instaloader.db import crud as _crud
        await _crud.insert_fetched_profile(db, username, data)
        print(f'Persisted profile {username}')
    except Exception as e:
        print(f'Failed to fetch/persist profile {username}: {e}')


async def handle_post(db, shortcode: str):
    try:
        svc = get_global_service()
        data = await svc.get_post(shortcode)
        from instaloader.db import crud as _crud
        await _crud.insert_fetched_post(db, shortcode, data)
        print(f'Persisted post {shortcode}')
    except Exception as e:
        print(f'Failed to fetch/persist post {shortcode}: {e}')


async def run_once(db):
    if not WORKER_TARGETS:
        return
    targets = [t.strip() for t in WORKER_TARGETS.split(',') if t.strip()]
    for t in targets:
        if t.startswith('post:'):
            shortcode = t.split(':', 1)[1]
            await handle_post(db, shortcode)
        else:
            username = t
            await handle_profile(db, username)


async def main_loop():
    # import DB session factory lazily so the module can be imported without
    # asyncpg installed. This function will raise if DB not configured.
    from instaloader.db.database import AsyncSessionLocal, engine

    # create async session per run
    while True:
        async with AsyncSessionLocal() as db:
            await run_once(db)
        await asyncio.sleep(INTERVAL_SECONDS)


def _install_signal_handlers(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)


def main():
    loop = asyncio.get_event_loop()
    _install_signal_handlers(loop)
    try:
        loop.run_until_complete(main_loop())
    finally:
        # dispose engine if available
        try:
            from instaloader.db.database import engine
            loop.run_until_complete(engine.dispose())
        except Exception:
            pass


if __name__ == '__main__':
    main()
