"""Worker to process stories and extract supermarket items using an LLM.

This worker is intended to be run once on server startup (to seed DB) and
optionally periodically. It relies on the `InstagramService` factory and the
LLM processor shim.
"""
import asyncio
import os
from typing import List

from instaloader.services.instagram_service import get_global_service


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
                    print(f'Inserted item {it.get("name")} from {username} story {i}')
            except Exception as e:
                print(f'Failed processing story {username}#{i}: {e}')


async def run_once(db):
    targets = os.getenv('SUPERMARKET_TARGETS', '')
    if not targets:
        return
    usernames = [t.strip() for t in targets.split(',') if t.strip()]
    await process_stories_once(db, usernames)


if __name__ == '__main__':
    # quick CLI for debugging
    import asyncio
    from instaloader.db.database import AsyncSessionLocal

    async def main():
        async with AsyncSessionLocal() as db:
            await run_once(db)

    asyncio.run(main())
