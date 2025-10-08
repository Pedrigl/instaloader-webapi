"""Utility to create DB tables for the async SQLAlchemy models.

Run with: python -m instaloader.db.init_db
"""
import asyncio
import sys
import time
import importlib
from sqlalchemy.exc import OperationalError

# Import the package so model modules are loaded and register with Base
import instaloader.db  # noqa: F401

from .database import get_engine, Base

MAX_RETRIES = 10
SLEEP_SECONDS = 3


async def init_models():
    attempt = 0
    while True:
        try:
            eng = get_engine()
            async with eng.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("DB tables created/verified")
            return
        except OperationalError as e:
            attempt += 1
            print(f"DB not ready (attempt {attempt}/{MAX_RETRIES}): {e}", file=sys.stderr)
            if attempt >= MAX_RETRIES:
                print("Exceeded retries, aborting", file=sys.stderr)
                raise
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            print("Unexpected error while initializing DB:", e, file=sys.stderr)
            raise


def main():
    asyncio.run(init_models())


if __name__ == '__main__':
    main()
