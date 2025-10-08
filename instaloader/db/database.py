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
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base

# Prefer reading DB URL from env; fallback to None
DATABASE_URL = os.getenv('DATABASE_URL', None)

# Lazy-initialized engine and sessionmaker
_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[sessionmaker] = None

# Expose names for backward-compatibility; they will be set when get_engine()
# is first called. Call get_engine() before using these at runtime.
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[sessionmaker] = None

# Declarative base for models
Base = declarative_base()


def get_engine() -> AsyncEngine:
    """Create and return the AsyncEngine. Raises if DATABASE_URL is not set.

    This function also initializes the module-level `engine` and
    `AsyncSessionLocal` variables for backward compatibility with code that
    imports them from this module.
    """
    global _engine, _AsyncSessionLocal, engine, AsyncSessionLocal
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError('DATABASE_URL is not set; cannot create DB engine')
        _engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        _AsyncSessionLocal = sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
        engine = _engine
        AsyncSessionLocal = _AsyncSessionLocal
    return _engine  # type: ignore


def get_sessionmaker() -> sessionmaker:
    """Return the configured sessionmaker (initializes engine if needed)."""
    if _AsyncSessionLocal is None:
        get_engine()
    return _AsyncSessionLocal  # type: ignore


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession per request.

    Example usage in FastAPI endpoint:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            await db.execute(...)
    """
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
