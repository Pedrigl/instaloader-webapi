from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserSession
from .fetched_models import FetchedProfile, FetchedPost
from sqlalchemy import insert


async def get_session_by_username(db: AsyncSession, username: str):
    q = select(UserSession).where(UserSession.username == username)
    res = await db.execute(q)
    return res.scalars().first()


async def upsert_session(db: AsyncSession, username: str, session_data: dict):
    existing = await get_session_by_username(db, username)
    if existing:
        stmt = update(UserSession).where(UserSession.username == username).values(session_data=session_data)
        await db.execute(stmt)
        await db.commit()
        return await get_session_by_username(db, username)
    else:
        obj = UserSession(username=username, session_data=session_data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


async def insert_fetched_profile(db: AsyncSession, username: str, data: dict):
    obj = FetchedProfile(username=username, data=data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def insert_fetched_post(db: AsyncSession, shortcode: str, data: dict):
    obj = FetchedPost(shortcode=shortcode, data=data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
