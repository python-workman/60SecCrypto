from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TickerPrice
from app.schemas import PriceResponseSchema

router = APIRouter(prefix="/api/v1/prices", tags=["Prices"])

SUPPORTED_TICKERS = {"btc_usd", "eth_usd"}


async def validate_ticker(
        ticker: str = Query(..., description="Тикер валюты, например btc_usd")
        ):
    """Валидация тикера: только btc_usd или eth_usd."""
    if ticker not in SUPPORTED_TICKERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Неподдерживаемый тикер: {ticker}. "
                f"Допустимые значения: {', '.join(SUPPORTED_TICKERS)}"
            )
        )
    return ticker


@router.get("/all", response_model=List[PriceResponseSchema])
async def get_all_prices(
    ticker: str = Depends(validate_ticker),
    limit: int = Query(
        100, ge=1, le=1000, description="Количество записей на странице"
    ),
    offset: int = Query(0, ge=0, description="Смещение от начала выборки"),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех сохранённых данных по указанной валюте с пагинацией."""
    query = (
        select(TickerPrice)
        .where(TickerPrice.ticker == ticker)
        .order_by(desc(TickerPrice.timestamp))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/latest", response_model=PriceResponseSchema)
async def get_latest_price(
    ticker: str = Depends(validate_ticker),
    db: AsyncSession = Depends(get_db)
):
    """Получение последней цены валюты."""
    query = (
        select(TickerPrice)
        .where(TickerPrice.ticker == ticker)
        .order_by(desc(TickerPrice.timestamp))
        .limit(1)
    )
    result = await db.execute(query)
    latest_price = result.scalar_one_or_none()

    if not latest_price:
        raise HTTPException(
            status_code=404,
            detail=f"Данные для тикера '{ticker}' не найдены"
        )
    return latest_price


@router.get("/filter", response_model=List[PriceResponseSchema])
async def get_prices_by_date(
    ticker: str = Depends(validate_ticker),
    start_timestamp: Optional[int] = Query(
        None,
        description="Начальная метка времени (Unix timestamp)"
    ),
    end_timestamp: Optional[int] = Query(
        None,
        description="Конечная метка времени (Unix timestamp)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Получение цен валюты с фильтром по временному диапазону."""
    if (
        start_timestamp is not None
        and end_timestamp is not None
        and start_timestamp > end_timestamp
    ):
        raise HTTPException(
            status_code=400,
            detail="start_timestamp должен быть меньше или равен end_timestamp"
        )

    query = select(TickerPrice).where(TickerPrice.ticker == ticker)

    if start_timestamp is not None:
        query = query.where(TickerPrice.timestamp >= start_timestamp)
    if end_timestamp is not None:
        query = query.where(TickerPrice.timestamp <= end_timestamp)

    query = query.order_by(desc(TickerPrice.timestamp))
    result = await db.execute(query)
    return result.scalars().all()
