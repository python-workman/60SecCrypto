import asyncio
import time

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from app.client.deribit import DeribitClient
from app.config import settings
from app.database import SyncSessionLocal
from app.models import TickerPrice

logger = get_task_logger(__name__)

celery_app = Celery("deribit_tasks", broker=settings.celery_broker_url)

celery_app.conf.update(
    result_backend="db+" + settings.database_url_sync,
    beat_schedule={
        "fetch-prices-every-minute": {
            "task": "app.tasks.celery_app.fetch_crypto_prices",
            "schedule": crontab(minute="*"),
        },
    },
    timezone="UTC",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


async def _async_fetch():
    """Асинхронный параллельный сбор цен."""
    tickers = ["btc_usd", "eth_usd"]
    async with DeribitClient(base_url=settings.DERIBIT_BASE_URL) as client:
        tasks = [client.get_index_price(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    processed = []
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            logger.error(f"Не удалось получить цену {ticker}: {result}")
        else:
            processed.append({
                "ticker": ticker,
                "price": round(result, 2),
                "timestamp": int(time.time())
            })
    return processed


@celery_app.task
def fetch_crypto_prices():
    """Задача Celery: сбор цен и запись в БД."""
    try:
        fetched_data = asyncio.run(_async_fetch())
    except Exception:
        logger.exception("Ошибка выполнения асинхронного цикла")
        return

    if not fetched_data:
        logger.warning("Нет данных для сохранения")
        return

    for item in fetched_data:
        logger.info(
            f"[Celery Success] Получено: "
            f"{item['ticker']} = {item['price']}"
        )

    try:
        with SyncSessionLocal() as db_session:
            prices_to_save = [
                TickerPrice(
                    ticker=item["ticker"],
                    price=item["price"],
                    timestamp=item["timestamp"]
                )
                for item in fetched_data
            ]
            db_session.add_all(prices_to_save)
            db_session.commit()
            logger.info(f"Сохранено {len(prices_to_save)} цен в БД")

    except Exception:
        logger.exception("Ошибка записи в БД")
