from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, func
from .database import Base


class SupermarketItem(Base):
    __tablename__ = 'supermarket_items'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(512), nullable=False)
    price = Column(Float, nullable=True)
    unit = Column(String(64), nullable=True)
    store = Column(String(255), nullable=True)
    source_type = Column(String(32), nullable=True)  # 'story' or 'post'
    source_id = Column(String(255), nullable=True)
    raw_data = Column(JSON, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Product(Base):
    __tablename__ = 'products'

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    image_url = Column(String(2048), nullable=True)
    description = Column(String, nullable=True)
    market_prices = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
