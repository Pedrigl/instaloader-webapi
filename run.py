#!/usr/bin/env python3
"""Application entrypoint: initializes DB, imports sessions, runs one-off workers, then starts the API.

Usage: python run.py
In Docker the container runs this to bootstrap and then start uvicorn.
"""
import asyncio
import os
import shutil
from pathlib import Path


async def _init_db_if_available():
    try:
        from instaloader.db.init_db import init_models
    except Exception:
        return
    try:
        await init_models()
    except Exception as e:
        print('warning: failed to initialize DB:', e)


async def _import_mounted_sessions():
    """If a host-mounted session directory exists (mounted into /data/session by compose), copy into user's config dir."""
    mount_dir = os.getenv('SESSION_MOUNT_DIR', '/data/session')
    target_dir = Path.home() / '.config' / 'instaloader'
    try:
        p = Path(mount_dir)
        if p.exists() and p.is_dir():
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in p.iterdir():
                if f.is_file():
                    shutil.copy2(str(f), str(target_dir / f.name))
            print(f'Imported session files from {mount_dir} into {target_dir}')
    except Exception as e:
        print('warning: failed to import mounted sessions:', e)


async def _load_saved_session_and_run_worker():
    try:
        from instaloader.services.instagram_service import get_global_service
        svc = get_global_service()
        # attempt to load saved session from config dir
        try:
            username = await svc.load_saved_session_if_any()
            if username:
                print('Loaded saved session for', username)
        except Exception as e:
            print('no saved session loaded:', e)

        # run supermarket worker one-off if DB configured
        try:
            from instaloader.db.database import AsyncSessionLocal
            from instaloader.worker import supermarket_worker as _smw

            async with AsyncSessionLocal() as db:
                await _smw.run_once(db)
                print('supermarket worker run completed (one-off)')
        except Exception as e:
            print('skip supermarket worker (db not ready or error):', e)
    except Exception as e:
        print('warning: worker startup failed:', e)


def main():
    # synchronous bootstrap: run async init tasks, then start uvicorn
    try:
        # copy mounted sessions if any
        asyncio.run(_import_mounted_sessions())
        # init DB
        asyncio.run(_init_db_if_available())
        # load session and run worker
        asyncio.run(_load_saved_session_and_run_worker())
    except Exception as e:
        print('bootstrap warning:', e)

    # start uvicorn
    import uvicorn

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    print(f'Starting uvicorn on {host}:{port} ...')
    uvicorn.run('instaloader.api.api_server:app', host=host, port=port)


if __name__ == '__main__':
    main()
