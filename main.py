import asyncio
import logging
import sys

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.api.endpoints import router as prices_router
from app.database import engine
from app.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

app = FastAPI(
    title="60SecCrypto API",
    description=(
        "API для отслеживания ежеминутных "
        "цен криптовалют с биржи Deribit"
        ),
    version="1.0.0"
)

app.include_router(prices_router)


@app.on_event("startup")
async def startup_event():
    """
    Отказоустойчивая инициализация БД с ожиданием запуска контейнера Postgres
    """
    logger.info("Запуск приложения. Проверка готовности базы данных...")
    retries = 5
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "База данных успешно инициализирована, таблицы созданы."
            )
            break
        except OperationalError:
            retries -= 1
            logger.warning(
                f"База данных еще не готова. "
                f"Ожидание... (Осталось попыток: {retries})"
            )
            await asyncio.sleep(3)
    else:
        logger.critical(
            "Не удалось подключиться к базе данных после 5 попыток. Выход."
        )


@app.get("/")
def read_root():
    return {
        "status": "working",
        "message": (
            "Добро пожаловать в 60SecCrypto API. "
            "Перейдите на /docs"
        ),
    }
