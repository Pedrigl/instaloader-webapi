"""DB-backed API: serves supermarket items persisted by the worker.

This app is intentionally separate from the development/testing API (`api_server.py`)
so you can run the DB-only server in production while keeping the dev controller around.
"""
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    """Lazy DB dependency: imports the real get_db at runtime so module import
    doesn't fail when DB driver isn't installed.
    """
    try:
        from instaloader.db.database import get_db as _real_get_db
    except Exception as e:
        # Raise an HTTP error at request time if DB is not configured/available
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=f'Database not available: {e}')

    async for session in _real_get_db():
        yield session

app = FastAPI(title='instaloader-db')


class SupermarketItemOut(BaseModel):
    id: int
    name: str
    price: Optional[float] = None
    unit: Optional[str] = None
    store: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    raw_data: Optional[dict] = None

    class Config:
        orm_mode = True


@app.get('/items', response_model=List[SupermarketItemOut])
async def list_items(limit: int = 100, name: Optional[str] = None, store: Optional[str] = None, db: AsyncSession = Depends(get_db_dep)):
    from instaloader.db import crud as _crud
    items = await _crud.list_supermarket_items(db, limit=limit, name=name, store=store)
    return items


@app.get('/items/{item_id}', response_model=SupermarketItemOut)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db_dep)):
    from instaloader.db import crud as _crud
    item = await _crud.get_supermarket_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='item not found')
    return item


@app.post('/admin/trigger-run')
async def trigger_run(db: AsyncSession = Depends(get_db_dep)):
    """Trigger the supermarket worker run once using the DB session."""
    # call worker run_once with the provided DB session
    from instaloader.worker import supermarket_worker as _smw
    await _smw.run_once(db)
    return {'status': 'ok'}