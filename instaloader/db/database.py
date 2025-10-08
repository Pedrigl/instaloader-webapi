"""Database context using SQLAlchemy (async) for Postgres.

Usage:
  - Set environment variable DATABASE_URL, e.g.
      export DATABASE_URL=postgresql+asyncpg://user:password@localhost/instaloader
  - Install dependencies: SQLAlchemy>=1.4 and asyncpg
      pip install SQLAlchemy asyncpg

This module exposes:
  - engine: Async engine
  - AsyncSessionLocal: sessionmaker for AsyncSession
  - Base: declarative base for models
  - get_db: async FastAPI dependency that yields a DB session
"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Prefer reading DB URL from env; fallback to a local placeholder
DATABASE_URL = os.getenv(
    'DATABASE_URL',
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# sessionmaker for AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession per request.

    Example usage in FastAPI endpoint:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
