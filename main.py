# main.py
import uvicorn
from fastapi import FastAPI

from app.api.endpoints import router as prices_router
from app.database import engine
from app.models import Base

app = FastAPI(
    title="60SecCrypto API",
    description=(
        "API для отслеживания ежеминутных цен"
        "криптовалют с биржи Deribit"
    ),
    version="1.0.0"
)

app.include_router(prices_router)


@app.on_event("startup")
async def startup_event():
    """
    При запуске приложения локально автоматически создаем таблицы в БД,
    если они еще не созданы. (В продакшене для этого используется Alembic).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[FastAPI] База данных успешно инициализирована, таблицы созданы.")


@app.get("/")
def read_root():
    return {
        "status": "working",
        "message": (
            "Добро пожаловать в 60SecCrypto API. "
            "Перейдите на /docs для просмотра документации."
        ),
    }


if __name__ == "__main__":
    uvicorn.run("main.py:app", host="127.0.0.1", port=8000, reload=True)
