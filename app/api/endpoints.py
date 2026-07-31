from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TickerPrice
from app.schemas import PriceResponseSchema


router = APIRouter(prefix="/api/v1/prices", tags=["Prices"])


@router.get("/all", response_model=List[PriceResponseSchema])
async def get_all_prices(
    ticker: str = Query(..., description="Тикер валюты, например btc_usd"),
    db: AsyncSession = Depends(get_db)
):
    """1. Получение всех сохраненных данных по указанной валюте"""
    query = (
        select(TickerPrice)
        .where(TickerPrice.ticker == ticker)
        .order_by(desc(TickerPrice.timestamp))
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/latest", response_model=PriceResponseSchema)
async def get_latest_price(
    ticker: str = Query(..., description="Тикер валюты, например btc_usd"),
    db: AsyncSession = Depends(get_db)
):
    """2. Получение последней цены валюты"""
    query = (
        select(TickerPrice)
        .where(TickerPrice.ticker == ticker)
        .order_by(desc(TickerPrice.timestamp)).limit(1)
    )
    result = await db.execute(query)
    latest_price = result.scalar_one_or_none()

    if not latest_price:
        raise HTTPException(
            status_code=404, detail=f"Данные для тикера '{ticker}' не найдены"
        )
    return latest_price


@router.get("/filter", response_model=List[PriceResponseSchema])
async def get_prices_by_date(
    ticker: str = Query(
        ...,
        description="Тикер валюты, например btc_usd"
    ),
    start_timestamp: int = Query(
        ...,
        description="Начальное время в UNIX timestamp"
    ),
    end_timestamp: int = Query(
        ...,
        description="Конечное время в UNIX timestamp"
    ),
    db: AsyncSession = Depends(get_db)
):
    """3. Получение цены валюты с фильтром по дате (временному диапазону)"""
    query = (
        select(TickerPrice)
        .where(TickerPrice.ticker == ticker)
        .where(TickerPrice.timestamp >= start_timestamp)
        .where(TickerPrice.timestamp <= end_timestamp)
        .order_by(desc(TickerPrice.timestamp))
    )
    result = await db.execute(query)
    return result.scalars().all()
