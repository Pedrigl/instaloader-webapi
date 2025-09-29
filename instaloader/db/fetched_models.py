from sqlalchemy import Column, Integer, String, DateTime, JSON, func, Text
from .database import Base


class FetchedProfile(Base):
    __tablename__ = 'fetched_profiles'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)
    data = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FetchedPost(Base):
    __tablename__ = 'fetched_posts'

    id = Column(Integer, primary_key=True, index=True)
    shortcode = Column(String(64), index=True, nullable=False)
    data = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
