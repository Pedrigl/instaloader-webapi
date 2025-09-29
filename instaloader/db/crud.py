from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserSession
from .fetched_models import FetchedProfile, FetchedPost
from sqlalchemy import insert
from .items_models import SupermarketItem
from .items_models import Product as ProductModel
from sqlalchemy import select


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


async def insert_supermarket_item(db: AsyncSession, item: dict):
    """Insert a detected supermarket item.

    Expects `item` to be a dict with keys matching the model: name, price,
    unit, store, source_type, source_id, raw_data.
    """
    obj = SupermarketItem(
        name=item.get('name') or 'unknown',
        price=item.get('price'),
        unit=item.get('unit'),
        store=item.get('store'),
        source_type=item.get('source_type'),
        source_id=item.get('source_id'),
        raw_data=item.get('raw_data'),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_supermarket_item_by_id(db: AsyncSession, item_id: int):
    q = select(SupermarketItem).where(SupermarketItem.id == item_id)
    res = await db.execute(q)
    return res.scalars().first()


async def list_supermarket_items(db: AsyncSession, limit: int = 100, name: str | None = None, store: str | None = None):
    q = select(SupermarketItem)
    if name:
        q = q.where(SupermarketItem.name.ilike(f"%{name}%"))
    if store:
        q = q.where(SupermarketItem.store == store)
    q = q.limit(limit)
    res = await db.execute(q)
    return res.scalars().all()


async def upsert_product(db: AsyncSession, product: dict):
    pid = product.get('id')
    q = select(ProductModel).where(ProductModel.id == pid)
    res = await db.execute(q)
    existing = res.scalars().first()
    if existing:
        stmt = update(ProductModel).where(ProductModel.id == pid).values(
            title=product.get('title'),
            image_url=product.get('imageUrl') or product.get('image_url'),
            description=product.get('description'),
            market_prices=product.get('marketPrices') or []
        )
        await db.execute(stmt)
        await db.commit()
        res = await db.execute(select(ProductModel).where(ProductModel.id == pid))
        return res.scalars().first()
    else:
        obj = ProductModel(
            id=pid,
            title=product.get('title') or 'unknown',
            image_url=product.get('imageUrl') or product.get('image_url'),
            description=product.get('description'),
            market_prices=product.get('marketPrices') or []
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


async def list_products(db: AsyncSession, limit: int = 100, offset: int = 0):
    q = select(ProductModel).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()


async def get_product(db: AsyncSession, product_id: str):
    q = select(ProductModel).where(ProductModel.id == product_id)
    res = await db.execute(q)
    return res.scalars().first()
