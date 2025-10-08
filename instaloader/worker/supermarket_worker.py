"""Worker to process stories and extract supermarket items using an LLM.

This worker is intended to be run once on server startup (to seed DB) and
optionally periodically. It relies on the `InstagramService` factory and the
LLM processor shim.
"""
import asyncio
import os
import signal
from typing import List

from instaloader.services.instagram_service import get_global_service

# Interval (seconds) between runs when running in loop mode
INTERVAL_SECONDS = int(os.getenv('WORKER_INTERVAL_SECONDS', '3600'))


async def process_stories_once(db, usernames: List[str]):
    """Fetch stories for each username, extract items, and persist to DB."""
    svc = get_global_service()
    # lazy imports to avoid heavy deps at import time
    from instaloader.llm.processor import extract_items_from_image
    from instaloader.db import crud as _crud

    for username in usernames:
        try:
            stories = await svc.get_stories_for_user(username)
        except Exception as e:
            print(f'Failed to get stories for {username}: {e}')
            continue
        # stories is a list of items with 'get_bytes' removed in the API; here we
        # need bytes so we call the per-item getter
        for i, st in enumerate(stories, start=1):
            getter = st.get('get_bytes')
            if not getter:
                print(f'Story {username}#{i} has no get_bytes method, skip')
                # skip if not available
                continue
            try:
                # fetch bytes via service (the service provides helper for posts,
                # but not for story bytes; call getter in threadpool via service)
                # The service exposes get_story_media that returns bytes for index
                img_bytes, mime = await svc.get_story_media(username, i)
                items = await extract_items_from_image(img_bytes, 'story', f'{username}:{i}')
                for it in items:
                    # normalize fields and insert
                    await _crud.insert_supermarket_item(db, it)
            except Exception as e:
                print(f'Failed processing story {username}#{i}: {e}')


async def run_once(db):
    targets = os.getenv('SUPERMARKET_TARGETS', '')
    if not targets:
        return
    usernames = [t.strip() for t in targets.split(',') if t.strip()]
    await process_stories_once(db, usernames)


async def main_loop():
    """Run the supermarket worker periodically using the project's AsyncSessionLocal.

    This imports DB dependencies lazily so the module can be imported without
    requiring asyncpg at import time.
    """
    from instaloader.db.database import AsyncSessionLocal

    while True:
        async with AsyncSessionLocal() as db:
            await run_once(db)
        await asyncio.sleep(INTERVAL_SECONDS)


def _install_signal_handlers(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, loop.stop)
        except NotImplementedError:
            # add_signal_handler may not be implemented on some platforms
            pass


if __name__ == '__main__':
    # CLI for debugging and looped runs
    import argparse
    import asyncio

    p = argparse.ArgumentParser(description='Supermarket worker: process stories and extract items')
    p.add_argument('--loop', action='store_true', help='Run continuously at interval (SUPERMARKET_INTERVAL_SECONDS)')
    p.add_argument('--interval', type=int, help='Interval in seconds between runs when using --loop')
    args = p.parse_args()

    if args.interval:
        # override env-based interval for this run
        INTERVAL_SECONDS = args.interval  # type: ignore

    if args.loop:
        loop = asyncio.get_event_loop()
        _install_signal_handlers(loop)
        try:
            loop.run_until_complete(main_loop())
        finally:
            try:
                from instaloader.db.database import engine
                loop.run_until_complete(engine.dispose())
            except Exception:
                pass
    else:
        from instaloader.db.database import AsyncSessionLocal

        async def main_once():
            async with AsyncSessionLocal() as db:
                await run_once(db)

        asyncio.run(main_once())
