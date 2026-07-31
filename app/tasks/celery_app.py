import asyncio
import time

from celery import Celery
from celery.schedules import crontab

from app.client.deribit import DeribitClient
from app.config import settings
from app.database import SyncSessionLocal
from app.models import TickerPrice


celery_app = Celery("deribit_tasks", broker=settings.celery_broker_url)

celery_app.conf.update(
    result_backend="db+" + settings.database_url_sync,
    beat_schedule={
        "fetch-prices-every-minute": {
            "task": "app.tasks.celery_app.fetch_crypto_prices",
            "schedule": crontab(minute="*"),
        },
    },
    timezone="UTC"
)


async def _async_fetch():
    """Изолированный асинхронный сбор данных"""
    tickers = ["btc_usd", "eth_usd"]
    results = []

    async with DeribitClient(base_url=settings.DERIBIT_BASE_URL) as client:
        for ticker in tickers:
            try:
                price = await client.get_index_price(ticker)
                results.append({
                    "ticker": ticker,
                    "price": price,
                    "timestamp": int(time.time())
                })
            except Exception as e:
                print(f"[Celery Async] Ошибка сбора {ticker}: {e}")
    return results


@celery_app.task
def fetch_crypto_prices():
    """
    Синхронный маршал Celery: запускает изолированный цикл
    и пишет в БД через psycopg2
    """
    try:
        fetched_data = asyncio.run(_async_fetch())
    except Exception as e:
        print(f"[Celery] Ошибка выполнения асинхронного цикла: {e}")
        return

    if fetched_data:
        with SyncSessionLocal() as db_session:
            try:
                prices_to_save = []
                for item in fetched_data:
                    db_price = TickerPrice(
                        ticker=item["ticker"],
                        price=round(item["price"], 2),
                        timestamp=item["timestamp"]
                    )
                    prices_to_save.append(db_price)
                    print(
                        f"[Celery Success] Получено: "
                        f"{item['ticker']} = {item['price']}"
                        )

                db_session.add_all(prices_to_save)
                db_session.commit()
                print(
                    f"[Celery] Пачка из {len(prices_to_save)} "
                    f"цен успешно зафиксирована в PostgreSQL."
                )
            except Exception as e:
                db_session.rollback()
                print(f"[Celery] Ошибка записи пачки в БД: {e}")
