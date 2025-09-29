"""Utility to create DB tables for the async SQLAlchemy models.

Run with: python -m instaloader.db.init_db
"""
import asyncio
from .database import engine, Base


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main():
    asyncio.run(init_models())


if __name__ == '__main__':
    main()
